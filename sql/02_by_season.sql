SELECT season,
       COUNT(*) AS games,
       ROUND(100.0 * AVG(1.0 * home_win), 1) AS home_win_pct,
       ROUND(AVG(1.0 * margin), 1) AS avg_home_margin
FROM nfl.games
GROUP BY season
ORDER BY season;
