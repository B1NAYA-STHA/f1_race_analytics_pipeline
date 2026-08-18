# F1 Analytics Implementation Plan

## 1. Project overview

This project builds an end-to-end Formula 1 analytics pipeline using Python, PostgreSQL, Apache Airflow, and Kaggle publishing. The ingestion and normalization foundation is already in place for historical Ergast CSV data and newest Jolpica API records. The next phase is to operationalize the pipeline for scheduled orchestration, warehouse loading, validation, and automatic Kaggle dataset publishing after each race weekend.

## 2. Current repo state

The repository already includes:

- historical F1 data ingestion from Ergast CSV archive
- current-season ingestion from Jolpica API
- normalization logic that merges raw input into bronze CSV tables
- PostgreSQL configuration in Docker Compose
- Python dependencies for ETL tasks

Key current code entry points:

- [src/ingest_main.py](src/ingest_main.py): orchestration entry for ingesting historical and current season data
- [src/normalize.py](src/normalize.py): merges raw and API data into unified bronze tables
- [docker-compose.yml](docker-compose.yml): local PostgreSQL service
- [requirements.txt](requirements.txt): project dependencies

## 3. Target architecture

### Data flow

```text
Ergast CSV + Jolpica API
        |
        v
Ingestion jobs
        |
        v
Bronze normalized CSVs
        |
        v
Validation + quality checks
        |
        v
PostgreSQL warehouse
        |
        v
Analytics marts / BI / SQL queries
        |
        v
Kaggle dataset snapshot after each race weekend
```

### Recommended stack

- Orchestration: Apache Airflow
- Data warehouse: PostgreSQL 15
- ETL processing: Python, Pandas, SQLAlchemy, psycopg2
- Transformation layer: dbt (recommended)
- Validation: Pandera or Great Expectations
- Dataset publishing: Kaggle API
- Local runtime: Docker Compose

## 4. Pipeline stages

### Stage 1: Ingestion

Goal: continuously fetch the latest Formula 1 data.

Responsibilities:

- fetch historical Ergast CSV archive when needed
- fetch global endpoints such as seasons and status
- fetch API data for all years as required
- fetch current season incrementally after each race weekend
- persist raw data under data/raw and data/raw/jolpica

Current implementation already supports this pattern via the ingestion entry point in [src/ingest_main.py](src/ingest_main.py).

### Stage 2: Normalization

Goal: unify raw historical and API data into a standard bronze model.

Responsibilities:

- merge historical and API data into consistent table structures
- map IDs consistently across entities
- add source tracking for rows from historical vs API origin
- compute missing values where needed
- write normalized tables to data/bronze

This is already being done by [src/normalize.py](src/normalize.py).

### Stage 3: Warehouse loading

Goal: load normalized bronze data into PostgreSQL for analytics use.

Responsibilities:

- create warehouse schema
- create typed tables in PostgreSQL
- load CSV files into staging/bronze tables
- enforce primary keys and key relationships
- perform deduplication and validation

### Stage 4: Curated analytics layer

Goal: transform bronze data into cleaned, query-ready tables.

Responsibilities:

- create silver tables with standardized types and business logic
- create analytics marts for drivers, races, constructors, lap times, results, standings, pit stops
- join dimensions and facts into star schemas
- optimize for BI/reporting queries

### Stage 5: Post-race publishing to Kaggle

Goal: publish a refreshed, complete dataset after each race weekend.

Responsibilities:

- detect a newly completed race weekend
- export the latest dataset snapshot
- generate metadata and README
- upload version using Kaggle API
- store dataset version notes like "Round 12 update"

## 5. Recommended warehouse design

Use layered schema design:

- raw_staging: raw source tables or imported staging data
- bronze: normalized tables from pipeline output
- silver: cleaned data with typed columns and deduplication
- marts: analytics-ready datasets used for dashboards and reporting

Suggested dimensional tables:

- dim_drivers
- dim_constructors
- dim_circuits
- dim_races
- dim_seasons

Suggested fact tables:

- fact_results
- fact_lap_times
- fact_pit_stops
- fact_driver_standings
- fact_constructor_standings

This structure makes the analytics layer clearer and more maintainable than querying bronze data directly.

## 6. Airflow orchestration plan

### DAG strategy

Create at least two DAGs:

#### 1. Daily ETL DAG

Runs on a schedule such as every 6 hours or once per day.

Tasks:

1. check if ingestion is needed
2. run historical ingestion if missing
3. run current-season data fetch
4. normalize all bronze tables
5. validate bronze output
6. load to PostgreSQL
7. run warehouse transformations
8. trigger data quality checks
9. send alerts if failures occur

#### 2. Race-weekend publication DAG

Runs after a race is completed or when a new round appears.

Tasks:

