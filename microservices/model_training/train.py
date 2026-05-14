import sys
import os

# Add the project root to sys.path to allow importing from shared
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.data_layer_temp.repository.database_repository import SQLiteRepository
from backend.models.recommender.job_recommender import JobRecommender

def run_training():
    """Trains the model and logs to MLflow."""
    print("--- Microservice: Model Training Started ---")
    repo = SQLiteRepository()
    recommender = JobRecommender(repository=repo)
    recommender.train()
    print("--- Microservice: Model Training Completed ---")

if __name__ == "__main__":
    run_training()
