# Skill-Ex: AI Career Radar

Skill-Ex is an MLOps-ready platform for skill extraction, job recommendation, and market trend analysis.

## Project Structure

```
microservices/
├── ingestion/          # API Fetching & S3/SQLite Syncing
├── model_training/     # ML Training & MLflow Logging
├── recommendation_api/ # FastAPI Inference Service
└── dashboard/          # Streamlit UI
shared/                 # Shared logic (Interfaces, Config, Utils)
airflow-jobs/           # Orchestration (DAGs, Config)
```

## Running the Microservices

Each service can be run independently from the project root:

### 1. Recommendation API (FastAPI)
```bash
export PYTHONPATH=$PYTHONPATH:.
uvicorn microservices.recommendation_api.main:app --reload --port 8000
```
- **UI**: [http://localhost:8000](http://localhost:8000)

### 2. Dashboard (Streamlit)
```bash
streamlit run microservices/dashboard/app.py
```
- **UI**: [http://localhost:8501](http://localhost:8501)

### 3. Ingestion & Training (Manual)
```bash
# Via Orchestrator
python scripts/pipeline_tasks.py fetch-and-sync
python scripts/pipeline_tasks.py train

# Directly
python microservices/ingestion/run.py
python microservices/model_training/train.py
```

## MLOps Pipeline (DVC)

We use DVC to manage data versioning and pipeline execution across microservices.

1. **Pull Data**: `dvc pull`
2. **Run Pipeline**: `dvc repro` (Runs Ingestion -> Training)
3. **Track Changes**: `dvc push`

## Workflow Orchestration (Airflow)

A weekly automated pipeline is configured in `airflow-jobs/` to keep the system up to date.

### Option A: Running with Docker (Recommended)
```bash
cd airflow-jobs
docker-compose up -d
```
The UI will be available at [http://localhost:8085](http://localhost:8085).

### Option B: Running with Virtual Environment
1. **Set Airflow Home**: `export AIRFLOW_HOME=$(pwd)/airflow-jobs`
2. **Set Dags Folder**: `export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/airflow-jobs/dags`
3. **Run**: `./venv/bin/airflow standalone`


## Prerequisites

- Python 3.12+
- Virtual environment (`venv`)
- Amazon S3 bucket (for raw data)
- RapidAPI Key (for JSearch API)

## Setup

1. **Virtual Environment**:
   Ensure your virtual environment is active and dependencies are installed.
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file in the root directory with the following keys:
   ```env
   RAPIDAPI_KEY=your_key_here
   AWS_ACCESS_KEY_ID=your_id_here
   AWS_SECRET_ACCESS_KEY=your_secret_here
   AWS_RAW_BUCKET=amzn-s3-raw-bucket-skillex
   AWS_PROCESSED_BUCKET=amzn-s3-processed-bucket-skillex
   ```

## API Reference
- **Interactive Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Status Endpoint**: [http://localhost:8000/](http://localhost:8000/)

## Key Features

- **Microservices Architecture**: Independent, decoupled services for Ingestion, Training, API, and Dashboard.
- **Automated Pipeline**: End-to-end flow managed by Airflow 3.x.
- **Data Version Control**: DVC ensures reproducibility of datasets.
- **Skill Extraction**: High-performance regex-based extraction for 150+ tech skills.
- **Job Recommendations**: TF-IDF based matching with skill gap analysis.
- **Market Trends**: Time-series penetration and momentum analysis for tech skills.
- **SOLID Design**: Shared core logic and interfaces for easy maintainability.