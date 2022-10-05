from uuid import uuid4
import faas_profiler_python as fp

import os
import boto3
import shutil

COLLECION_BUCKET = os.environ.get(
    "PHOTO_COLLECTION_BUCKET",
    "sample-photo-collection")


@fp.profile()
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
            
            filename = f"{uuid4()}.jpg"
            efs_path = os.path.join("/", "mnt", "lambda", filename)
            tmp_path = os.path.join("/", "tmp", filename)

            s3_client.download_file(COLLECION_BUCKET, _key, tmp_path)
            shutil.copy(tmp_path, efs_path)

            messages.append(
                f"Saved {_key} in {efs_path}")

    return {
        "statusCode": 200,
        "message": messages
    }
