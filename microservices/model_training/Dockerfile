FROM python:3.12-slim

WORKDIR /app

COPY model_training/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY model_training/ ./model_training/
COPY shared/ ./shared/
COPY ml/ ./ml/

ENV PYTHONPATH=/app

# Updated path to main.py
CMD ["python", "model_training/main.py"]
