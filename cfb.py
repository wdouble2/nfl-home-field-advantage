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
