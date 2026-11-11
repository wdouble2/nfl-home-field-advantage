"""Helpers for Part 2: college football (CollegeFootballData.com) vs. the NFL.

Uses requests + pandas only. The API key is read from .env (CFBD_API_KEY) and never printed.
"""
import os
import re
import time

import hfa
import pandas as pd
import requests
from dotenv import load_dotenv

API = "https://api.collegefootballdata.com/games"


def snake(name):
    """camelCase -> snake_case, e.g. homeTeam -> home_team."""
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


def pull_games(first=2015, last=2025):
    """Every regular-season college game for each season (one API call per season)."""
    load_dotenv()
    headers = {"Authorization": f"Bearer {os.environ['CFBD_API_KEY']}", "Accept": "application/json"}
    frames = []
    for year in range(first, last + 1):
        r = requests.get(API, params={"year": year, "seasonType": "regular"}, headers=headers, timeout=60)
        r.raise_for_status()
        frames.append(pd.DataFrame(r.json()))
        time.sleep(0.5)   # be polite to a free API
    raw = pd.concat(frames, ignore_index=True)
    raw.columns = [snake(c) for c in raw.columns]
    return raw


def title_game_ids(raw):
    """Game ids of conference title games, including ones the API's `notes` field doesn't label.

    `notes` is mostly empty before 2022, so a title game is also spotted by its date: the only
    game of its conference on that conference's last date of the season, in December. Conferences
    that played their title game at a neutral site (late November or December) are skipped, so a postponed
    regular-season game that happened to be played last (e.g. Cal-Stanford 2018) isn't mistaken
    for a title game.
    """
    labelled = raw[raw.notes.fillna("").str.contains("championship", case=False)].id
    c = raw[raw.conference_game.astype(bool) & raw.completed.astype(bool)].copy()
    c["date"] = pd.to_datetime(c.start_date, utc=True).dt.tz_convert("US/Eastern").dt.date
    month, day = pd.to_datetime(c.date).dt.month, pd.to_datetime(c.date).dt.day
    c["december"] = month == 12
    key = ["season", "home_conference"]
    last_date = c.groupby(key).date.transform("max")
    games_that_day = c.groupby(key + ["date"]).id.transform("size")
    late = c.december | ((month == 11) & (day >= 25))
    neutral_title = c[c.neutral_site.astype(bool) & late].groupby(key).size()   # e.g. Pac-12 title game on Nov 30, 2018
    has_neutral_title = pd.Series(list(zip(c.season, c.home_conference)), index=c.index).isin(neutral_title.index)
    by_date = c[(c.date == last_date) & (games_that_day == 1) & c.december & ~has_neutral_title].id
    return set(labelled) | set(by_date)


def clean(raw):
    """FBS vs. FBS regular-season games at the home team's usual stadium, finished, no ties,
    no conference title games.

    Same columns as nfl.games (game_id, season, week, gameday, home_team, away_team,
    home_score, away_score, home_win, margin, covid_season) plus conference info.
    """
    g = raw[(raw.home_classification == "fbs") & (raw.away_classification == "fbs")].copy()
    g = g[~g.neutral_site.astype(bool) & g.completed.astype(bool)]
    g = g.dropna(subset=["home_points", "away_points"])
    g = g[g.home_points != g.away_points]
    # Conference title games are hosted by the higher seed (the college version of the playoffs).
    g = g[~g.id.isin(title_game_ids(raw))]
    # A "home" game can still be at a borrowed venue (hurricane moves, a second "home" stadium,
    # mislabelled rows). Same rule as Part 1: keep only the home team's most-used stadium that season.
    usual = g.groupby(["season", "home_team"]).venue_id.agg(lambda s: s.mode().iat[0])
    g = g[g.venue_id.values == usual.loc[list(zip(g.season, g.home_team))].values]
    g = g.rename(columns={"id": "game_id", "home_points": "home_score", "away_points": "away_score"})
    g["gameday"] = g.start_date.str[:10]
    g["home_score"] = g.home_score.astype(int)
    g["away_score"] = g.away_score.astype(int)
    g["margin"] = g.home_score - g.away_score
    g["home_win"] = (g.margin > 0).astype(int)
    g["covid_season"] = (g.season == 2020).astype(int)
    g["conference_game"] = g.conference_game.astype(bool).astype(int)
    cols = ["game_id", "season", "week", "gameday", "home_team", "away_team", "home_conference",
            "away_conference", "home_score", "away_score", "home_win", "margin", "covid_season",
            "conference_game", "attendance"]
    return g[cols].sort_values(["season", "week", "game_id"]).reset_index(drop=True)


