FROM ghcr.io/mlflow/mlflow:v2.11.3

RUN pip install boto3

EXPOSE 5000

CMD mlflow server \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root s3://${AWS_MODELS_BUCKET}/artifacts \
    --host 0.0.0.0 \
    --port 5000

