-- Home win percent by league and season (look at 2020).
SELECT league,
       season,
       COUNT(*) AS games,
       ROUND(100.0 * AVG(1.0 * home_win), 1) AS home_win_pct
FROM compare.league_games
GROUP BY league, season
ORDER BY league, season;
