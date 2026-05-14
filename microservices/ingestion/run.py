import sys
import os
import datetime

# Add the project root to sys.path to allow importing from shared
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from ml.shared.data.pipeline import DataPipeline
from ml.shared.data.ingestion.job_fetcher import JSearchFetcher
from ml.shared.data.ingestion.s3_storage import S3StorageProvider
from ml.shared.config.settings import settings

def run_ingestion():
    """Fetches jobs from API, pushes to S3, and syncs to SQLite."""
    print("--- Microservice: Ingestion Started ---")
    
    # 1. Fetch from API
    fetcher = JSearchFetcher()
    jobs = fetcher.fetch_jobs()
    print(f"Fetched {len(jobs)} jobs from API.")
    
    # 2. Push to S3
    storage = S3StorageProvider()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_key = f"raw/jobs_{timestamp}.json"
    
    data_to_upload = {"data": jobs}
    storage.upload_json(settings.aws.raw_bucket, file_key, data_to_upload)
    print(f"Uploaded raw data to S3: {file_key}")
    
    # 3. Sync S3 to SQLite
    pipeline = DataPipeline()
    pipeline.sync_from_s3()
    print("--- Microservice: Ingestion Completed ---")

if __name__ == "__main__":
    run_ingestion()
