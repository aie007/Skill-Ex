from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from datetime import datetime, timedelta
import os

# Default arguments for the DAG
default_args = {
    'owner': 'skill-ex-admin',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'weekly_mlops_pipeline',
    default_args=default_args,
    description='Weekly Fetch, Sync, and Train Pipeline for Skill-Ex',
    schedule='@weekly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['mlops', 'skillex'],
) as dag:

    # Task 1: Fetch from API and Sync to S3/SQLite
    # We use dvc repro ingest to ensure DVC tracks the output
    fetch_data = BashOperator(
        task_id='fetch_and_sync_data',
        bash_command='export PYTHONPATH=$PYTHONPATH:. && ./venv/bin/dvc repro ingest',
    )

    # Task 2: Train the Recommender Model
    # We use dvc repro train to ensure MLflow logging and artifact tracking
    train_model = BashOperator(
        task_id='train_recommender_model',
        bash_command='export PYTHONPATH=$PYTHONPATH:. && ./venv/bin/dvc repro train',
    )

    # Task 3: Push Data to DVC Remote (S3)
    dvc_push = BashOperator(
        task_id='dvc_push_to_s3',
        bash_command='./venv/bin/dvc push',
    )

    # Set task dependencies
    fetch_data >> train_model >> dvc_push
