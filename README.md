# Skill-Ex: AI Career Radar

Skill-Ex is an MLOps-ready platform for skill extraction, job recommendation, and market trend analysis.

## Project Structure

```
backend/
├── main.py             # FastAPI application
├── core/               # Shared interfaces (SOLID)
├── data/               # Data Layer (SQLite, S3 Ingestion, Pipeline)
├── models/             # ML Engines (Recommender, Trend Analyzer)
├── config/             # Centralized Configuration (Settings, YAML)
├── utils/              # Shared Extractors (Regex-based)
└── app.py              # Streamlit Frontend
```

## Prerequisites

- Python 3.12+
- Virtual environment (`venv`)
- Amazon S3 bucket (for raw data)
- RapidAPI Key (for JSearch API)

## Setup

1. **Virtual Environment**:
   Ensure your virtual environment is active.
   ```bash
   source venv/bin/activate
   ```

2. **Environment Variables**:
   Create a `.env` file in the root directory with the following keys:
   ```env
   RAPIDAPI_KEY=your_key_here
   AWS_ACCESS_KEY_ID=your_id_here
   AWS_SECRET_ACCESS_KEY=your_secret_here
   ```

## Running the Backend

The backend is a FastAPI application. It automatically handles database initialization and syncs data from S3 if the local database is empty.

```bash
# From the project root
export PYTHONPATH=$PYTHONPATH:.
uvicorn backend.main:app --reload --port 8000
```

- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Web UI**: [http://localhost:8000/](http://localhost:8000/)

## Running the Frontend

The primary dashboard is built with Streamlit.

```bash
# From the project root
streamlit run backend/app.py
```

- **Dashboard**: [http://localhost:8501](http://localhost:8501)

## MLflow & Experiment Tracking

Experiment tracking and model versioning are handled via MLflow.

### Running the MLflow UI
To view training metrics, parameters, and model artifacts:
```bash
# From the project root
mlflow ui --port 5000
```
- **UI**: [http://localhost:5000](http://localhost:5000)

## Key Features

- **Automatic S3 Sync**: On first run, the backend fetches and processes raw job data from S3.
- **Skill Extraction**: High-performance regex-based extraction for 150+ tech skills.
- **Job Recommendations**: TF-IDF based matching with skill gap analysis.
- **Market Trends**: Time-series penetration and momentum analysis for tech skills.
- **SOLID Architecture**: Independent components for easy maintainability and testing.