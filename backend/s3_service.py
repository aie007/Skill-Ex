import os
import pandas as pd
from io import BytesIO
import boto3
from dotenv import load_dotenv

load_dotenv()  
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


s3 = boto3.client("s3")

bucket_name = "amzn-s3-skillex"
objects_list = s3.list_objects_v2(Bucket=bucket_name).get("Contents", [])

for obj in objects_list:
    key = obj['Key']
    
    if key  in ("company.parquet"):
        response = s3.get_object(Bucket=bucket_name, Key=key)
        bytes_data = response['Body'].read()

        df = pd.read_parquet(BytesIO(bytes_data))
        print(f"\nData from {key}:")
        print(df.head())