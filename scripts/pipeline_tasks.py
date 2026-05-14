import sys
import argparse
import mlflow
from backend.data.pipeline import DataPipeline
from backend.data.ingestion.job_fetcher import JSearchFetcher
from backend.data.ingestion.s3_storage import S3StorageProvider
from backend.models.recommender.job_recommender import JobRecommender
from backend.data.repository.database_repository import SQLiteRepository
from backend.config.settings import settings
import datetime
import json

def fetch_and_sync():
    """Fetches jobs from API, pushes to S3, and syncs to SQLite."""
    print("--- Task: Fetch and Sync Started ---")
    
    # 1. Fetch from API
    fetcher = JSearchFetcher()
    jobs = fetcher.fetch_jobs()
    print(f"Fetched {len(jobs)} jobs from API.")
    
    # 2. Push to S3
    storage = S3StorageProvider()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_key = f"raw/jobs_{timestamp}.json"
    
    # Wrap in expected structure for pipeline
    data_to_upload = {"data": jobs}
    storage.upload_json(settings.aws.raw_bucket, file_key, data_to_upload)
    print(f"Uploaded raw data to S3: {file_key}")
    
    # 3. Sync S3 to SQLite
    pipeline = DataPipeline()
    pipeline.sync_from_s3()
    print("--- Task: Fetch and Sync Completed ---")

def train():
    """Trains the model and logs to MLflow."""
    print("--- Task: Model Training Started ---")
    repo = SQLiteRepository()
    recommender = JobRecommender(repository=repo)
    recommender.train()
    print("--- Task: Model Training Completed ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill-Ex Pipeline Tasks")
    parser.add_argument("task", choices=["fetch-and-sync", "train"], help="Task to execute")
    
    args = parser.parse_args()
    
    if args.task == "fetch-and-sync":
        fetch_and_sync()
    elif args.task == "train":
        train()
