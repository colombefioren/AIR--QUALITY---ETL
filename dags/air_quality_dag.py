import logging
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from src.dag.tasks import (
    validate_settings,
    extract_historical,
    extract_forecast,
    extract_today_hourly,
    prepare_dimensions,
    transform_facts,
    save_postgres,
)

logger = logging.getLogger(__name__)

default_args = {
    "owner": "coco_data_engineering",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=2),
    "email_on_failure": False,
}

CITY_CSV = Path("data/star_schema/dim_city.csv")

with DAG(
    dag_id="air_quality_madagascar_etl",
    default_args=default_args,
    description="Madagascar Air Quality ETL - Visual Crossing to CSV to Power BI",
    schedule="0 6 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["air_quality", "madagascar", "etl", "visual_crossing"],
) as dag:

    validate = PythonOperator(
        task_id="validate_settings",
        python_callable=validate_settings,
    )

    if CITY_CSV.exists():
        cities = pd.read_csv(CITY_CSV)["city_name"].tolist()
    else:
        cities = []
        logger.warning("City CSV not found at %s — no extraction tasks created", CITY_CSV)

    extract_historical_tasks = [
        PythonOperator(
            task_id=f"extract_historical_{city}",
            python_callable=extract_historical,
            op_kwargs={"city_name": city},
        )
        for city in cities
    ]

    extract_forecast_tasks = [
        PythonOperator(
            task_id=f"extract_forecast_{city}",
            python_callable=extract_forecast,
            op_kwargs={"city_name": city},
        )
        for city in cities
    ]

    extract_hourly_tasks = [
        PythonOperator(
            task_id=f"extract_hourly_{city}",
            python_callable=extract_today_hourly,
            op_kwargs={"city_name": city},
        )
        for city in cities
    ]

    prepare = PythonOperator(
        task_id="prepare_dimensions",
        python_callable=prepare_dimensions,
    )

    transform = PythonOperator(
        task_id="transform_facts",
        python_callable=transform_facts,
    )

    pg_load = PythonOperator(
        task_id="save_postgres",
        python_callable=save_postgres,
    )

all_extractors = []

if extract_historical_tasks:
    all_extractors.extend(extract_historical_tasks)
if extract_forecast_tasks:
    all_extractors.extend(extract_forecast_tasks)
if extract_hourly_tasks:
    all_extractors.extend(extract_hourly_tasks)

if all_extractors:
    validate >> all_extractors >> prepare
else:
    validate >> prepare

prepare >> transform >> pg_load
