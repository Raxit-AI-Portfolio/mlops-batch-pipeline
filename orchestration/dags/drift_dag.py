from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/project"
ENV = "PROFILE=local"

with DAG(
    dag_id="drift_dag",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["mlcicd", "monitoring"],
) as dag:
    check_drift = BashOperator(
        task_id="check_drift",
        bash_command=f"cd {PROJECT_DIR} && {ENV} python -m mlcicd.monitoring.drift",
    )
