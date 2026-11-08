# Does Home Field Advantage Exist in the NFL?

![Home win % by season](charts/01_home_win_by_season.png)

## The question
How much does playing at home help NFL teams, and did it shrink in 2020 when stadiums were mostly empty?

## Key findings
- Home teams won **54.6%** of 2,837 regular-season games from 2015–2025, by **1.8 points** on average.
- In 2020, with few fans, that dropped to **50.4%**, a coin flip, vs **55.0%** in normal seasons. It was already low in 2019 (52.0%), so crowds look like part of the story, not all of it.
- **Miami** had the biggest home boost: **62.5%** at home vs **36.4%** away (+26 points). Seattle and Arizona actually won slightly more often on the road.

| | |
| --- | --- |
| ![2020 vs normal seasons](charts/03_covid_vs_normal.png) | ![Top 10 home boost](charts/02_top10_home_boost.png) |

## How I built it
1. Pulled 11 seasons of game results with [nflreadpy](https://github.com/nflverse/nflreadpy) (nflverse).
2. Cleaned in pandas: regular season only, no neutral sites or ties, relocated teams merged (OAK→LV, SD→LAC, STL→LA).
3. Loaded into a Postgres database (Neon) in its own `nfl` schema.
4. Answered each question with SQL (see [`/sql`](sql)).
5. Visualized with matplotlib.

The full walkthrough is in [`analysis.ipynb`](analysis.ipynb).

## Run it yourself
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo 'DB_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME' > .env
jupyter notebook analysis.ipynb
```

## Tools
Python, pandas, SQL (Postgres), SQLAlchemy, matplotlib, Jupyter

## Data
[nflverse](https://github.com/nflverse) schedules data (CC-BY 4.0)
