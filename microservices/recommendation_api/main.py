from fastapi import FastAPI, Request, Response, Query, HTTPException, UploadFile, File, Depends, Cookie
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any
import pdfplumber
import io
from dotenv import load_dotenv, find_dotenv
from shared.data.repository.database_repository import SQLiteRepository
from shared.data.pipeline import DataPipeline
from .engine import JobRecommender
from shared.models.trend.trend_analyzer import TrendAnalyzer
from shared.utils.extractors import RegexSkillExtractor
from shared.utils.pii_masker import PIIMasker
from shared.config.settings import settings

app = FastAPI(title="Skill-Ex AI Core API")

# Mount static files and templates (as per original main.py)
# Mount static files and templates
app.mount("/static", StaticFiles(directory="microservices/recommendation_api/static"), name="static")
templates = Jinja2Templates(directory="microservices/recommendation_api/templates")

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
    # Auto-train if artifacts are missing
    if not recommender.load_artifacts():
        print("Model artifacts not found. Training model...")
        recommender.train()
    return recommender

def get_trend_analyzer():
    return TrendAnalyzer()

def get_extractor():
    return RegexSkillExtractor()

# --- Cookie Consent Logic (from original main.py) ---

async def verify_consent(consent_cookie: Optional[str] = Cookie(None, alias="user_consent")):
    if consent_cookie != "granted":
        raise HTTPException(
            status_code=403, 
            detail="Consent required. Please accept cookies to use this feature."
        )
    return True

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    consent = request.cookies.get("user_consent")
    show_banner = True if not consent else False
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"message": "viola!", "show_banner": show_banner}
    )

@app.post("/set-consent")
async def set_cookie_consent(response: Response, choice: str = Query(...)):
    if choice == "accept":
        response.set_cookie(
            key="user_consent",
            value="granted",
            max_age=31536000,
            httponly=True,
            samesite="lax"
        )
        return {"status": "accepted"}
    response.delete_cookie(key="user_consent")
    return {"status": "rejected"}

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

        recommendations, gaps = recommender.recommend(", ".join(masked_skills))
        
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