def add_strength_adjusted_edge(df):
    """Adds `adj_edge`: home margin minus the gap in team strength (Part 1's rating model, fit per season).

    Its average is the home edge in points between two equally good teams. Ratings are fit on every
    game in `df`, so college conference games borrow strength information from non-conference games.
    """
    out = df.copy()
    out["adj_edge"] = hfa.adjusted_edge(out)
    out["strength_gap"] = out.margin - out.adj_edge
    return out


def season_home_edges(df, split=None, labels=None):
    """Home edge in points per season from Part 1's rating model, with proper standard errors.

    Fits, separately each season:  margin = home_edge[group] + rating[home] - rating[away].
    `split` (e.g. "conference_game") gives each group its own home edge while every game informs
    the team ratings. Returns one row per season and group: home_edge, se, sigma (how much results vary
    around the model), games.
    """
    import math
    import numpy as np
    rows = []
    for season, d in df.groupby("season"):
        grp = d[split].map(labels).to_numpy() if split else np.array(["all"] * len(d))
        names = sorted(set(grp))
        teams = sorted(set(d.home_team) | set(d.away_team))
        idx = {t: i for i, t in enumerate(teams)}
        X = np.zeros((len(d), len(names) + len(teams) - 1))
        for j, n in enumerate(names):
            X[:, j] = grp == n
        for r, (h, a) in enumerate(zip(d.home_team, d.away_team)):
            for team, sign in ((h, 1), (a, -1)):
                i = idx[team]
                if i < len(teams) - 1:
                    X[r, len(names) + i] += sign
                else:                      # ratings sum to zero: last team = minus the sum of the others
                    X[r, len(names):] -= sign
        y = d.margin.to_numpy(float)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        s2 = resid @ resid / (len(y) - np.linalg.matrix_rank(X))
        cov = s2 * np.linalg.pinv(X.T @ X)
        for j, n in enumerate(names):
            rows.append({"season": season, "group": n, "home_edge": beta[j], "se": math.sqrt(cov[j, j]),
                         "sigma": math.sqrt(s2), "games": int((grp == n).sum())})
    return pd.DataFrame(rows)


def pool(edges):
    """Inverse-variance average of per-season home edges (more precise seasons count more)."""
    import math
    w = 1 / edges.se ** 2
    est = (w * edges.home_edge).sum() / w.sum()
    return pd.Series({"home_edge": est, "se": 1 / math.sqrt(w.sum()), "sigma": (w * edges.sigma).sum() / w.sum(),
                      "games": edges.games.sum()})


def season_home_edges_wins(df, split=None, labels=None, prior_sd=1.0):
    """Like season_home_edges, but from wins and losses only (scores ignored).

    Fits, separately each season, a logistic model:
        log-odds(home win) = home_edge[group] + rating[home] - rating[away]
    Team ratings get a gentle pull toward average (normal prior with sd `prior_sd` in log-odds),
    because with few games per team an unbeaten or winless team would otherwise get an infinite
    rating. home_edge is in log-odds; 1 / (1 + exp(-home_edge)) is the equal-team home win share.
    Caution: the pull toward average leaves some strength in the home term when home teams are
    usually the stronger side (college non-conference games), so use it for balanced groups.
    """
    import math
    import numpy as np
    rows = []
    for season, d in df.groupby("season"):
        grp = d[split].map(labels).to_numpy() if split else np.array(["all"] * len(d))
        names = sorted(set(grp))
        teams = sorted(set(d.home_team) | set(d.away_team))
        idx = {t: i for i, t in enumerate(teams)}
        X = np.zeros((len(d), len(names) + len(teams)))
        for j, n in enumerate(names):
            X[:, j] = grp == n
        for r, (h, a) in enumerate(zip(d.home_team, d.away_team)):
            X[r, len(names) + idx[h]] += 1
            X[r, len(names) + idx[a]] -= 1
        y = d.home_win.to_numpy(float)
        penalty = np.r_[np.zeros(len(names)), np.full(len(teams), 1 / prior_sd ** 2)]
        beta = np.zeros(X.shape[1])
        for _ in range(100):                       # Newton's method
            p = 1 / (1 + np.exp(-X @ beta))
            H = X.T @ (X * (p * (1 - p))[:, None]) + np.diag(penalty)
            step = np.linalg.solve(H, X.T @ (y - p) - penalty * beta)
            beta += step
            if np.abs(step).max() < 1e-9:
                break
        cov = np.linalg.inv(H)
        for j, n in enumerate(names):
            rows.append({"season": season, "group": n, "home_edge": beta[j], "se": math.sqrt(cov[j, j]),
                         "sigma": float("nan"), "games": int((grp == n).sum())})
    return pd.DataFrame(rows)


