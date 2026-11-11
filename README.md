# Where Does Home Field Matter Most: NFL or College Football?

![Strength-adjusted home edge by season: NFL vs. college conference games, 2015–2025](charts/09_league_by_season.png)

## Part 2: NFL vs. college football

**Question:** In which league does home field matter most, and where do fans matter most?

**Data:** 2,837 NFL games and 7,586 college games between two FBS teams (5,580 of them conference games), regular season 2015–2025.

**The trap:** raw home win % says college home field is far bigger (58.6% vs. 54.6%). But strong schools often schedule weaker visitors at home, and college talent gaps are wider. So the comparison removes team strength with Part 1's rating model and measures the home edge **in points between two equally good teams**.

### Verdict
1. **Home field is worth about 2 points in both leagues.** In normal seasons: college conference games **+2.4 pts** (95% range 2.0–2.8), NFL **+1.9 pts** (1.4–2.4). Between equally good teams, that's a home win **56.6%** vs. **56.2%** of the time. College is slightly higher, but the gap could be luck (p = 0.11).
2. **College only looks bigger because of scheduling.** In non-conference games the home team starts about 7 points stronger and wins 66.8% of the time. With team strength removed, non-conference games show the same +2.4-point edge as conference games.
3. **Home field shrank in 2020 in both leagues.** NFL: +1.9 → **+0.1 pts** (p = 0.03). College conference games: +2.4 → **+1.0 pts** (p = 0.055, just short of the usual 0.05 bar; all FBS games: p = 0.02). The two drops are about the same size (p = 0.75 for a difference), so there's no evidence that fans matter more in one league than the other.
4. **That fits a crowd effect, but doesn't prove one.** It's a single season, and the NFL's 2019 edge (−0.05 pts, with full stadiums) was just as low. College attendance in 2020 can't settle it either: crowd size mostly followed conference rules, and comparing games within the same conference, bigger crowds showed almost no extra edge (p = 0.83).

![Normal seasons vs. 2020 by league, team strength removed](charts/08_league_fan_effect.png)

### Limitations
- 2020 is one season, and college teams played only 3–12 games, so 2020 estimates are noisy (wide 95% ranges).
- "2020" means fewer fans, not zero: many college stadiums allowed partial crowds, and a few NFL stadiums did too. Recorded attendance of 0 may sometimes mean "not recorded".
- 2020 college schedules were mostly conference games, and some conferences played shortened seasons.
- Raw win % isn't comparable between leagues (see "The trap"), so the verdict uses points with team strength removed.
- Data quirks: the API labels conference title games only from 2022, so earlier ones are found by date; and its venue labels are sometimes inconsistent, so the usual-stadium rule drops a few genuine home games (negligible effect on results).

### How it was built
- **Data:** CollegeFootballData.com API (`/games`, regular season 2015–2025) pulled with `requests`; columns converted from camelCase to snake_case. Helpers in [`cfb.py`](cfb.py).
- **Cleaning:** both teams FBS; no neutral sites, unfinished games, ties or conference title games (the higher seed hosts); only games at the home team's usual stadium (same rule as Part 1).
- **Database:** `cfb.games` table plus a `compare.league_games` view that stacks the NFL and both college groups with a `league` column ([`sql/05`](sql/05_create_league_view.sql)), queried by [`sql/06–09`](sql).
- **Statistics:** raw win % with Wilson 95% ranges (`proportion_confint`) and two-proportion z-tests (`proportions_ztest`). Then Part 1's rating model fit each season (`margin = home edge + rating[home] − rating[away]`), with separate home edges for college conference and non-conference games, model-based standard errors and inverse-variance pooling across seasons. (In 2020 the college schedule split into four groups of teams that never met; the home edge is still measured within each group.) Differences use z-tests; the crowd check uses an OLS trend with and without conference.
- **Review:** checked by a separate AI review agent (data, statistics and every number in this README) before publishing; its findings are fixed here.

### What changed from the first version of Part 2
The first version (commit `590adbb`) compared raw win % only and said college conference games "didn't budge" in 2020 while the NFL lost its edge. A review found that wrong: raw win % hid a similar drop in college. It also kept 39 conference title games hosted by the higher seed and 21 games away from the home team's usual stadium, and it described conference games as "evenly matched" (they aren't; they're balanced between home and away teams). All of this is fixed above.

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
- [`league_compare.ipynb`](league_compare.ipynb): Part 2. College pull → clean → load into Postgres → SQL 05–09 → raw and strength-adjusted statistics → charts 8–9.
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
