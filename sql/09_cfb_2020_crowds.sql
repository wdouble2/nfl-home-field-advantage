-- 2020 college games only: did home teams do better when more fans were allowed in?
-- Attendance comes from CollegeFootballData.com (missing for a few games).
SELECT CASE WHEN attendance <= 1000 THEN '1) 1,000 or fewer'
            WHEN attendance <= 10000 THEN '2) 1,001 to 10,000'
            ELSE '3) more than 10,000' END AS crowd,
       COUNT(*) AS games,
       ROUND(100.0 * AVG(1.0 * home_win), 1) AS home_win_pct,
       ROUND(AVG(1.0 * margin), 1) AS avg_home_margin
FROM cfb.games
WHERE season = 2020 AND attendance IS NOT NULL
GROUP BY 1
ORDER BY 1;
