# Formula 1 Data Engineering Pipeline

End-to-end data pipeline for Formula 1 data: ingest raw data from a historical Ergast CSV archive (1950–2024) and the Jolpica F1 API (2025+), normalize both into unified bronze CSVs, then load into PostgreSQL with Pandas.

## Data Sources

| Source | Period | Type | Update Frequency |
| ------ | ------ | ---- | ---------------- |
| [Ergast CSV archive](https://raceoptidatapublicfiles.blob.core.windows.net/ergast2024/ergast_2024.zip) | 1950–2024 | CSV (14 tables in a zip) | One-time download |
| [Jolpica F1 API](https://api.jolpi.ca/ergast/f1) | 2025–current | JSON (live API) | New year + after each race |

The CSV archive covers everything through 2024 (full results, lap times, pit stops, sprint data from 2021). From 2025 onward the API is the source of truth. Both are normalized into a single set of bronze tables.

## Pipeline Stages

### 1. Ingest (`src/ingest_main.py`)

Orchestrator entry point, runs each stage only when needed (idempotent, resumable):

- **Historical CSVs** — download from the blob zip once; skipped when already complete. Completeness is verified by content: all 14 tables present *and* `races.csv` reaches at least 2024.
- **Global endpoints** (`seasons`, `status`) — always re-fetched at the start of each run (tiny, keeps the year/status lists current through the new season). All endpoints are paginated (the API default page size is 30; we loop until `MRData.total`).
- **Past API years** — fetched once; skipped on later runs unless `--force`.
- **Current year** — full season endpoints (circuits, drivers, constructors, races) plus **incremental round updates**: after each race weekend the latest round is refreshed and any missing/empty rounds are fetched. Placeholders for un-run rounds are kept so the season schedule is available in advance.

CLI:

```
python src/ingest_main.py            # full pipeline
python src/ingest_main.py --year 2025  # single year
python src/ingest_main.py --force      # re-fetch everything
```

Raw data lands in `data/raw/` (CSVs) and `data/raw/jolpica/{year}/` (API JSON).

### 2. Normalize (`src/normalize.py`)

Merges historical CSVs and API JSON into unified **bronze** tables in `data/bronze/`:

- 13 tables: `seasons, status, circuits, drivers, constructors, races, results, qualifying, sprint_results, lap_times, pit_stops, driver_standings, constructor_standings`.
- Historical rows keep their original integer IDs; API rows resolve references (drivers/constructors/circuits/status via `Ref`/slug, races via `year+round`) against the historical tables and **allocate new integer IDs** for anything new (e.g. new drivers, 2026 Madring circuit, Audi/Cadillac).
- A trailing `source` column marks each row as `historical` or `api`.
- Missing API fields (e.g. `fastestLapSpeed`, lap/pit-stop milliseconds) are computed or filled with `NULL`.
- Pure function of `data/raw` — deterministic and idempotent; run after any ingest.

CLI: `python src/normalize.py`

### 3. Load (planned)

Bronze → PostgreSQL using Pandas (`src/ingest_to_postgres.py`). DB credentials come from `env.py` (gitignored).

## Data Flow

```
Ergast CSV zip ─┐
                 ├─► data/raw ──► src/normalize.py ──► data/bronze/*.csv ──► PostgreSQL
Jolpica API ────┘
```

## Tests

```
python -m pytest
```

Tests cover core logic only: lap merge, API backoff/retry, incremental round updates, pagination, ingest completeness, and normalization (time parsing + end-to-end ID mapping).

## Layout

```
src/                ingest + normalize modules
tests/              pytest suite
data/raw/           downloaded historical CSVs + Jolpica API JSON (gitignored)
data/bronze/        normalized unified tables (gitignored)
```
