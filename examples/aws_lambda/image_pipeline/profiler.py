import faas_profiler_python as fp

import json
import os
import boto3
import uuid
import logging

from PIL import Image

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

COLLECION_BUCKET = os.environ.get(
    "PHOTO_COLLECTION_BUCKET",
    "sample-photo-collection")
THUMBNAIL_BUCKET = os.environ.get(
    "THUMBNAIL_BUCKET",
    "image-pipeline-dev-images-thumbnails")

REGION = os.environ.get("FUNCTION_REGION", "eu-central-1")

PROCESS_FUNCTION = os.environ.get(
    "PROCESS_FUNCTION",
    "image-thumbnailer-dev-process_image")
THUMBNAIL_FUNCTION = os.environ.get(
    "THUMBNAIL_FUNCTION",
    "image-thumbnailer-dev-thumbnail_image")

EFS_MOUNT = os.environ.get("EFS_MOUNT", "/mnt/lambda")

"""
Clients
"""

s3_client = boto3.client('s3')
lambda_client = boto3.client("lambda", region_name=REGION)

"""
Helper
"""


def return_message(code: int = 200, message=None) -> dict:
    return {
        "statusCode": code,
        "message": message
    }


"""
Handlers
"""


@fp.profile()
def distribute_work(event, context):
    """
    Distribute Work to process image.

    Reads all images from a bucket order and calls a function async to process them.
    """
    collection_folder = event.get("collection_folder", "nature/")

    paginator = s3_client.get_paginator('list_objects')
    page_iterator = paginator.paginate(
        Bucket=COLLECION_BUCKET,
        Prefix=collection_folder)

    messages = []
    for page in page_iterator:
        for content in page.get("Contents", []):
            _key = content.get("Key")
            if not _key:
                continue

            lambda_client.invoke(
                FunctionName=PROCESS_FUNCTION,
                InvocationType="Event",
                Payload=json.dumps({
                    "bucket_name": COLLECION_BUCKET,
                    "object_key": _key
                }).encode('utf-8'))

            messages.append(
                f"Invoke async {PROCESS_FUNCTION} function for image {_key}")

    return return_message(message=messages)


@fp.profile()
def process_image(event, context):
    """
    Edits a single image.
    Saves the original image to EFS and calls functions to edit the image.
    """
    image_bucket, image_key = event.get("bucket_name"), event.get("object_key")
    if not image_bucket or not image_key:
        return return_message(
            code=400, message="Please provide a bucket name and object key")

    ratios = [5, 10]

    for ratio in ratios:
        lambda_client.invoke(
            FunctionName=THUMBNAIL_FUNCTION,
            InvocationType="Event",
            Payload=json.dumps({
                "bucket_name": image_bucket,
                "object_key": image_key,
                "ratio": 2
            }).encode('utf-8'))
        logger.info(
            f"Invoked async {THUMBNAIL_FUNCTION} to thumbnail {image_key} with ratio {ratio}")

    return return_message(message="Invoked thumbnailer")


@fp.profile()
def thumbnail_image(event, context):
    """
    Create thumbnail for given image and ratio. Stores image in thumbnail bucket.
    """
    image_bucket, image_key = event.get("bucket_name"), event.get("object_key")
    if not image_bucket or not image_key:
        return return_message(
            code=400, message="Please provide a bucket name and object key")

    ratio = int(event.get("ratio"))
    if not ratio:
        return return_message(
            code=400, message="Please provide a thumbnail ration")

    logger.info(f"Get S3 image (bucket={image_bucket}, key={image_key})")
    response = s3_client.get_object(Bucket=image_bucket, Key=image_key)
    file_stream = response['Body']
    logger.info("Load S3 image.")
    image = Image.open(file_stream)

    logger.info(f"Make thumbail (ratio={ratio}).")
    image.thumbnail(tuple(x / ratio for x in image.size))

    thumbnail_name = "thumbnail_{id}.jpg".format(id=uuid.uuid4())
    thumbnail_path = os.path.abspath(os.path.join("/", "tmp", thumbnail_name))
    logger.info(f"Save thumbail to {thumbnail_path}.")
    image.save(thumbnail_path)

    logger.info(
        f"Upload thumbail from {thumbnail_path} to {THUMBNAIL_BUCKET}.")
    print("Start")
    s3_client.upload_file(thumbnail_path, THUMBNAIL_BUCKET, thumbnail_name)
    print("Stop")

    return return_message(
        message=f"Thumbnail for {image_key} in ratio {ratio} created.")


@fp.profile()
def save_image(event, context):
    """
    Gets invoked if a file was uploaded to S3 bucket.
    Stores image to EFS.
    """
    records = event.get("Records", [])
    for record in records:
        s3_record = record.get("s3")
        if not s3_record:
            continue

        _bucket_name = s3_record.get("bucket", {}).get("name")
        _object_key = s3_record.get("object", {}).get("key")
        if not _bucket_name or not _object_key:
            continue

        efs_image_path = os.path.abspath(os.path.join(EFS_MOUNT, _object_key))
        logger.info(
            f"Download image {_object_key} from {_bucket_name} to {efs_image_path}")
        s3_client.download_file(_bucket_name, _object_key, efs_image_path)
        logger.info(f"Saved image in EFS {efs_image_path}")

    return return_message(message="Saved images to EFS")
