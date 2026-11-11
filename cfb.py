"""Helpers for Part 2: college football (CollegeFootballData.com) vs. the NFL.

Uses requests + pandas only. The API key is read from .env (CFBD_API_KEY) and never printed.
"""
import os
import re
import time

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


def clean(raw):
    """FBS vs. FBS regular-season games at the home team's stadium, finished, no ties.

    Same columns as nfl.games (game_id, season, week, gameday, home_team, away_team,
    home_score, away_score, home_win, margin, covid_season) plus conference info.
    """
    g = raw[(raw.home_classification == "fbs") & (raw.away_classification == "fbs")].copy()
    g = g[~g.neutral_site.astype(bool) & g.completed.astype(bool)]
    g = g.dropna(subset=["home_points", "away_points"])
    g = g[g.home_points != g.away_points]
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
