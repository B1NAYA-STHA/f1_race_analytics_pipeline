from pathlib import Path

# Project paths
PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
JOLPICA_DIR = RAW_DIR / "jolpica"

# Historical Ergast CSV mirror (pre-2023)
HISTORICAL_DB_URL = (
    "https://raw.githubusercontent.com/rubenv/ergast-mrd/master/f1db_csv.zip"
)

# Jolpica API config
JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"
API_START_YEAR = 2023
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