from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from dags.tasks import (
    extract_hourly_task,
    load_to_warehouse,
    rebuild_clean_task,
    validate_settings,
)

default_args = {
    "owner": "air-quality-team",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="air_quality_pipeline",
    default_args=default_args,
    description="Collect hourly AQI data, build star schema, load to Postgres",
    schedule="0 * * * *",
    start_date=datetime(2026, 4, 1),
    catchup=False,
    tags=["air-quality", "aqi"],
) as dag:
    t_validate = PythonOperator(
        task_id="validate_settings",
        python_callable=validate_settings,
    )
    t_extract = PythonOperator(
        task_id="extract_hourly",
        python_callable=extract_hourly_task,
    )
    t_rebuild = PythonOperator(
        task_id="rebuild_clean",
        python_callable=rebuild_clean_task,
    )
    t_load = PythonOperator(
        task_id="load_to_warehouse",
        python_callable=load_to_warehouse,
    )

    t_validate >> t_extract >> t_rebuild >> t_load
