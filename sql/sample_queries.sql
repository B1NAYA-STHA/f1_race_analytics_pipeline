-- Sample validation and analytics queries for the F1 warehouse
-- Use these queries to explore and validate the loaded data

-- ============================================
-- VALIDATION QUERIES
-- ============================================

-- 1. Row counts by table
SELECT 'seasons' as table_name, COUNT(*) as row_count FROM bronze.seasons
UNION ALL
SELECT 'status', COUNT(*) FROM bronze.status
UNION ALL
SELECT 'circuits', COUNT(*) FROM bronze.circuits
UNION ALL
SELECT 'drivers', COUNT(*) FROM bronze.drivers
UNION ALL
SELECT 'constructors', COUNT(*) FROM bronze.constructors
UNION ALL
SELECT 'races', COUNT(*) FROM bronze.races
UNION ALL
SELECT 'results', COUNT(*) FROM bronze.results
UNION ALL
SELECT 'qualifying', COUNT(*) FROM bronze.qualifying
UNION ALL
SELECT 'sprint_results', COUNT(*) FROM bronze.sprint_results
UNION ALL
SELECT 'lap_times', COUNT(*) FROM bronze.lap_times
UNION ALL
SELECT 'pit_stops', COUNT(*) FROM bronze.pit_stops
UNION ALL
SELECT 'driver_standings', COUNT(*) FROM bronze.driver_standings
UNION ALL
SELECT 'constructor_standings', COUNT(*) FROM bronze.constructor_standings
ORDER BY row_count DESC;


-- 2. Data source distribution
SELECT 
    "source",
    COUNT(*) as count
FROM bronze.drivers
GROUP BY "source";


-- 3. Latest races loaded
SELECT 
    "year",
    "round",
    "name",
    "date",
    "source"
FROM bronze.races
ORDER BY "year" DESC, "round" DESC
LIMIT 10;


-- 4. Check for missing foreign keys (orphaned results)
SELECT 
    COUNT(*) as orphaned_results
FROM bronze.results r
WHERE r."raceId" IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM bronze.races ra WHERE ra."raceId" = r."raceId"
);


-- 5. Driver statistics
SELECT 
    d."driverId",
    d."forename",
    d."surname",
    d."nationality",
    COUNT(r."resultId") as races,
    COUNT(CASE WHEN r."position" = '1' THEN 1 END) as wins,
    COUNT(CASE WHEN r."position" IN ('1', '2', '3') THEN 1 END) as podiums
FROM bronze.drivers d
LEFT JOIN bronze.results r ON d."driverId" = r."driverId"
WHERE d."source" = 'api'  -- Show only newer API drivers
GROUP BY d."driverId", d."forename", d."surname", d."nationality"
ORDER BY wins DESC, podiums DESC;


-- ============================================
-- ANALYTICS QUERIES
-- ============================================

-- 6. Race results for latest season
SELECT 
    r."year",
    r."round",
    r."name" as race_name,
    c."name" as circuit_name,
    COUNT(*) as finishers
FROM bronze.races r
JOIN bronze.circuits c ON r."circuitId" = c."circuitId"
LEFT JOIN bronze.results res ON r."raceId" = res."raceId"
WHERE r."year" = (SELECT MAX(CAST("year" AS INTEGER)) FROM bronze.races)
GROUP BY r."year", r."round", r."name", c."name"
ORDER BY r."round";


-- 7. Constructor performance this year
SELECT 
    con."constructorId",
    con."name",
    COUNT(res."resultId") as races,
    COUNT(CASE WHEN res."position" = '1' THEN 1 END) as wins,
    ROUND(AVG(CAST(NULLIF(res."points", 'NULL') AS NUMERIC)), 2) as avg_points
FROM bronze.constructors con
LEFT JOIN bronze.results res ON con."constructorId" = res."constructorId"
LEFT JOIN bronze.races ra ON res."raceId" = ra."raceId"
WHERE ra."year" = (SELECT MAX(CAST("year" AS INTEGER)) FROM bronze.races)
GROUP BY con."constructorId", con."name"
ORDER BY wins DESC, avg_points DESC;


-- 8. Pit stop strategy comparison
SELECT 
    r."year",
    r."round",
    r."name",
    d."forename" || ' ' || d."surname" as driver,
    COUNT(ps."stop") as pit_stops,
    MIN(CAST(NULLIF(ps."milliseconds", 'NULL') AS NUMERIC)) as fastest_stop_ms,
    MAX(CAST(NULLIF(ps."milliseconds", 'NULL') AS NUMERIC)) as slowest_stop_ms
FROM bronze.pit_stops ps
JOIN bronze.drivers d ON ps."driverId" = d."driverId"
JOIN bronze.races r ON ps."raceId" = r."raceId"
WHERE r."year" = (SELECT MAX(CAST("year" AS INTEGER)) FROM bronze.races)
GROUP BY r."year", r."round", r."name", d."forename", d."surname"
ORDER BY r."round", pit_stops DESC;


-- 9. Lap time analysis for a specific race (adjust race details as needed)
SELECT 
    d."forename" || ' ' || d."surname" as driver,
    lt."lap",
    lt."time",
    CAST(NULLIF(lt."milliseconds", 'NULL') AS NUMERIC) as milliseconds,
    lt."position"
FROM bronze.lap_times lt
JOIN bronze.drivers d ON lt."driverId" = d."driverId"
JOIN bronze.races r ON lt."raceId" = r."raceId"
WHERE r."year" = (SELECT MAX(CAST("year" AS INTEGER)) FROM bronze.races)
AND r."round" = '1'  -- First race of the year
ORDER BY lt."lap", lt."milliseconds" ASC
LIMIT 50;


-- 10. Qualifying performance vs race results
SELECT 
    r."year",
    r."round",
    d."forename" || ' ' || d."surname" as driver,
    q."position" as quali_pos,
    res."grid" as grid_pos,
    res."position" as race_pos,
    CAST(NULLIF(res."points", 'NULL') AS NUMERIC) as points
FROM bronze.qualifying q
JOIN bronze.drivers d ON q."driverId" = d."driverId"
JOIN bronze.races r ON q."raceId" = r."raceId"
LEFT JOIN bronze.results res ON r."raceId" = res."raceId" AND d."driverId" = res."driverId"
WHERE r."year" = (SELECT MAX(CAST("year" AS INTEGER)) FROM bronze.races)
ORDER BY r."round", CAST(q."position" AS INTEGER);
