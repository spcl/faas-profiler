import faas_profiler_python as fp

import os
import boto3

SNS_ARN = os.environ.get("SNS_ARN")


@fp.profile()
def handler(event, context):
    sns_client = boto3.client("sns", region_name="eu-central-1")

    for idx in range(0, 50):
        sns_client.publish(
            TopicArn=SNS_ARN,
            Message='Message',
            Subject=f'Message with ID {idx}')

    return {"statusCode": 200}