1. detect new round in current season
2. fetch latest round data
3. normalize fresh data
4. validate freshness and integrity
5. load updated data to warehouse
6. generate Kaggle export package
7. upload to Kaggle dataset
8. notify team of successful publication

### Airflow best practices

- keep each stage in a separate task
- use retries for API requests and uploads
- store secrets in Airflow connections or environment variables
- make ingestion and normalization idempotent
- log success/failure metadata for each run
- add alerting via email, Slack, or Teams

## 7. Data validation plan

Add validation before any warehouse load and Kaggle upload.

### Validate at three levels

1. Raw source validation
   - required JSON keys exist
   - no malformed data from API responses
   - current-season round completeness check

2. Bronze validation
   - all required columns are present
   - entity IDs are not null when expected
   - duplicate keys are detected
   - row counts match expectations

3. Warehouse validation
   - referential integrity
   - unique key constraints
   - null checks on critical fields
   - time/date parsing checks

Recommended tools:

- Pandera for DataFrame assertions
- Great Expectations for richer rule sets
- PostgreSQL constraints and NOT NULL checks

## 8. Kaggle publication process

### Goal

After each race weekend, upload a refreshed dataset snapshot using Kaggle without manual intervention.

### Recommended process

1. detect new completed round
2. export final dataset tables from bronze or silver
3. package them into a Kaggle-ready folder
4. write a dataset README with version notes
5. upload using Kaggle API
6. publish as a new version of the existing dataset

### Folder structure for Kaggle export

```text
data/
  kaggle/
    f1_dataset_snapshot_2026_round_12/
      README.md
      metadata.json
      circuits.csv
      drivers.csv
      constructors.csv
      races.csv
      results.csv
      lap_times.csv
      pit_stops.csv
      driver_standings.csv
      constructor_standings.csv
```

### Kaggle API setup

Store the following as environment variables or secure Airflow secrets:

- KAGGLE_USERNAME
- KAGGLE_KEY
- KAGGLE_DATASET_SLUG

Then run the Kaggle CLI or API to create a new dataset version.

## 9. Proposed implementation roadmap

### Phase 1: Warehouse foundation

- create PostgreSQL schema and init scripts
- build a loader script to import bronze CSVs into Postgres
- define core table types and constraints
- build a smoke test pipeline end-to-end

### Phase 2: Airflow setup

- add Airflow Docker Compose setup
- create DAGs for ingestion and transformation
- schedule ingestion and validation tasks
- add retry and alert logic

### Phase 3: Transformation layer

- create silver layer using typed staging tables
- build fact and dimension tables
- create SQL or dbt models for analytics
- validate queries with sample race data

### Phase 4: Kaggle publishing

- create export script for final dataset snapshot
- add metadata generation and README
- upload using Kaggle API
- verify published dataset version

### Phase 5: Analytics and reporting

- create dashboard-ready aggregations
- add performance metrics
- build a driver/team analytics view
- add notebook-based exploratory analysis

## 10. Operational best practices

- Use environment variables for credentials and config
- Keep raw, bronze, and publish outputs separate
- Make all ETL tasks incremental where possible
- Use schedule-aware DAG logic for current-season races
- Always validate before Kaggle upload
- Maintain a clear versioning strategy for dataset snapshots
- Log each race weekend run in a metadata table

## 11. Risks and mitigations

### Risk: API changes or missing race data
Mitigation: validate schema before loading and make the current-season ingestion incremental and retryable.

### Risk: dataset upload fails due to authentication or size issues
Mitigation: add a validation step, preflight checks, and alerting before upload.

### Risk: duplicative rows in bronze or warehouse tables
Mitigation: enforce unique keys and deduplicate on load.

### Risk: stale warehouse data
Mitigation: schedule daily checks and race-weekend validations with freshness thresholds.

## 12. Recommended final stack

The most robust final stack for this project is:

- Airflow for orchestration
- PostgreSQL for analytics warehouse
- Python + Pandas + SQLAlchemy + psycopg2 for ETL
- dbt for marts and transformations
- Pandera or Great Expectations for validation
- Kaggle API for auto-publishing race snapshot datasets
- Docker Compose for local deployment and reproducibility

## 13. Summary

The project is already well-positioned for the next phase. Ingestion and normalization are implemented and working. The next step is to build a warehouse layer, add Airflow DAGs, and create a post-race Kaggle publication workflow. This will turn the project from a solid data pipeline into a repeatable, production-oriented F1 analytics platform.

## 14. Immediate next steps

1. create PostgreSQL schema and loader script
2. create Airflow DAG files for daily pipeline and race-weekend processing
3. define validation rules for bronze and warehouse tables
4. add Kaggle export and upload module
5. implement first end-to-end run for a current season update
