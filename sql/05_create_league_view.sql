-- One row per game for three groups, so every comparison query can GROUP BY league.
--   NFL                    : every game in nfl.games (Part 1)
--   College (all FBS)      : every FBS-vs-FBS game in cfb.games
--   College (conference)   : only conference games: evenly matched teams, the fair comparison
-- A college conference game appears in both college groups on purpose (it is part of each group).
CREATE SCHEMA IF NOT EXISTS compare;

CREATE OR REPLACE VIEW compare.league_games AS
SELECT 'NFL' AS league, season, week, home_team, away_team, home_score, away_score,
       home_win, margin, covid_season
FROM nfl.games
UNION ALL
SELECT 'College (all FBS)', season, week, home_team, away_team, home_score, away_score,
       home_win, margin, covid_season
FROM cfb.games
UNION ALL
SELECT 'College (conference)', season, week, home_team, away_team, home_score, away_score,
       home_win, margin, covid_season
FROM cfb.games
WHERE conference_game = 1;
