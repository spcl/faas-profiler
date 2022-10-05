import os
import boto3

from uuid import uuid4

COLLECION_BUCKET = os.environ.get(
    "PHOTO_COLLECTION_BUCKET",
    "sample-photo-collection")


def handler(event, context):
    s3_client = boto3.client('s3')

    paginator = s3_client.get_paginator('list_objects')
    page_iterator = paginator.paginate(
        Bucket=COLLECION_BUCKET,
        Prefix="nature/")

    messages = []
    for page in page_iterator:
        for content in page.get("Contents", []):
            _key = content.get("Key")
            if not _key:
                continue

            file_name = os.path.join("/", "mnt", "lambda", f"{uuid4()}.jpg")

            with open(file_name, "wb") as fp:
                s3_client.download_fileobj(COLLECION_BUCKET, _key, fp)
            messages.append(
                f"Saved {_key} in {file_name}")

    return {
        "statusCode": 200,
        "message": messages
    }
