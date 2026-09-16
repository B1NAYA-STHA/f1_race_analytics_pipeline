# F1 Analytics

F1 Analytics is an end-to-end Formula 1 data platform. It collects historical and current-season data, normalizes it into a consistent model, loads it into PostgreSQL, transforms it with dbt, and exposes the results through a Streamlit analytics dashboard.

The project follows a medallion architecture:

```text
Ergast archive + Jolpica API
            |
            v
      data/raw/             Raw source files and API responses
            |
            v
      data/bronze/          Unified normalized CSV tables
            |
            v
      PostgreSQL bronze     Source-aligned warehouse tables
            |
            v
      dbt silver             Clean dimensions and facts
            |
            v
      dbt marts              Analytics-ready tables
            |
            v
      Streamlit dashboard + Kaggle dataset
```

## What The Project Provides

- Historical F1 data from the Ergast CSV archive, covering 1950-2024.
- Current-season data from the Jolpica F1 API.
- Resumable and idempotent ingestion with pagination, retries, and incremental race updates.
- Unified bronze tables combining historical and API data.
- PostgreSQL warehouse schemas for bronze, silver, and marts layers.
- dbt models for race results, standings, career records, circuit statistics, lap times, and pit stops.
- Airflow orchestration for scheduled pipeline execution.
- A Streamlit dashboard with season analytics and all-time exploration pages.
- Automated Kaggle dataset publishing after successful pipeline runs.

## Data Sources

| Source                                                                                            | Coverage     | Format      | Purpose                      |
| ------------------------------------------------------------------------------------------------- | ------------ | ----------- | ---------------------------- |
| [Ergast archive](https://raceoptidatapublicfiles.blob.core.windows.net/ergast2024/ergast_2024.zip) | 1950-2024    | CSV archive | Historical source            |
| [Jolpica F1 API](https://api.jolpi.ca/ergast/f1)                                                   | 2025-current | JSON API    | Current and incremental data |

## Kaggle Dataset

The normalized F1 dataset is published here:

[F1 Dataset on Kaggle](https://www.kaggle.com/datasets/binayas/f1-dataset)

The Airflow pipeline can upload a new Kaggle dataset version after dbt and quality checks complete successfully.

## Repository Structure

```text
.
|-- dags/                       Airflow DAGs
|-- data/
|   |-- raw/                    Downloaded archives and API responses
|   `-- bronze/                 Normalized bronze CSV tables
|-- dbt/
|   |-- models/silver/          Clean dimensions and facts
|   |-- models/marts/           Analytics-ready models
|   |-- profiles.yml            Local dbt profile
|   `-- dbt_project.yml
|-- src/
|   |-- ingest/                 Historical and Jolpica ingestion
|   |-- normalize/              Historical/API normalization
|   |-- warehouse/              PostgreSQL loading and quality checks
|   |-- app/                    Streamlit dashboard
|   `-- upload_kaggle.py        Kaggle publishing script
|-- tests/                      Python tests
|-- docker-compose.yml          PostgreSQL and Airflow services
|-- Dockerfile.airflow          Airflow image definition
|-- requirements.txt            Local Python dependencies
`-- requirements-airflow.txt   Airflow image dependencies
```

## Requirements

- Python 3.10 or newer
- Docker Desktop with Docker Compose
- Git
- PostgreSQL client tools are optional
- A Kaggle API token is required only for Kaggle publishing

## Configuration

Create a `.env` file in the repository root. Keep it local and never commit it.

Example local database settings:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=f1_warehouse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password
```

For Kaggle publishing, also configure:

```env
KAGGLE_API_TOKEN=KGAT_your_token
KAGGLE_DATASET=binayas/f1-dataset
```

Airflow receives its runtime environment from `docker-compose.yml`. The local Compose configuration uses the PostgreSQL service name `postgres` so containers can communicate over the Docker network.

## Local Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the local application and development dependencies:

```powershell
pip install -r requirements.txt
pip install -e ".[dev,dbt,app]"
```

Start PostgreSQL and Airflow:

```powershell
docker compose up -d --build
```

Useful local URLs:

- Streamlit: http://localhost:8501
- Airflow: http://localhost:8081
- PostgreSQL: `localhost:5432`

The default local Airflow credentials are configured in `docker-compose.yml`. Change them before exposing Airflow outside the local machine.

## Run The Pipeline Manually

Run ingestion:

```powershell
python src/ingest/ingest_main.py
```

Useful ingestion options:

```powershell
python src/ingest/ingest_main.py --year 2025
python src/ingest/ingest_main.py --force
```

Normalize the raw sources into bronze CSVs:

```powershell
python src/normalize/normalize.py
```

Load bronze data into PostgreSQL:

```powershell
python src/warehouse/loader.py
```

Run warehouse quality checks:

```powershell
python src/warehouse/quality_checks.py
```

Build the dbt silver and marts layers:

```powershell
cd dbt
dbt build --profiles-dir . --target dev
cd ..
```

Publish the normalized dataset to Kaggle:

```powershell
python src/upload_kaggle.py
```

## Airflow Scheduling

The DAG is defined in [dags/f1_race_weekend.py](dags/f1_race_weekend.py). It runs the complete workflow:

```text
ingest -> normalize -> bronze load -> quality checks -> dbt build -> Kaggle upload
```

The current schedule is Sunday at 22:00 UTC:

```text
0 22 * * 0
```

Airflow can also be triggered manually from the web UI. The scheduler must remain running for scheduled executions to occur.

## Streamlit Dashboard

Start the dashboard directly from the repository root:

```powershell
streamlit run src/app/main.py
```

The dashboard is organized into two navigation groups.

### Season

These pages respond to the global season selector:

- Overview: current leader, constructor leader, latest race, and race winners.
- Standings: driver and constructor championship tables.
- Progression: championship progression by round.
- Race Results: driver finishing-position heatmap.
- Qualifying: qualifying position versus race finish.
- Head-to-Head: teammate comparison.
- Lap Time: race-level pace and delta-to-best analysis.
- Pit Stops: race-level stop-duration and strategy analysis.

### All-time and Explorer

These pages are not restricted to the selected season:

- Career Records: all-time driver and constructor leaderboards.
- Circuit Explorer: world map, circuit records, latest race, and latest winner.

Dashboard query results are cached for 15 minutes. The sidebar refresh button clears the Streamlit cache when new warehouse data has been loaded.

## Testing And Validation

Run the Python test suite:

```powershell
python -m pytest
```

Run linting:

```powershell
ruff check src tests
```

Compile the application modules:

```powershell
python -m compileall -q src/app
```

The Streamlit pages can be smoke-tested with `streamlit.testing.v1.AppTest` after PostgreSQL and the marts tables are available.

## License And Data Notice

This project is an educational and engineering analytics project. Source data is obtained from the Ergast archive and Jolpica F1 API. Refer to those providers' terms and attribution requirements when redistributing or publishing derived datasets.
