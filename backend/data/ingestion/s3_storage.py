import json
import boto3
from typing import Any, List
from backend.config.settings import settings

class S3StorageProvider:
    def __init__(self, aws_config=None):
        self.config = aws_config or settings.aws
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=self.config.key_id,
            aws_secret_access_key=self.config.secret
        )

    def upload_json(self, bucket: str, key: str, data: Any):
        self.s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(data, indent=2))

    def fetch_json(self, bucket: str, key: str) -> Any:
        response = self.s3.get_object(Bucket=bucket, Key=key)
        return json.loads(response['Body'].read().decode('utf-8'))

    def list_objects(self, bucket: str, prefix: str = "") -> List[str]:
        response = self.s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.json')]

    def download_file(self, bucket: str, key: str, local_path: str):
        self.s3.download_file(bucket, key, local_path)

    def backup_file(self, bucket: str, file_path: str, remote_key: str):
        with open(file_path, 'rb') as f:
            self.s3.put_object(Bucket=bucket, Key=remote_key, Body=f)
