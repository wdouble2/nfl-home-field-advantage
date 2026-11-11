-- The "fan effect": how much of each league's home edge disappeared in 2020 (few or no fans).
--   drop_in_2020     : normal home win percent minus 2020 home win percent (in percentage points)
--   pct_of_edge_lost : that drop as a share of the normal edge over 50 percent
WITH by_period AS (
    SELECT league,
           100.0 * AVG(CASE WHEN covid_season = 0 THEN 1.0 * home_win END) AS normal_pct,
           100.0 * AVG(CASE WHEN covid_season = 1 THEN 1.0 * home_win END) AS pct_2020,
           SUM(1 - covid_season) AS normal_games,
           SUM(covid_season) AS games_2020
    FROM compare.league_games
    GROUP BY league
)
SELECT league,
       normal_games,
       games_2020,
       ROUND(normal_pct, 1) AS normal_home_win_pct,
       ROUND(pct_2020, 1) AS home_win_pct_2020,
       ROUND(normal_pct - pct_2020, 1) AS drop_in_2020,
       ROUND(100.0 * (normal_pct - pct_2020) / NULLIF(normal_pct - 50, 0), 0) AS pct_of_edge_lost
FROM by_period
ORDER BY league DESC;
