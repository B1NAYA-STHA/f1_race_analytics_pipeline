# F1 Analytics

An end-to-end Formula 1 data platform built to turn historical and live race data into reliable, queryable analytics.

F1 Analytics combines a resilient ingestion pipeline, a PostgreSQL warehouse, dbt transformations, scheduled orchestration, automated quality checks, Kaggle publishing, and an interactive Streamlit dashboard.

## Project Overview

The platform unifies two eras of Formula 1 data:

- Historical Ergast archive data covering 1950-2024
- Current and incremental data from the Jolpica F1 API

The result is a consistent analytical model that supports season analysis, career records, circuit exploration, lap-time analysis, and pit-stop analysis.

## Architecture

```text
                         +----------------------+
                         | Ergast CSV archive   |
                         +----------+-----------+
                                    |
                         +----------v-----------+
                         | Jolpica F1 API       |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Ingestion             |
                         | pagination, retries,  |
                         | incremental updates   |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Raw storage           |
                         | data/raw               |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Normalization         |
                         | ID resolution, merging |
                         | lineage tracking       |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Bronze                 |
                         | 13 unified CSV tables |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | PostgreSQL warehouse  |
                         | bronze / silver /     |
                         | marts schemas         |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | dbt                   |
                         | dimensions, facts,    |
                         | analytics marts       |
                         +----------+-----------+
                                    |
                 +------------------+------------------+
                 |                                     |
                 v                                     v
        Streamlit dashboard                    Kaggle dataset
```

## Highlights

### Resilient ingestion

- Historical archive download with completeness checks
- Jolpica API pagination based on API-reported totals
- Retry and exponential backoff for rate limits and transient failures
- Incremental refresh of completed and newly available race rounds
- Idempotent and resumable pipeline behavior

### Medallion warehouse design

- **Bronze:** source-aligned normalized tables with data lineage
- **Silver:** typed dimensions and fact tables built with dbt
- **Marts:** analytics-ready models designed for dashboard queries

### Data quality

- Python unit tests for ingestion, pagination, retries, normalization, and incremental behavior
- dbt uniqueness, not-null, relationship, lineage, and integrity tests
- Bronze loading validation with table and row-count checks
- CI validation on pushes and pull requests

### Automation

GitHub Actions provides two operational paths:

- CI validation for tests, linting, compilation, and dbt parsing
- Scheduled pipeline execution for ingestion, warehouse loading, dbt builds, validation, and Kaggle publishing

The project also includes an Airflow DAG for local orchestration and production-style workflow demonstration.

## Dashboard

The Streamlit application is organized around two analytical perspectives.

### Season analytics

- Season overview with championship leaders and latest race context
- Driver and constructor standings
- Championship progression by round
- Race-results finishing-position heatmap
- Qualifying versus race performance
- Teammate head-to-head comparisons
- Race-level lap-time analysis
- Race-level pit-stop analysis

### All-time and exploration

- Driver and constructor career leaderboards
- World circuit map with selectable locations
- Circuit records for wins, podiums, and poles
- Latest race and winner for each circuit

The dashboard reads from the PostgreSQL `marts` schema and uses cached queries for responsive exploration.

## Warehouse Models

The warehouse contains source and analytical entities for:

- Seasons
- Circuits
- Drivers
- Constructors
- Races
- Race results
- Qualifying
- Sprint results
- Lap times
- Pit stops
- Driver standings
- Constructor standings

The dbt marts layer includes:

- `race_results_detail`
- `championship_standings`
- `driver_season_summary`
- `constructor_season_summary`
- `driver_career`
- `constructor_career`
- `circuit_stats`
- `qualifying_vs_race`
- `lap_time_analysis`
- `pit_stop_analysis`

## Project Scope

```text
13       bronze source tables
23       dbt models
226      dbt data tests
23       Python tests
631,000+ lap-time records
1950+    historical coverage
2025+    live API coverage
```

## Repository Structure

```text
.
|-- dags/                       Airflow orchestration
|-- dbt/
|   |-- models/silver/          Typed dimensions and facts
|   |-- models/marts/           Analytics-ready models
|   |-- tests/                  Singular dbt integrity tests
|   `-- dbt_project.yml
|-- src/
|   |-- ingest/                 Historical and API ingestion
|   |-- normalize/              Source normalization
|   |-- warehouse/              PostgreSQL loading and validation
|   |-- app/                    Streamlit dashboard
|   `-- upload_kaggle.py        Kaggle dataset publishing
|-- tests/                      Python test suite
|-- docker-compose.yml          Local PostgreSQL and Airflow services
|-- Dockerfile.airflow          Airflow runtime image
`-- pyproject.toml              Project and tool configuration
```

## Published Dataset

The normalized dataset is published on Kaggle:

[F1 Dataset on Kaggle](https://www.kaggle.com/datasets/binayas/f1-dataset)

## Data Sources

- [Ergast archive](https://raceoptidatapublicfiles.blob.core.windows.net/ergast2024/ergast_2024.zip)
- [Jolpica F1 API](https://api.jolpi.ca/ergast/f1)

## Why This Project

This project was designed as a practical data-engineering system rather than a one-off analysis. It demonstrates the complete path from unreliable external sources to trusted analytical products:

```text
source systems -> ingestion -> normalized data -> warehouse -> tested marts -> user-facing analytics
```

It also demonstrates the boundary between development and production concerns: Docker and Airflow support local orchestration, while hosted PostgreSQL and scheduled GitHub Actions support the deployed data flow.

## Data Notice

This is an educational and engineering analytics project. Source data is obtained from the Ergast archive and Jolpica F1 API. Refer to the respective providers' terms and attribution requirements when redistributing or publishing derived datasets.
