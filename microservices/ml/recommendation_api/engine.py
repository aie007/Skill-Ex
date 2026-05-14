import os
import pickle
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import mlflow
import mlflow.sklearn
from shared.core.interfaces import IRecommender, IDataRepository
from shared.config.settings import settings

class JobRecommender(IRecommender):
    def __init__(self, repository: IDataRepository, artifact_path: str = "model_artifacts.pkl"):
        self.repository = repository
        self.artifact_path = artifact_path
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        self.matrix = None
        self.job_ids = None
        self.full_df = None

    def train(self):
        """Trains the model and logs to MLflow."""
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
        mlflow.set_tracking_uri(tracking_uri)
        
        with mlflow.start_run(run_name="Job_Recommender_Training"):
            df = self.repository.get_all_jobs()
            if df.empty:
                print("No data found for training.")
                return

            self.full_df = df
            train_df, test_df = train_test_split(df, test_size=0.20, random_state=42)
            
            self.job_ids = train_df['job_id'].tolist()
            self.matrix = self.vectorizer.fit_transform(train_df['skill_set'].fillna(''))
            
            # Validation
            test_vecs = self.vectorizer.transform(test_df['skill_set'].fillna(''))
            similarities = cosine_similarity(test_vecs, self.matrix)
            avg_sim = similarities.max(axis=1).mean()
            
            mlflow.log_param("vectorizer_type", "TF-IDF")
            mlflow.log_metric("avg_validation_similarity", round(float(avg_sim), 4))
            
            with open(self.artifact_path, "wb") as f:
                pickle.dump((self.matrix, self.job_ids, self.vectorizer), f)
            mlflow.log_artifact(self.artifact_path)
            
            print(f"Training complete. Avg Sim: {avg_sim:.4f}")
            return float(avg_sim)
        
        return 0.0

    def sync_model_from_s3(self):
        """Attempts to download the latest model from the S3 Model Registry."""
        try:
            from shared.data.ingestion.s3_storage import S3StorageProvider
            storage = S3StorageProvider()
            bucket = settings.aws.models_bucket
            latest_key = "models/latest_recommender.pkl"
            
            print(f"Checking for latest model in S3 registry: {bucket}/{latest_key}")
            storage.download_file(bucket, latest_key, self.artifact_path)
            print("Successfully downloaded latest model from S3.")
            return self.load_artifacts()
        except Exception as e:
            print(f"Could not sync model from S3: {str(e)}")
            return False

    def load_artifacts(self):
        if os.path.exists(self.artifact_path):
            with open(self.artifact_path, "rb") as f:
                self.matrix, self.job_ids, self.vectorizer = pickle.load(f)
            return True
        return False

    def recommend(self, user_skills: str, top_n: int = 5) -> Tuple[List[Dict[str, Any]], List[str]]:
        if self.matrix is None and not self.load_artifacts():
            raise ValueError("Model must be trained or artifacts loaded before calling recommend().")

        user_vec = self.vectorizer.transform([user_skills])
        sim_scores = cosine_similarity(user_vec, self.matrix).flatten()
        top_indices = sim_scores.argsort()[-top_n:][::-1]
        
        user_skill_set = set(user_skills.lower().replace(',', '').split())
        recommendations = []
        all_gap_skills = set()

        if self.full_df is None:
            self.full_df = self.repository.get_all_jobs()

        for idx in top_indices:
            job_id = self.job_ids[idx]
            job_data = self.full_df[self.full_df['job_id'] == job_id].iloc[0]
            
            job_skill_set = set(str(job_data['skill_set']).lower().split())
            missing_skills = job_skill_set - user_skill_set
            all_gap_skills.update(missing_skills)

            recommendations.append({
                "job_id": job_id,
                "title": job_data['title'],
                "company": job_data['company'],
                "match_score": round(float(sim_scores[idx]), 3),
                "missing_skills": list(missing_skills)
            })

        return recommendations, list(all_gap_skills)
