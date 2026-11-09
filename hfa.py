"""Shared helpers for the NFL home-field-advantage deep dive.

Everything here uses only pandas and numpy (no extra installs).
"""
import math
import numpy as np
import pandas as pd

TEAM_MAP = {"OAK": "LV", "SD": "LAC", "STL": "LA"}   # relocated franchises -> current name

# Approximate home-city coordinates (lat, lon) and time zone (UTC offset in standard time).
# Old abbreviations keep their own city, because travel depends on where a team actually played.
CITY = {
    "ARI": (33.53, -112.26, -7), "ATL": (33.76, -84.40, -5), "BAL": (39.28, -76.62, -5),
    "BUF": (42.77, -78.79, -5), "CAR": (35.23, -80.85, -5), "CHI": (41.86, -87.62, -6),
    "CIN": (39.10, -84.52, -5), "CLE": (41.51, -81.70, -5), "DAL": (32.75, -97.09, -6),
    "DEN": (39.74, -105.02, -7), "DET": (42.34, -83.05, -5), "GB": (44.50, -88.06, -6),
    "HOU": (29.68, -95.41, -6), "IND": (39.76, -86.16, -5), "JAX": (30.32, -81.64, -5),
    "KC": (39.05, -94.48, -6), "LA": (33.95, -118.34, -8), "LAC": (33.95, -118.34, -8),
    "LV": (36.09, -115.18, -8), "MIA": (25.96, -80.24, -5), "MIN": (44.97, -93.26, -6),
    "NE": (42.09, -71.26, -5), "NO": (29.95, -90.08, -6), "NYG": (40.81, -74.07, -5),
    "NYJ": (40.81, -74.07, -5), "PHI": (39.90, -75.17, -5), "PIT": (40.45, -80.02, -5),
    "SEA": (47.60, -122.33, -8), "SF": (37.40, -121.97, -8), "TB": (27.98, -82.50, -5),
    "TEN": (36.17, -86.77, -6), "WAS": (38.91, -76.86, -5),
    "OAK": (37.75, -122.20, -8), "SD": (32.78, -117.12, -8), "STL": (38.63, -90.19, -6),
}


def miles(a, b):
    """Great-circle distance in miles between two team cities."""
    (la1, lo1, _), (la2, lo2, _) = CITY[a], CITY[b]
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def clean(raw, first=1999, last=2025, drop_ties=True):
    """Regular-season games actually played in the home team's own stadium."""
    g = raw[(raw.game_type == "REG") & raw.season.between(first, last)].copy()
    g = g.dropna(subset=["home_score", "away_score"])
    g = g[g.location == "Home"]
    # A "home" game can still be at a borrowed venue (Katrina 2005, Toronto series, snow moves).
    # Keep only games at the home team's most-used stadium that season.
    usual = g.groupby(["season", "home_team"]).stadium_id.agg(lambda s: s.mode().iat[0])
    g = g[g.set_index(["season", "home_team"]).stadium_id.values == usual.loc[list(zip(g.season, g.home_team))].values]
    if drop_ties:
        g = g[g.home_score != g.away_score]
    g["home_city"], g["away_city"] = g.home_team, g.away_team          # keep original for travel
    g["home_team"] = g.home_team.replace(TEAM_MAP)
    g["away_team"] = g.away_team.replace(TEAM_MAP)
    g["margin"] = g.home_score - g.away_score
    g["home_win"] = (g.margin > 0).astype(int)
    g["covid_season"] = (g.season == 2020).astype(int)
    g["miles"] = [miles(h, a) for h, a in zip(g.home_city, g.away_city)]
    g["tz_shift"] = [CITY[h][2] - CITY[a][2] for h, a in zip(g.home_city, g.away_city)]  # + = away team travels east
    g["rest_diff"] = g.home_rest - g.away_rest
    g["primetime"] = (g.gametime.fillna("13:00") >= "19:00").astype(int)
    return g.reset_index(drop=True)


def wilson(k, n, z=1.96):
    """95% Wilson confidence interval for a proportion, returned in percent."""
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def norm_p(z):
    """Two-sided p-value for a z statistic."""
    return math.erfc(abs(z) / math.sqrt(2))


def rating_model(df, y="margin"):
    """Least-squares team ratings with a home-field term:  y = HFA + rating[home] - rating[away].

    Returns (hfa, se, ratings Series). Ratings sum to zero, so they read as points vs. an average team.
    """
    teams = sorted(set(df.home_team) | set(df.away_team))
    idx = {t: i for i, t in enumerate(teams)}
    X = np.zeros((len(df), len(teams) + 1))
    X[:, 0] = 1.0
    for r, (h, a) in enumerate(zip(df.home_team, df.away_team)):
        X[r, 1 + idx[h]] += 1
        X[r, 1 + idx[a]] -= 1
    # sum-to-zero constraint: replace last team column by subtracting it from the others
    Xc = X[:, :-1] - np.outer(X[:, -1], np.r_[0, np.ones(len(teams) - 1)])
    yv = df[y].to_numpy(float)
    beta, *_ = np.linalg.lstsq(Xc, yv, rcond=None)
    resid = yv - Xc @ beta
    dof = len(yv) - Xc.shape[1]
    s2 = resid @ resid / dof
    cov = s2 * np.linalg.pinv(Xc.T @ Xc)
    r = np.r_[beta[1:], -beta[1:].sum()]
    return beta[0], math.sqrt(cov[0, 0]), pd.Series(r, index=teams), math.sqrt(s2)


def adjusted_edge(df, y="margin"):
    """Per-game home edge after removing team strength (fit separately each season)."""
    out = pd.Series(index=df.index, dtype=float)
    for s, d in df.groupby("season"):
        _, _, r, _ = rating_model(d, y)
        out.loc[d.index] = d[y] - (r.loc[d.home_team].to_numpy() - r.loc[d.away_team].to_numpy())
    return out


def mean_ci(x):
    x = np.asarray(x, float)
    m, se = x.mean(), x.std(ddof=1) / math.sqrt(len(x))
    return m, m - 1.96 * se, m + 1.96 * se, se
