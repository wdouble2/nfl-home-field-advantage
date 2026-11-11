# Where Does Home Field Matter Most: NFL or College Football?

![Home win % by season: NFL vs. college conference games, 2015–2025](charts/09_league_by_season.png)

## Part 2: NFL vs. college football

**Question:** In which league does home field matter most, and where do fans matter most?

College home games are often mismatches (big schools host small schools), so the comparison uses three groups: the **NFL** (2,837 games), **college, all FBS** (7,646 FBS-vs-FBS games) and **college, conference games only** (5,627 games between evenly matched teams). The conference-only group is the fair comparison used for the verdict.

### Verdict
1. **When teams are evenly matched, home field is worth about the same in both leagues.** College conference home teams won **55.7%** (95% range 54.4–57.0) vs. **54.6%** in the NFL (52.8–56.5). The gap could easily be luck (p = 0.36).
2. **College only looks bigger because of mismatches.** Counting every FBS game, college home teams won **58.6%** by **4.3 points** on average (NFL: 1.8), because strong schools host weaker visitors.
3. **2020 hit the NFL, not college conference games.** With mostly empty stadiums, the NFL fell from **55.0%** to **50.4%** (about 90% of its edge gone); college conference games stayed at **55.7%**. Neither change is significant on its own (p = 0.16 and p ≈ 1.0), but Part 1's strength-adjusted model finds the NFL drop significant (p = 0.006).

![Normal seasons vs. 2020 by league](charts/08_league_fan_effect.png)

### Limitations
- Some college stadiums allowed partial crowds in 2020 (often 20–25% capacity) while most NFL games had none, so "fans matter more in the NFL" can't be claimed outright.
- In 2020 many college teams played mostly conference games, so that season's schedule differs from normal years.
- Win % is compared, not point margins: college games score more and have bigger blowouts.
- 2020 is a single season, so its numbers are noisy.

### How it was built
- **Data:** CollegeFootballData.com API (`/games`, regular season 2015–2025) pulled with `requests`; columns converted from camelCase to snake_case. Helpers in [`cfb.py`](cfb.py).
- **Cleaning:** both teams FBS, no neutral sites, completed games only, no ties. Same columns as the NFL table (`home_win`, `margin`, `covid_season`) plus `conference_game`.
- **Database:** `cfb.games` table plus a `compare.league_games` view that stacks the NFL and both college groups with a `league` column ([`sql/05`](sql/05_create_league_view.sql)), queried by [`sql/06–08`](sql).
- **Statistics:** Wilson 95% ranges (`proportion_confint`) and two-proportion z-tests (`proportions_ztest`) from statsmodels.

---

# Part 1: How Much Is NFL Home Field Really Worth?

![Strength-adjusted home edge by season, 1999–2025](charts/04_adjusted_hfa_by_season.png)

### The question
How much does playing at home help NFL teams, did it disappear in 2020 when stadiums were mostly empty, and **why** does it exist at all?

### Key findings (27 seasons, 6,878 games, plus play-by-play penalties)
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

### Methods
- **Data:** nflverse schedules 1999–2025 (scores, rest days, roof, weather, kickoff times) and play-by-play 2015–2025 (penalties).
- **Cleaning:** regular season; no neutral sites, ties, or "home" games at borrowed stadiums (2005 Saints, Bills in Toronto, 2010 Metrodome collapse); relocated teams merged.
- **Rating model:** per season, least squares on `home margin = HFA + rating[home] − rating[away]` (ratings sum to zero), giving home field in points with standard errors.
- **Inference:** Wilson intervals for win %, two-proportion and Welch-style z-tests, inverse-variance pooling across seasons, Bonferroni correction for the penalty tests, a heterogeneity (Q) test, empirical-Bayes shrinkage and a split-half check for team effects.
- **Honest limits:** 2020 still had some fans in some stadiums (attendance isn't in the data); one strength rating per team per season; situations overlap, so rest, travel, time zones and division games are also fit jointly.

## Notebooks
- [`league_compare.ipynb`](league_compare.ipynb): Part 2. College pull → clean → load into Postgres → SQL 05–08 → statistics → charts 8–9.
- [`analysis.ipynb`](analysis.ipynb): version 1. Pull → clean → load into Postgres → 4 SQL queries (see [`/sql`](sql)) → charts 1–3.
- [`deep_dive.ipynb`](deep_dive.ipynb): version 2. Everything above, re-run from the raw data. Helper functions are in [`hfa.py`](hfa.py) (pandas + numpy only).

## On the web
- **Live write-up:** [wdouble2.github.io](https://wdouble2.github.io/#work), with an interactive version of the main chart.
- **Live SQL window:** run the version-1 queries (or your own) against the 2015–2025 games, right in the browser.
- **Team Explorer:** pick any team for its ratings by season, home vs. road record, and where its home edge ranks among all 32; compare two teams head to head. Its data comes from [`build_site_data.py`](build_site_data.py); the site's link-preview image comes from [`make_preview_image.py`](make_preview_image.py).

## Run it yourself
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook deep_dive.ipynb      # no database needed
# analysis.ipynb and league_compare.ipynb also load Postgres: put DB_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME in .env
# league_compare.ipynb's first run also needs a free key from collegefootballdata.com/key: CFBD_API_KEY=... in .env
```

## Tools
Python, pandas, NumPy, SQL (Postgres), SQLAlchemy, requests, statsmodels, matplotlib, Jupyter

## Data
- [nflverse](https://github.com/nflverse) schedules and play-by-play data (CC-BY 4.0)
- College football game data from [CollegeFootballData.com](https://collegefootballdata.com)
