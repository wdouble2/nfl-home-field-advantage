WITH team_games AS (
    SELECT home_team AS team, 'home' AS venue, home_win AS won FROM nfl.games
    UNION ALL
    SELECT away_team AS team, 'away' AS venue, 1 - home_win AS won FROM nfl.games
)
SELECT team,
       ROUND(100.0 * AVG(CASE WHEN venue = 'home' THEN 1.0 * won END), 1) AS home_win_pct,
       ROUND(100.0 * AVG(CASE WHEN venue = 'away' THEN 1.0 * won END), 1) AS away_win_pct,
       ROUND(100.0 * AVG(CASE WHEN venue = 'home' THEN 1.0 * won END)
           - 100.0 * AVG(CASE WHEN venue = 'away' THEN 1.0 * won END), 1) AS home_boost
FROM team_games
GROUP BY team
ORDER BY home_boost DESC;
