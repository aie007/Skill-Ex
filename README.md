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
You can run these via the global orchestrator or directly:
```bash
# Via Orchestrator
python scripts/pipeline_tasks.py fetch-and-sync
python scripts/pipeline_tasks.py train

# Directly
python microservices.ingestion.run
python microservices.model_training.train
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

## MLflow & Experiment Tracking
Run `mlflow ui --port 5000` to view metrics and artifacts at [http://localhost:5000](http://localhost:5000).

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

## Running the Backend

The backend is a FastAPI application. It automatically handles database initialization and syncs data from S3 if the local database is empty.

```bash
# From the project root
export PYTHONPATH=$PYTHONPATH:.
uvicorn backend.main:app --reload --port 8000
```

- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Web UI**: [http://localhost:8000/](http://localhost:8000/)

## MLOps Pipeline (DVC)

We use DVC to manage data versioning and pipeline execution.

1. **Pull Data**:
   To fetch the latest versioned data from S3:
   ```bash
   dvc pull
   ```

2. **Run Pipeline**:
   To execute the full data ingestion and model training pipeline (Fetch -> Sync -> Train):
   ```bash
   dvc repro
   ```

3. **Track Changes**:
   If you modify data or logic, run `dvc repro` and then push the new state:
   ```bash
   dvc push
   ```

## Workflow Orchestration (Airflow)

A weekly automated pipeline is configured in `airflow-jobs/` to keep the system up to date.

### Option A: Running with Docker (Recommended)
This is the easiest way to run the full Airflow stack (Scheduler, Worker, Webserver).
```bash
cd airflow-jobs
docker-compose up -d
```
The UI will be available at [http://localhost:8085](http://localhost:8085) (default credentials: `airflow`/`airflow`).

### Option B: Running with Virtual Environment
If you prefer to run locally without Docker:
1. **Set Airflow Home**:
   ```bash
   export AIRFLOW_HOME=$(pwd)/airflow-jobs
   ```
2. **Initialize Database**:
   ```bash
   ./venv/bin/airflow db init
   ```
3. **Create Admin User**:
   ```bash
   ./venv/bin/airflow users create --username admin --firstname admin --lastname admin --role Admin --email admin@example.com --password admin
   ```
4. **Start Scheduler** (handles periodic runs):
   ```bash
   ./venv/bin/airflow scheduler
   ```
4. **Start Webserver** (UI):
   ```bash
   ./venv/bin/airflow webserver -p 8080
   ```

2. **DAG Location**: `airflow-jobs/dags/weekly_mlops.py`

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

- **Automated Pipeline**: End-to-end flow from API to versioned models.
- **Data Version Control**: DVC ensures reproducibility of datasets.
- **Skill Extraction**: High-performance regex-based extraction for 150+ tech skills.
- **Job Recommendations**: TF-IDF based matching with skill gap analysis.
- **Market Trends**: Time-series penetration and momentum analysis for tech skills.
- **SOLID Architecture**: Independent components for easy maintainability and testing.