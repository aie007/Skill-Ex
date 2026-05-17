from typing import List, Dict, Any
from shared.data.ingestion.s3_storage import S3StorageProvider
from shared.data.repository.database_repository import SQLiteRepository
from shared.utils.extractors import RegexSkillExtractor, ExperienceExtractor
from shared.config.settings import settings

class DataPipeline:
    def __init__(self, repo: SQLiteRepository = None):
        self.repo = repo or SQLiteRepository()
        self.storage = S3StorageProvider()
        self.skill_extractor = RegexSkillExtractor()
        self.exp_extractor = ExperienceExtractor()

    def restore_db_from_s3(self):
        """Attempts to download the DB backup from S3."""
        print("INFO: Attempting to restore DB from S3 backup...")
        try:
            backup_bucket = settings.aws.processed_bucket
            backup_key = "db_backups/job_market.db"
            self.storage.download_file(backup_bucket, backup_key, settings.database.name)
            print("INFO: DB restored successfully from S3.")
            return True
        except Exception as e:
            print(f"WARNING: No DB backup found or failed to download: {e}")
            return False

    def sync_from_s3(self):
        """Fetches all raw JSONs from S3, processes them, and saves to DB."""
        print("INFO: Starting sync from S3...")
        try:
            raw_bucket = settings.aws.raw_bucket
            keys = self.storage.list_objects(raw_bucket, prefix="raw/")
            
            if not keys:
                print("WARNING: No raw data found in S3.")
                return

            for key in keys:
                print(f"INFO: Processing {key}...")
                raw_data = self.storage.fetch_json(raw_bucket, key)
                
                # The structure might vary, but original code looked for 'data' key
                jobs_list = raw_data.get('data', []) if isinstance(raw_data, dict) else raw_data
                
                processed = []
                for job in jobs_list:
                    desc = job.get("job_description", "")
                    title = job.get("job_title", "")
                    
                    skills = self.skill_extractor.extract(desc)
                    exp_level = self.exp_extractor.extract(title, desc)
                    
                    processed.append({
                        "title": title,
                        "company": job.get("employer_name"),
                        "skills": skills,
                        "experience": exp_level,
                        "date": job.get("job_posted_at_datetime_utc"),
                        "source_id": job.get("job_id"),
                        "raw_ref": key
                    })
                
                self.repo.save_jobs(processed)
            print("INFO: Sync complete.")
        except Exception as e:
            print(f"ERROR: Failed to sync from S3: {e}")

