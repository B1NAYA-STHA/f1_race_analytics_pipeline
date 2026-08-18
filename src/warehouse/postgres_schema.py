"""PostgreSQL schema definitions for the medallion architecture."""

BRONZE_SCHEMA = "bronze"
SILVER_SCHEMA = "silver"
MARTS_SCHEMA = "marts"


# SQL to create schemas
CREATE_SCHEMAS = f"""
CREATE SCHEMA IF NOT EXISTS {BRONZE_SCHEMA};
CREATE SCHEMA IF NOT EXISTS {SILVER_SCHEMA};
CREATE SCHEMA IF NOT EXISTS {MARTS_SCHEMA};
"""


# Bronze table definitions (mirrors normalized CSV structure)
BRONZE_TABLES = {
    "seasons": [
        ("year", "TEXT NOT NULL"),
        ("url", "TEXT"),
    ],
    "status": [
        ("statusId", "TEXT PRIMARY KEY"),
        ("status", "TEXT NOT NULL"),
        ("source", "TEXT"),
    ],
    "circuits": [
        ("circuitId", "TEXT PRIMARY KEY"),
        ("circuitRef", "TEXT NOT NULL"),
        ("name", "TEXT"),
        ("location", "TEXT"),
        ("country", "TEXT"),
        ("lat", "NUMERIC"),
        ("lng", "NUMERIC"),
        ("alt", "TEXT"),
        ("url", "TEXT"),
        ("source", "TEXT"),
    ],
    "drivers": [
        ("driverId", "TEXT PRIMARY KEY"),
        ("driverRef", "TEXT NOT NULL"),
        ("number", "TEXT"),
        ("code", "TEXT"),
        ("forename", "TEXT"),
        ("surname", "TEXT"),
        ("dob", "TEXT"),
        ("nationality", "TEXT"),
        ("url", "TEXT"),
        ("source", "TEXT"),
    ],
    "constructors": [
        ("constructorId", "TEXT PRIMARY KEY"),
        ("constructorRef", "TEXT NOT NULL"),
        ("name", "TEXT NOT NULL"),
        ("nationality", "TEXT"),
        ("url", "TEXT"),
        ("source", "TEXT"),
    ],
    "races": [
        ("raceId", "TEXT PRIMARY KEY"),
        ("year", "TEXT"),
        ("round", "TEXT"),
        ("circuitId", "TEXT"),
        ("name", "TEXT"),
        ("date", "TEXT"),
        ("time", "TEXT"),
        ("url", "TEXT"),
        ("fp1_date", "TEXT"),
        ("fp1_time", "TEXT"),
        ("fp2_date", "TEXT"),
        ("fp2_time", "TEXT"),
        ("fp3_date", "TEXT"),
        ("fp3_time", "TEXT"),
        ("quali_date", "TEXT"),
        ("quali_time", "TEXT"),
        ("sprint_date", "TEXT"),
        ("sprint_time", "TEXT"),
        ("source", "TEXT"),
    ],
    "results": [
        ("resultId", "TEXT PRIMARY KEY"),
        ("raceId", "TEXT"),
        ("driverId", "TEXT"),
        ("constructorId", "TEXT"),
        ("number", "TEXT"),
        ("grid", "TEXT"),
        ("position", "TEXT"),
        ("positionText", "TEXT"),
        ("positionOrder", "TEXT"),
        ("points", "TEXT"),
        ("laps", "TEXT"),
        ("time", "TEXT"),
        ("milliseconds", "TEXT"),
        ("fastestLap", "TEXT"),
        ("rank", "TEXT"),
        ("fastestLapTime", "TEXT"),
        ("fastestLapSpeed", "TEXT"),
        ("statusId", "TEXT"),
        ("source", "TEXT"),
    ],
    "qualifying": [
        ("qualifyId", "TEXT PRIMARY KEY"),
        ("raceId", "TEXT"),
        ("driverId", "TEXT"),
        ("constructorId", "TEXT"),
        ("number", "TEXT"),
        ("position", "TEXT"),
        ("q1", "TEXT"),
        ("q2", "TEXT"),
        ("q3", "TEXT"),
        ("source", "TEXT"),
    ],
    "sprint_results": [
        ("sprintResultId", "TEXT PRIMARY KEY"),
        ("raceId", "TEXT"),
        ("driverId", "TEXT"),
        ("constructorId", "TEXT"),
        ("number", "TEXT"),
        ("grid", "TEXT"),
        ("position", "TEXT"),
        ("positionText", "TEXT"),
        ("positionOrder", "TEXT"),
        ("points", "TEXT"),
        ("laps", "TEXT"),
        ("time", "TEXT"),
        ("milliseconds", "TEXT"),
        ("fastestLap", "TEXT"),
        ("fastestLapTime", "TEXT"),
        ("statusId", "TEXT"),
        ("source", "TEXT"),
    ],
    "lap_times": [
        ("raceId", "TEXT"),
        ("driverId", "TEXT"),
        ("lap", "TEXT"),
        ("position", "TEXT"),
        ("time", "TEXT"),
        ("milliseconds", "TEXT"),
        ("source", "TEXT"),
    ],
    "pit_stops": [
        ("raceId", "TEXT"),
        ("driverId", "TEXT"),
        ("stop", "TEXT"),
        ("lap", "TEXT"),
        ("time", "TEXT"),
        ("duration", "TEXT"),
        ("milliseconds", "TEXT"),
        ("source", "TEXT"),
    ],
    "driver_standings": [
        ("driverStandingsId", "TEXT PRIMARY KEY"),
        ("raceId", "TEXT"),
        ("driverId", "TEXT"),
        ("points", "TEXT"),
        ("position", "TEXT"),
        ("positionText", "TEXT"),
        ("wins", "TEXT"),
        ("source", "TEXT"),
    ],
    "constructor_standings": [
        ("constructorStandingsId", "TEXT PRIMARY KEY"),
        ("raceId", "TEXT"),
        ("constructorId", "TEXT"),
        ("points", "TEXT"),
        ("position", "TEXT"),
        ("positionText", "TEXT"),
        ("wins", "TEXT"),
        ("source", "TEXT"),
    ],
}


def generate_create_table_sql(table_name: str, columns: list) -> str:
    """Generate CREATE TABLE statement from column definitions."""
    column_defs = ",\n    ".join([f'"{col}" {dtype}' for col, dtype in columns])
    return f"""
    CREATE TABLE IF NOT EXISTS {BRONZE_SCHEMA}.{table_name} (
        {column_defs}
    );
    """


def get_all_bronze_create_statements() -> str:
    """Generate all CREATE TABLE statements for bronze schema."""
    statements = [CREATE_SCHEMAS]
    for table_name, columns in BRONZE_TABLES.items():
        statements.append(generate_create_table_sql(table_name, columns))
    return "\n".join(statements)


if __name__ == "__main__":
    print(get_all_bronze_create_statements())
