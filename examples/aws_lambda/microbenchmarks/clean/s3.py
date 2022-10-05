import os
import sys
import boto3
import json

from uuid import uuid4

S3_BUCKET = os.environ.get("S3_BUCKET", "benchmarks-dev-bucket")


def handler(event, context):
    s3_client = boto3.client("s3", region_name="eu-central-1")

    obj = {"hello": "world"}

    for idx in range(0, 50):
        object_key = f"{uuid4()}_{idx}.json"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Body=json.dumps(obj),
            Key=object_key)

    return {
        "statusCode": 200
    }
