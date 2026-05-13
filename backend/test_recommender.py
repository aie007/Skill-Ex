import io
import pandas as pd
from unittest.mock import MagicMock, patch
from backend.models.recommender.job_recommender import JobRecommender
from backend.data.repository.database_repository import SQLiteRepository
from backend.utils.extractors import RegexSkillExtractor
from backend.utils.pii_masker import PIIMasker

def test_recommendation_logic():
    # 1. Setup Mock Repo
    repo = SQLiteRepository("backend/data/job_market.db")
    
    # 2. Setup Recommender
    recommender = JobRecommender(repo)
    if not recommender.load_artifacts():
        print("Model not trained, training now...")
        recommender.train()

    # 3. Test PII Masking
    sample_text = "My name is John Doe, I live in Bangalore. Skills: Python, SQL, Docker."
    masked = PIIMasker.mask(sample_text)
    print(f"Original: {sample_text}")
    print(f"Masked: {masked}")

    # 4. Test Recommendation
    extractor = RegexSkillExtractor()
    skills = extractor.extract(masked)
    print(f"Extracted Skills: {skills}")

    if skills:
        recs, gaps = recommender.recommend(", ".join(skills))
        print("\nTop Recommendations:")
        for r in recs:
            print(f"- {r['title']} at {r['company']} (Score: {r['match_score']})")
    else:
        print("No skills found.")

if __name__ == "__main__":
    test_recommendation_logic()
