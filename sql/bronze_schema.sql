-- Bronze schema creation script
-- Run this manually if needed or use src/warehouse/loader.py to automate

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS marts;

-- Seasons
CREATE TABLE IF NOT EXISTS bronze.seasons (
    "year" TEXT NOT NULL,
    "url" TEXT
);

-- Status (primary key)
CREATE TABLE IF NOT EXISTS bronze.status (
    "statusId" TEXT PRIMARY KEY,
    "status" TEXT NOT NULL,
    "source" TEXT
);

-- Circuits (primary key)
CREATE TABLE IF NOT EXISTS bronze.circuits (
    "circuitId" TEXT PRIMARY KEY,
    "circuitRef" TEXT NOT NULL,
    "name" TEXT,
    "location" TEXT,
    "country" TEXT,
    "lat" NUMERIC,
    "lng" NUMERIC,
    "alt" TEXT,
    "url" TEXT,
    "source" TEXT
);

-- Drivers (primary key)
CREATE TABLE IF NOT EXISTS bronze.drivers (
    "driverId" TEXT PRIMARY KEY,
    "driverRef" TEXT NOT NULL,
    "number" TEXT,
    "code" TEXT,
    "forename" TEXT,
    "surname" TEXT,
    "dob" TEXT,
    "nationality" TEXT,
    "url" TEXT,
    "source" TEXT
);

-- Constructors (primary key)
CREATE TABLE IF NOT EXISTS bronze.constructors (
    "constructorId" TEXT PRIMARY KEY,
    "constructorRef" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "nationality" TEXT,
    "url" TEXT,
    "source" TEXT
);

-- Races (primary key)
CREATE TABLE IF NOT EXISTS bronze.races (
    "raceId" TEXT PRIMARY KEY,
    "year" TEXT,
    "round" TEXT,
    "circuitId" TEXT,
    "name" TEXT,
    "date" TEXT,
    "time" TEXT,
    "url" TEXT,
    "fp1_date" TEXT,
    "fp1_time" TEXT,
    "fp2_date" TEXT,
    "fp2_time" TEXT,
    "fp3_date" TEXT,
    "fp3_time" TEXT,
    "quali_date" TEXT,
    "quali_time" TEXT,
    "sprint_date" TEXT,
    "sprint_time" TEXT,
    "source" TEXT
);

-- Results (primary key)
CREATE TABLE IF NOT EXISTS bronze.results (
    "resultId" TEXT PRIMARY KEY,
    "raceId" TEXT,
    "driverId" TEXT,
    "constructorId" TEXT,
    "number" TEXT,
    "grid" TEXT,
    "position" TEXT,
    "positionText" TEXT,
    "positionOrder" TEXT,
    "points" TEXT,
    "laps" TEXT,
    "time" TEXT,
    "milliseconds" TEXT,
    "fastestLap" TEXT,
    "rank" TEXT,
    "fastestLapTime" TEXT,
    "fastestLapSpeed" TEXT,
    "statusId" TEXT,
    "source" TEXT
);

-- Qualifying (primary key)
CREATE TABLE IF NOT EXISTS bronze.qualifying (
    "qualifyId" TEXT PRIMARY KEY,
    "raceId" TEXT,
    "driverId" TEXT,
    "constructorId" TEXT,
    "number" TEXT,
    "position" TEXT,
    "q1" TEXT,
    "q2" TEXT,
    "q3" TEXT,
    "source" TEXT
);

-- Sprint Results (primary key)
CREATE TABLE IF NOT EXISTS bronze.sprint_results (
    "sprintResultId" TEXT PRIMARY KEY,
    "raceId" TEXT,
    "driverId" TEXT,
    "constructorId" TEXT,
    "number" TEXT,
    "grid" TEXT,
    "position" TEXT,
    "positionText" TEXT,
    "positionOrder" TEXT,
    "points" TEXT,
    "laps" TEXT,
    "time" TEXT,
    "milliseconds" TEXT,
    "fastestLap" TEXT,
    "fastestLapTime" TEXT,
    "statusId" TEXT,
    "source" TEXT
);

-- Lap Times (no primary key, fact table)
CREATE TABLE IF NOT EXISTS bronze.lap_times (
    "raceId" TEXT,
    "driverId" TEXT,
    "lap" TEXT,
    "position" TEXT,
    "time" TEXT,
    "milliseconds" TEXT,
    "source" TEXT
);

-- Pit Stops (no primary key, fact table)
CREATE TABLE IF NOT EXISTS bronze.pit_stops (
    "raceId" TEXT,
    "driverId" TEXT,
    "stop" TEXT,
    "lap" TEXT,
    "time" TEXT,
    "duration" TEXT,
    "milliseconds" TEXT,
    "source" TEXT
);

-- Driver Standings (primary key)
CREATE TABLE IF NOT EXISTS bronze.driver_standings (
    "driverStandingsId" TEXT PRIMARY KEY,
    "raceId" TEXT,
    "driverId" TEXT,
    "points" TEXT,
    "position" TEXT,
    "positionText" TEXT,
    "wins" TEXT,
    "source" TEXT
);

-- Constructor Standings (primary key)
CREATE TABLE IF NOT EXISTS bronze.constructor_standings (
    "constructorStandingsId" TEXT PRIMARY KEY,
    "raceId" TEXT,
    "constructorId" TEXT,
    "points" TEXT,
    "position" TEXT,
    "positionText" TEXT,
    "wins" TEXT,
    "source" TEXT
);
