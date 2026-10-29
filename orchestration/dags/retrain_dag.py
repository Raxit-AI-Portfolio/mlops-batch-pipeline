from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/project"
ENV = "PROFILE=local"

with DAG(
    dag_id="retrain_dag",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["mlcicd", "training"],
) as dag:
    train = BashOperator(
        task_id="train",
        bash_command=f"cd {PROJECT_DIR} && {ENV} python -m mlcicd.training.train",
    )

    evaluate = BashOperator(
        task_id="evaluate",
        bash_command=f"cd {PROJECT_DIR} && {ENV} python -m mlcicd.training.evaluate",
    )

    register = BashOperator(
        task_id="register",
        bash_command=f"cd {PROJECT_DIR} && {ENV} python -m mlcicd.registry.register",
    )

    train >> evaluate >> register
