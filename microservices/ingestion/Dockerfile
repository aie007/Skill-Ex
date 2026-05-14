FROM python:3.12-slim

WORKDIR /app

COPY ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ingestion/ ./ingestion/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

# Updated path to run.py
CMD ["python", "ingestion/run.py"]