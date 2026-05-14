FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY ../ml/shared/ /app/ml/shared

ENV PYTHONPATH=/app

CMD ["python", "run.py"]