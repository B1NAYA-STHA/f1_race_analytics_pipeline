from pathlib import Path

# Project paths
PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
JOLPICA_DIR = RAW_DIR / "jolpica"
BRONZE_DIR = DATA_DIR / "bronze"

# Historical Ergast CSV source (1950-2024)
HISTORICAL_DB_URL = (
    "https://raceoptidatapublicfiles.blob.core.windows.net/ergast2024/ergast_2024.zip"
)
HISTORICAL_EXPECTED_LAST_YEAR = 2024  # races.csv must reach this year to be trusted

# Raw historical tables (14 tables, in the order they land in data/raw)
HISTORICAL_TABLES = [
    "seasons",
    "status",
    "circuits",
    "drivers",
    "constructors",
    "races",
    "results",
    "qualifying",
    "sprint_results",
    "lap_times",
    "pit_stops",
    "driver_standings",
    "constructor_standings",
    "constructor_results",
]

# Maps zip filenames (no underscores) to our canonical table names
HISTORICAL_FILE_MAP = {
    "circuits.csv": "circuits.csv",
    "constructorresults.csv": "constructor_results.csv",
    "constructors.csv": "constructors.csv",
    "constructorstandings.csv": "constructor_standings.csv",
    "drivers.csv": "drivers.csv",
    "driverstandings.csv": "driver_standings.csv",
    "laptimes.csv": "lap_times.csv",
    "pitstops.csv": "pit_stops.csv",
    "qualifying.csv": "qualifying.csv",
    "races.csv": "races.csv",
    "results.csv": "results.csv",
    "seasons.csv": "seasons.csv",
    "sprintresults.csv": "sprint_results.csv",
    "status.csv": "status.csv",
}

# Jolpica API config
JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"
API_START_YEAR = 2025  # API covers from here on; CSV source covers 1950-2024
RATE_LIMIT_INTERVAL = 2.5  # seconds between requests
PAGE_LIMIT = 100  # max items per API page
MAX_RETRIES = 7  # retry attempts on 429 before failing
BACKOFF_BASE = 5  # seconds, doubles each attempt
MAX_BACKOFF = 120  # cap on each backoff wait

# Endpoint lists
GLOBAL_ENDPOINTS = ["seasons", "status"]

SEASON_ENDPOINTS = [
    "circuits",
    "drivers",
    "constructors",
]

ROUND_ENDPOINTS = [
    "results",
    "qualifying",
    "sprint",
    "pitstops",
    "laps",
    "driverstandings",
    "constructorstandings",
]

# Standings endpoints return StandingsTable instead of RaceTable
STANDINGS_ENDPOINTS = ["driverstandings", "constructorstandings"]

# Maps endpoint name to the JSON key holding its items
ROUND_ITEMS_KEY = {
    "results": "Results",
    "qualifying": "QualifyingResults",
    "sprint": "SprintResults",
    "pitstops": "PitStops",
    "laps": "Laps",
    "driverstandings": "DriverStandings",
    "constructorstandings": "ConstructorStandings",
}
