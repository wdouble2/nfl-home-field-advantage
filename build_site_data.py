"""Build the data file behind the website's Team Explorer.

Run:  .venv/bin/python build_site_data.py  [output path]
Writes teams.json (default: ../portfolio-site/data/teams.json).
Uses the same cleaning and rating model as deep_dive.ipynb (see hfa.py).
"""
import json, math, sys
from pathlib import Path
import nflreadpy as nfl
import pandas as pd
from hfa import clean, rating_model, adjusted_edge

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "portfolio-site" / "data" / "teams.json"
NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens", "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers", "CHI": "Chicago Bears", "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys", "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars", "KC": "Kansas City Chiefs",
    "LA": "Los Angeles Rams", "LAC": "Los Angeles Chargers", "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings", "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers", "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}

raw = nfl.load_schedules(list(range(1999, 2026))).to_pandas()
g = clean(raw)
g["edge"] = adjusted_edge(g)

# Team strength by season (points vs. an average team, home field removed).
ratings = {}
for s, d in g.groupby("season"):
    _, _, r, _ = rating_model(d, "margin")
    ratings[int(s)] = r

# Extra home boost per team (strength-adjusted, normal-crowd seasons), as in deep_dive.ipynb section 6.
n = g[g.season != 2020]; H = n.edge.mean()
boost = {}
for t in NAMES:
    h = n.loc[n.home_team == t, "edge"]; a = n.loc[n.away_team == t, "edge"]
    boost[t] = ((h.mean() - H) + (a.mean() - H), math.sqrt(h.var() / len(h) + a.var() / len(a)))
order = sorted(boost, key=lambda t: -boost[t][0])

teams = {}
for t in NAMES:
    hm, aw = g[g.home_team == t], g[g.away_team == t]
    seasons = []
    for s in range(1999, 2026):
        hs, as_ = hm[hm.season == s], aw[aw.season == s]
        seasons.append([s,
                        round(float(ratings[s][t]), 1) if t in ratings[s].index else None,   # None = team didn't exist yet
                        int(hs.home_win.sum()), int(len(hs) - hs.home_win.sum()),
                        int((1 - as_.home_win).sum()), int(as_.home_win.sum()),
                        round(float(hs.margin.mean()), 1) if len(hs) else None,
                        round(float(-as_.margin.mean()), 1) if len(as_) else None])
    best = max((r for r in seasons if r[1] is not None), key=lambda r: r[1])
    b, se = boost[t]
    teams[t] = {
        "name": NAMES[t],
        "home": [int(hm.home_win.sum()), int(len(hm) - hm.home_win.sum())],
        "road": [int((1 - aw.home_win).sum()), int(aw.home_win.sum())],
        "home_margin": round(float(hm.margin.mean()), 1), "road_margin": round(float(-aw.margin.mean()), 1),
        "boost": round(b, 2), "boost_lo": round(b - 1.96 * se, 2), "boost_hi": round(b + 1.96 * se, 2),
        "boost_rank": order.index(t) + 1,
        "best": [best[0], best[1]],
        "seasons": seasons,   # [season, rating, home W, home L, road W, road L, home avg margin, road avg margin]
    }

# Head-to-head for every pair (all games, both stadiums).
pairs = {}
codes = sorted(NAMES)
for i, a in enumerate(codes):
    for b in codes[i + 1:]:
        d = g[((g.home_team == a) & (g.away_team == b)) | ((g.home_team == b) & (g.away_team == a))].sort_values(["season", "week"])
        if not len(d):
            continue
        a_win = ((d.home_team == a) & (d.margin > 0)) | ((d.away_team == a) & (d.margin < 0))
        at_a, at_b = d[d.home_team == a], d[d.home_team == b]
        a_margin = (d.margin.where(d.home_team == a, -d.margin)).mean()
        last = [[int(r.season), int(r.week), r.home_team, int(r.home_score), r.away_team, int(r.away_score)] for r in d.tail(5).itertuples()][::-1]
        pairs[f"{a}|{b}"] = {
            "games": len(d), "a_wins": int(a_win.sum()),
            "at_a": [int(at_a.home_win.sum()), int(len(at_a) - at_a.home_win.sum())],
            "at_b": [int(at_b.home_win.sum()), int(len(at_b) - at_b.home_win.sum())],
            "a_margin": round(float(a_margin), 1), "last": last,
        }

out = {"league": {"hfa": round(H, 2), "seasons": [1999, 2025], "games": len(g)}, "teams": teams, "pairs": pairs}
OUT.write_text(json.dumps(out, separators=(",", ":"), allow_nan=False))   # fail loudly instead of writing invalid JSON
print(f"wrote {OUT} ({OUT.stat().st_size/1024:.0f} KB): {len(teams)} teams, {len(pairs)} matchups, league HFA {H:.2f}")
