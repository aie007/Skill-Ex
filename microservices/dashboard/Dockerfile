FROM python:3.12-slim

WORKDIR /app

COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard/ ./dashboard/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

# Updated path to app.py
CMD ["streamlit", "run", "dashboard/app.py"]
