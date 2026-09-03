"""F1 race weekend pipeline: ingest -> normalize -> bronze load -> quality -> dbt."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT = "/opt/airflow/project"

DBT_ENV = {
    "POSTGRES_HOST": "postgres",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "f1_warehouse",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres_password",
    "HOME": "/home/airflow",
    "PATH": "/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin",
}

KAGGLE_ENV = {
    "KAGGLE_API_TOKEN": "{{ conn.kaggle_default.password }}",
    "KAGGLE_DATASET": "binayas/f1-dataset",
    "HOME": "/home/airflow",
    "PATH": "/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin",
}

default_args = {
    "owner": "f1_analytics",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="f1_race_weekend_pipeline",
    description="Full F1 pipeline: ingest, normalize, bronze load, quality checks, dbt build",
    schedule="0 22 * * 0",
    start_date=datetime(2026, 3, 1),
    catchup=False,
    default_args=default_args,
    tags=["f1"],
) as dag:
    ingest = BashOperator(
        task_id="ingest_api_data",
        bash_command=f"cd {PROJECT} && python src/ingest/ingest_main.py",
    )

    normalize = BashOperator(
        task_id="normalize_bronze_csvs",
        bash_command=f"cd {PROJECT} && python src/normalize/normalize.py",
    )

    bronze_load = BashOperator(
        task_id="load_bronze_to_postgres",
        bash_command=f"cd {PROJECT} && python src/warehouse/loader.py",
    )

    quality_checks = BashOperator(
        task_id="bronze_quality_checks",
        bash_command=f"cd {PROJECT} && python src/warehouse/quality_checks.py",
    )

    dbt_build = BashOperator(
        task_id="dbt_build_silver_marts",
        bash_command=f"cd {PROJECT}/dbt && dbt build --profiles-dir . --target dev",
        env=DBT_ENV,
    )

    upload_kaggle = BashOperator(
        task_id="upload_kaggle",
        bash_command=f"cd {PROJECT} && python src/upload_kaggle.py",
        env=KAGGLE_ENV,
    )

    ingest >> normalize >> bronze_load >> quality_checks >> dbt_build >> upload_kaggle
