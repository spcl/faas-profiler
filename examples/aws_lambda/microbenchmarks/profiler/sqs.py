import faas_profiler_python as fp

import os
import boto3

from uuid import uuid4

SQS_URL = os.environ.get("SQS_URL")


@fp.profile()
def handler(event, context):
    sqs_client = boto3.client("sqs", region_name="eu-central-1")

    for idx in range(0, 50):
        sqs_client.send_message(QueueUrl=SQS_URL,
                                MessageBody=f"SQS message {idx} ({uuid4()})")

    return {
        "statusCode": 200
    }
