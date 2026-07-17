from airflow import DAG
from airflow.operators.python import PythonOperator

from dags.tasks import (
    extract_backfill_task,
    load_to_warehouse,
    prepare_dimensions,
    rebuild_clean_task,
    validate_settings,
)

with DAG(
    dag_id="backfill",
    description="One-time backfill: 12 months of historical AQI data",
    schedule="@once",
    catchup=False,
    tags=["air-quality", "backfill"],
) as dag:
    t_validate = PythonOperator(
        task_id="validate_settings",
        python_callable=validate_settings,
    )
    t_backfill = PythonOperator(
        task_id="extract_backfill",
        python_callable=extract_backfill_task,
    )
    t_rebuild = PythonOperator(
        task_id="rebuild_clean",
        python_callable=rebuild_clean_task,
    )
    t_dims = PythonOperator(
        task_id="prepare_dimensions",
        python_callable=prepare_dimensions,
    )
    t_load = PythonOperator(
        task_id="load_to_warehouse",
        python_callable=load_to_warehouse,
    )

    t_validate >> t_backfill >> t_rebuild >> t_dims >> t_load
