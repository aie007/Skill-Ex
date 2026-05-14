import sys
import os
import datetime

# Ensure /app and /app/ml are in the search path
# /app maps to the 'microservices' directory in our docker-compose volume mapping
sys.path.append('/app')
sys.path.append('/app/ml')

try:
    from shared.data.repository.database_repository import SQLiteRepository
    from recommendation_api.engine import JobRecommender
    from shared.data.ingestion.s3_storage import S3StorageProvider
    from shared.config.settings import settings
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)

def run_training():
    """
    Independent Model Training Service.
    - Trains the recommendation engine.
    - Logs metrics/parameters to MLflow.
    - Pushes the resulting model artifact to the S3 Model Registry (amzn-s3-models-bucket).
    """
    print("--- Model Training Service: Pipeline Started ---")
    
    try:
        # 1. Initialize Repository & Sync Data
        # Ensure the DB exists by trying to restore from S3 or syncing from raw data
        from shared.data.pipeline import DataPipeline
        repo = SQLiteRepository()
        pipeline = DataPipeline(repo)
        
        db_path = settings.database.name
        # Check if DB is missing or empty (table check happens in repo)
        try:
            is_empty = repo.get_all_jobs().empty
        except Exception:
            is_empty = True

        if not os.path.exists(db_path) or is_empty:
            print("Database missing or empty. Attempting to restore from S3 Model Registry...")
            if not pipeline.restore_db_from_s3():
                print("No DB backup found. Rebuilding from raw JSON logs...")
                pipeline.sync_from_s3()

        artifact_name = "model_artifacts.pkl"
        
        # 2. Train the model
        # Capture the performance metric (Average Similarity)
        recommender = JobRecommender(repository=repo, artifact_path=artifact_name)
        performance_score = recommender.train()
        
        # 3. Model Registry & Promotion Logic
        if os.path.exists(artifact_name):
            storage = S3StorageProvider()
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            bucket = settings.aws.models_bucket
            remote_key = f"models/recommender_{timestamp}.pkl"
            latest_key = "models/latest_recommender.pkl"
            
            # --- Always Archive ---
            print(f"Archiving versioned model: {remote_key}")
            storage.backup_file(bucket, artifact_name, remote_key)
            
            # --- Conditional Promotion ---
            # Use threshold from config.yaml (ml.skill_extraction_threshold)
            # Accessing it via settings (assuming it's mapped in settings.py)
            threshold = getattr(settings.ml, 'skill_extraction_threshold', 0.5) if hasattr(settings, 'ml') else 0.5
            
            if performance_score >= threshold:
                print(f"Promotion Approved: Score {performance_score:.4f} >= Threshold {threshold}")
                print(f"Updating latest model pointer: {latest_key}")
                storage.backup_file(bucket, artifact_name, latest_key)
            else:
                print(f"Promotion Rejected: Score {performance_score:.4f} < Threshold {threshold}")
                print("Latest model in S3 remains unchanged.")
            
            print("--- Model Training Service: Pipeline Completed ---")
        else:
            print(f"Error: Trained artifact '{artifact_name}' not found.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Failure in training service: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_training()
