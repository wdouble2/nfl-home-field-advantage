SELECT CASE WHEN covid_season = 1 THEN '2020 (few fans)' ELSE 'Normal seasons' END AS period,
       COUNT(*) AS games,
       ROUND(100.0 * AVG(1.0 * home_win), 1) AS home_win_pct
FROM nfl.games
GROUP BY covid_season
ORDER BY covid_season;   -- normal seasons first, 2020 second
