import sys
import os
import datetime

# Add the project root to sys.path to allow importing from shared
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.data.pipeline import DataPipeline
from shared.data.ingestion.job_fetcher import JSearchFetcher
from shared.data.ingestion.s3_storage import S3StorageProvider
from shared.config.settings import settings

def run_ingestion():
    """Fetches jobs from API, pushes to S3, and syncs to SQLite."""
    print("INFO: --- Microservice: Ingestion Started ---")
    
    try:
        # 1. Fetch from API
        fetcher = JSearchFetcher()
        print("INFO: Fetching jobs from API...")
        jobs = fetcher.fetch_jobs()
        print(f"INFO: Fetched {len(jobs)} jobs from API.")
        
        # 2. Push to S3
        storage = S3StorageProvider()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_key = f"raw/jobs_{timestamp}.json"
        
        data_to_upload = {"data": jobs}
        print(f"INFO: Uploading raw jobs data to S3: {file_key}")
        storage.upload_json(settings.aws.raw_bucket, file_key, data_to_upload)
        print(f"INFO: Uploaded raw data to S3: {file_key}")
        
        # 3. Sync S3 to SQLite
        pipeline = DataPipeline()
        print("INFO: Synchronizing S3 raw data to SQLite database...")
        pipeline.sync_from_s3()
        print("INFO: --- Microservice: Ingestion Completed ---")
    except Exception as e:
        print(f"ERROR: Ingestion failed: {str(e)}")
        raise e

if __name__ == "__main__":
    run_ingestion()
