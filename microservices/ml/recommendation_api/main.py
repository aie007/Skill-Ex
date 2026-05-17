from fastapi import FastAPI, Request, Response, Query, HTTPException, UploadFile, File, Depends
from typing import Optional, List, Dict, Any
import pdfplumber
import io
import os
import time
from dotenv import load_dotenv, find_dotenv
from shared.data.repository.database_repository import SQLiteRepository
from shared.data.pipeline import DataPipeline
from .engine import JobRecommender
from shared.models.trend.trend_analyzer import TrendAnalyzer
from shared.utils.extractors import RegexSkillExtractor
from shared.utils.pii_masker import PIIMasker
from shared.config.settings import settings

app = FastAPI(title="Skill-Ex AI Core API")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"INFO: Incoming request: {request.method} {request.url.path}")
    start_time = time.time()
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        print(f"INFO: Request {request.method} {request.url.path} completed in {duration:.4f}s with status code {response.status_code}")
        return response
    except Exception as e:
        duration = time.time() - start_time
        print(f"ERROR: Request {request.method} {request.url.path} failed after {duration:.4f}s with error: {str(e)}")
        raise e

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
        print("WARNING: Local model artifacts not found. Attempting to sync from S3 Model Registry...")
        
        # 2. Try to sync from S3
        if not recommender.sync_model_from_s3():
            print("WARNING: Model registry empty or unreachable. Training fresh model...")
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
        print(f"INFO: Received PDF file for recommendations. File size: {len(content)} bytes")
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            resume_text = " ".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        
        print("INFO: Extracted resume text from PDF successfully.")
        # Apply PII Masking
        masked_resume = PIIMasker.mask(resume_text)
        print("INFO: PII Masking completed successfully.")
        
        masked_skills = extractor.extract(masked_resume)
        if not masked_skills:
            print("WARNING: No recognized skills found in resume.")
            return {
                "masked_resume": masked_resume,
                "extracted_skills": [], 
                "recommendations": [], 
                "message": "No recognized skills found"
            }
        print(f"INFO: Extracted skills: {masked_skills}")
        recommendations, gaps = recommender.recommend(", ".join(masked_skills))
        print(f"INFO: Recommendations generated successfully. Found {len(recommendations)} matches.")
        return {
            "masked_resume": masked_resume,
            "extracted_skills": masked_skills, 
            "recommendations": recommendations,
            "skill_gaps": gaps
        }
    except Exception as e:
        print(f"ERROR: Error in recommendation endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trends")
async def get_market_trends(
    freq: str = 'W', 
    repo=Depends(get_repository),
    analyzer=Depends(get_trend_analyzer)
):
    try:
        print(f"INFO: Fetching market trends with frequency: {freq}")
        df = repo.get_trend_data()
        if df.empty:
            print("WARNING: Trend data repository is empty.")
            return {}
        trends = analyzer.get_timeseries_trends(df, freq=freq)
        print(f"INFO: Successfully calculated market trends. Frequency={freq}")
        return trends.reset_index().to_dict(orient="list")
    except Exception as e:
        print(f"ERROR: Trend calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trend calculation error: {str(e)}")

@app.get("/momentum")
async def get_skill_momentum(
    window: int = 3, 
    repo=Depends(get_repository),
    analyzer=Depends(get_trend_analyzer)
):
    try:
        print(f"INFO: Calculating skill momentum with window: {window}")
        df = repo.get_trend_data()
        if df.empty:
            print("WARNING: Trend data repository is empty for momentum calculation.")
            return {}
        trends = analyzer.get_timeseries_trends(df)
        momentum = analyzer.calculate_momentum(trends, window=window)
        print("INFO: Successfully calculated skill momentum.")
        return momentum.to_dict()
    except Exception as e:
        print(f"ERROR: Momentum calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Momentum calculation error: {str(e)}")