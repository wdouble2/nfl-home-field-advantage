-- Home win percent, how far above a coin flip (edge_over_50), and average home margin, by league.
SELECT league,
       COUNT(*) AS games,
       ROUND(100.0 * AVG(1.0 * home_win), 1) AS home_win_pct,
       ROUND(100.0 * AVG(1.0 * home_win) - 50, 1) AS edge_over_50,
       ROUND(AVG(1.0 * margin), 1) AS avg_home_margin
FROM compare.league_games
GROUP BY league
ORDER BY home_win_pct DESC;
