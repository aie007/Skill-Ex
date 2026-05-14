from fastapi import FastAPI, Request, Response, Query, HTTPException, UploadFile, File, Depends
from typing import Optional, List, Dict, Any
import pdfplumber
import io
import os
from dotenv import load_dotenv, find_dotenv
from shared.data.repository.database_repository import SQLiteRepository
from shared.data.pipeline import DataPipeline
from .engine import JobRecommender
from shared.models.trend.trend_analyzer import TrendAnalyzer
from shared.utils.extractors import RegexSkillExtractor
from shared.utils.pii_masker import PIIMasker
from shared.config.settings import settings

app = FastAPI(title="Skill-Ex AI Core API")

load_dotenv(dotenv_path=find_dotenv())

# Dependency Injection
def get_repository():
    repo = SQLiteRepository()
    repo.initialize() # Ensure tables exist first
    
    db_path = settings.database.name
    import os
    
    # Check if empty
    try:
        is_empty = repo.get_all_jobs().empty
    except Exception:
        is_empty = True
        
    if not os.path.exists(db_path) or is_empty:
        pipeline = DataPipeline(repo)
        # 1. Try to restore from DB backup first
        restored = pipeline.restore_db_from_s3()
        
        # 2. If restore failed and it's still empty, sync from raw JSONs
        if not restored and is_empty:
            pipeline.sync_from_s3()
            
    return repo

def get_recommender(repo=Depends(get_repository)):
    recommender = JobRecommender(repo)
    
    # 1. Try to load local artifacts first
    if not recommender.load_artifacts():
        print("Local model artifacts not found. Attempting to sync from S3 Model Registry...")
        
        # 2. Try to sync from S3
        if not recommender.sync_model_from_s3():
            print("Model registry empty or unreachable. Training fresh model...")
            # 3. Fallback to local training if registry is empty
            recommender.train()
            
    return recommender

def get_trend_analyzer():
    return TrendAnalyzer()

def get_extractor():
    return RegexSkillExtractor()

@app.get("/")
async def home():
    return {"status": "online", "service": "Skill-Ex AI Core API"}

# --- Consolidated Core API Endpoints ---

@app.post("/recommend")
async def recommend_from_pdf(
    file: UploadFile = File(...), 
    recommender=Depends(get_recommender),
    extractor=Depends(get_extractor)
):
    try:
        content = await file.read()
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            resume_text = " ".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        
        print("line 1")
        # Apply PII Masking
        masked_resume = PIIMasker.mask(resume_text)
        
        masked_skills = extractor.extract(masked_resume)
        if not masked_skills:
            return {
                "masked_resume": masked_resume,
                "extracted_skills": [], 
                "recommendations": [], 
                "message": "No recognized skills found"
            }
        print("line2")
        print(masked_skills)
        recommendations, gaps = recommender.recommend(", ".join(masked_skills))
        print("i got the recommendations")
        print(recommendations)
        return {
            "masked_resume": masked_resume,
            "extracted_skills": masked_skills, 
            "recommendations": recommendations,
            "skill_gaps": gaps
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trends")
async def get_market_trends(
    freq: str = 'W', 
    repo=Depends(get_repository),
    analyzer=Depends(get_trend_analyzer)
):
    try:
        df = repo.get_trend_data()
        if df.empty: return {}
        trends = analyzer.get_timeseries_trends(df, freq=freq)
        return trends.reset_index().to_dict(orient="list")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend calculation error: {str(e)}")

@app.get("/momentum")
async def get_skill_momentum(
    window: int = 3, 
    repo=Depends(get_repository),
    analyzer=Depends(get_trend_analyzer)
):
    try:
        df = repo.get_trend_data()
        if df.empty: return {}
        trends = analyzer.get_timeseries_trends(df)
        momentum = analyzer.calculate_momentum(trends, window=window)
        return momentum.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Momentum calculation error: {str(e)}")