def loo_strength_gap(df, split=None, labels=None):
    """Strength gap for each game from ratings fit WITHOUT that game (leave-one-out).

    Uses the standard shortcut for least squares: the prediction for game i with game i left out
    is  y_i - residual_i / (1 - leverage_i).  Subtracting the game's home-edge term leaves the gap
    in team strength, so picking "close matchups" doesn't peek at the game's own result.
    """
    import numpy as np
    out = pd.Series(index=df.index, dtype=float)
    for season, d in df.groupby("season"):
        grp = d[split].map(labels).to_numpy() if split else np.array(["all"] * len(d))
        names = sorted(set(grp))
        teams = sorted(set(d.home_team) | set(d.away_team))
        idx = {t: i for i, t in enumerate(teams)}
        X = np.zeros((len(d), len(names) + len(teams) - 1))
        for j, n in enumerate(names):
            X[:, j] = grp == n
        for r, (h, a) in enumerate(zip(d.home_team, d.away_team)):
            for team, sign in ((h, 1), (a, -1)):
                i = idx[team]
                if i < len(teams) - 1:
                    X[r, len(names) + i] += sign
                else:
                    X[r, len(names):] -= sign
        y = d.margin.to_numpy(float)
        pinv = np.linalg.pinv(X)
        beta = pinv @ y
        resid = y - X @ beta
        lev = np.einsum("ij,ji->i", X, pinv)
        loo_pred = y - resid / np.clip(1 - lev, 1e-9, None)
        home_term = X[:, :len(names)] @ beta[:len(names)]
        out.loc[d.index] = loo_pred - home_term
    return out


def _ridge_ratings(d, home_edge, prior_mean, lam):
    """Team ratings (points) from games `d`, home edge held fixed, pulled toward `prior_mean` (dict)."""
    import numpy as np
    teams = sorted(set(d.home_team) | set(d.away_team) | set(prior_mean))
    idx = {t: i for i, t in enumerate(teams)}
    X = np.zeros((len(d), len(teams)))
    for r, (h, a) in enumerate(zip(d.home_team, d.away_team)):
        X[r, idx[h]] += 1
        X[r, idx[a]] -= 1
    m = np.array([prior_mean.get(t, 0.0) for t in teams])
    y = d.margin.to_numpy(float) - home_edge
    r = np.linalg.solve(X.T @ X + lam * np.eye(len(teams)), X.T @ y + lam * m)
    return dict(zip(teams, r))


def walk_forward(df, first=2016, lam=5.0, carry=0.5):
    """Predict every game using ONLY information available before it was played.

    For each season t (from `first`) and each week w:
      - home edge and result spread (sigma) come from seasons before t (rating model, pooled);
      - team ratings come from season t's games before week w, pulled toward `carry` x last
        season's final ratings (lam = how strongly; new teams start at average).
    Each game gets a home-win probability from a model WITH the home edge and one WITHOUT it
    (ratings refit with the edge set to 0), plus the plain home-win rate of earlier seasons.
    """
    from statistics import NormalDist
    nd = NormalDist()
    edges = season_home_edges(df)
    out = []
    prev = {}
    for t in sorted(df.season.unique()):
        season = df[df.season == t]
        if t >= first:
            past = edges[edges.season < t]
            pooled = pool(past)
            h, sigma = pooled.home_edge, pooled.sigma
            home_rate = df[df.season < t].home_win.mean()
            prior = {k: carry * v for k, v in prev.items()}
            for w in sorted(season.week.unique()):
                train, test = season[season.week < w], season[season.week == w]
                r_with = _ridge_ratings(train, h, prior, lam)
                r_without = _ridge_ratings(train, 0.0, prior, lam)
                for g in test.itertuples():
                    gap_w = r_with.get(g.home_team, 0) - r_with.get(g.away_team, 0)
                    gap_0 = r_without.get(g.home_team, 0) - r_without.get(g.away_team, 0)
                    out.append({"game_id": g.game_id, "season": t, "week": w, "home_win": g.home_win,
                                "p_with_home_edge": nd.cdf((h + gap_w) / sigma),
                                "p_without_home_edge": nd.cdf(gap_0 / sigma),
                                "p_home_rate": home_rate})
        prev = _ridge_ratings(season, edges[edges.season == t].home_edge.iat[0], {}, 1e-6)
    return pd.DataFrame(out)
