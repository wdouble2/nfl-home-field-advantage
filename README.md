# How Much Is NFL Home Field Really Worth?

![Strength-adjusted home edge by season, 1999–2025](charts/04_adjusted_hfa_by_season.png)

## The question
How much does playing at home help NFL teams, did it disappear in 2020 when stadiums were mostly empty, and **why** does it exist at all?

## Key findings (27 seasons, 6,878 games, plus play-by-play penalties)
1. **Home field is worth about 2.3 points** against an equally good opponent, and it's slowly shrinking: ~2.6 pts in 1999–2009, ~2.2 in 2010–2019, ~2.0 since 2021.
2. **2020 really was different, but you need the right method to show it.** Raw win % dropped to 50.4% (vs. 55.0%), but one season is too noisy to prove that (p = 0.16). After removing team strength with a rating model, 2020's home edge was **+0.1 pts vs. +2.2** in other seasons (**p = 0.006**). 2019 was also near zero, so 2020 is the clearest low year, not the only one.
3. **Rest is the situation that matters most.** Each extra day of rest is worth ~0.2 pts (p = 0.001); when the visitor has 3+ more days of rest, home field falls to ~0.9 pts. Division games trim it by ~0.6 pts.
4. **Popular theories don't hold up:** cold weather, domes, primetime, Denver's altitude and West-coast "body clock" trips show no reliable extra edge once team strength is removed.
5. **Crowds don't seem to work through the referees.** Visitors draw ~0.35 more flags and ~3 more penalty yards per game, and that gap was **the same in 2020** with empty stands.
6. **Team-specific home edges are mostly noise.** The spread across teams is about what chance produces (p ≈ 0.26), and a team's home boost in 1999–2011 doesn't predict 2012–2025 (r = −0.11). The "Miami +26" from the simple win-% table in version 1 was a small-sample streak.

| | |
| --- | --- |
| ![Situations](charts/05_situations.png) | ![Team boosts](charts/07_team_boosts.png) |

![Penalty gap](charts/06_penalty_gap.png)

## Methods
- **Data:** nflverse schedules 1999–2025 (scores, rest days, roof, weather, kickoff times) and play-by-play 2015–2025 (penalties).
- **Cleaning:** regular season; no neutral sites, ties, or "home" games at borrowed stadiums (2005 Saints, Bills in Toronto, 2010 Metrodome collapse); relocated teams merged.
- **Rating model:** per season, least squares on `home margin = HFA + rating[home] − rating[away]` (ratings sum to zero), giving home field in points with standard errors.
- **Inference:** Wilson intervals for win %, two-proportion and Welch-style z-tests, inverse-variance pooling across seasons, Bonferroni correction for the penalty tests, a heterogeneity (Q) test, empirical-Bayes shrinkage and a split-half check for team effects.
- **Honest limits:** 2020 still had some fans in some stadiums (attendance isn't in the data); one strength rating per team per season; situations overlap, so rest, travel, time zones and division games are also fit jointly.

## Notebooks
- [`analysis.ipynb`](analysis.ipynb): version 1. Pull → clean → load into Postgres → 4 SQL queries (see [`/sql`](sql)) → charts 1–3.
- [`deep_dive.ipynb`](deep_dive.ipynb): version 2. Everything above, re-run from the raw data. Helper functions are in [`hfa.py`](hfa.py) (pandas + numpy only).

## Run it yourself
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook deep_dive.ipynb      # no database needed
# analysis.ipynb also loads Postgres: put DB_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME in .env
```

## Tools
Python, pandas, NumPy, SQL (Postgres), SQLAlchemy, matplotlib, Jupyter

## Data
[nflverse](https://github.com/nflverse) schedules and play-by-play data (CC-BY 4.0)
