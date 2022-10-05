import json
import os
import boto3
import logging
import requests

from datetime import datetime
from decimal import Decimal


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

REGION = os.environ.get("AWS_REGION", "eu-central-1")

QUOTES_API = os.environ.get("QUOTES_API", "api.quotable.io")

SNS_SCRAP_ARN = os.environ.get("SNS_SCRAP_ARN")
SQS_URL = os.environ.get("SQS_URL")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "quotes-dev-quotes")


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def dispatch_scrappers(event, context):
    sns_client = boto3.client("sns", region_name=REGION)

    tags = [
        "love",
        "inspirational",
        "humor",
        "philosophy",
        "god",
        "truth",
        "inspirational-quotes",
        "wisdom",
        "romance",
        "happiness"]
    for tag in tags:
        sns_client.publish(
            TopicArn=SNS_SCRAP_ARN,
            Message='Scrap',
            Subject=tag)

    return {
        "statusCode": 200
    }


def scrap_quotes(event, context):
    sqs_client = boto3.client("sqs", region_name=REGION)

    records = event.get("Records")
    if not records:
        raise RuntimeError("Got event with no records")

    subject = records[0].get("Sns", {}).get("Subject")
    if not subject:
        raise RuntimeError("Got no subject")

    logger.info(f"Fetching quotes for {subject}")

    get_request = requests.get(
        f"http://{QUOTES_API}/quotes",
        params=dict(
            tags=subject,
            limit=150))
    if not get_request.status_code == 200:
        logger.info(
            f"Failed to get quotes: {get_request.reason} (CODE: {get_request.status_code})")
        return {
            "statusCode": get_request.status_code,
            "message": get_request.reason}

    response = json.loads(get_request.content)
    quotes = response.get("results", [])

    logger.info(f"Fetched {len(quotes)} quotes for {subject}")

    for chunk in chunks(quotes, 10):
        sqs_client.send_message_batch(
            QueueUrl=SQS_URL,
            Entries=[{
                'Id': str(idx),
                'MessageBody': json.dumps(msg)
            } for idx, msg in enumerate(chunk)])

    return {
        "statusCode": 200
    }


def save_quotes(event, context):
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)

    records = event.get("Records", [])

    timestamp = datetime.now().timestamp()

    with table.batch_writer() as batch:
        for record in records:
            body = json.loads(record.get("body"))
            _id = body.get("_id")
            _author = body.get("authorSlug")
            _content = body.get("content")

            if not _id or not _author:
                continue

            batch.put_item(
                Item=dict(
                    quoteId=_id,
                    author=_author,
                    used=0,
                    quote=_content,
                    createdAt=Decimal(timestamp),
                    updatedAt=Decimal(timestamp)
                )
            )

    return {
        "statusCode": 200
    }
