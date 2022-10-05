import io
import json
import os
import uuid
import logging

from google.cloud import storage, tasks
from PIL import Image

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

COLLECION_BUCKET = os.environ.get("PHOTO_COLLECTION_BUCKET", "sample-photo-collection")
THUMBNAIL_BUCKET = os.environ.get("THUMBNAIL_BUCKET", "image-pipeline-dev-images-thumbnails")

SERVICE_ACCOUNT = os.environ.get("SERVICE_ACCOUNT", "faas-355111@appspot.gserviceaccount.com")

PROCESS_FUNCTION = os.environ.get("PROCESS_FUNC_URL", "https://faas-355111-europe-west3.cloudfunctions.net/image-pipeline-dev-process_image")
THUMBNAIL_FUNCTION = os.environ.get("THUMBNAIL_FUNC_URL", "https://faas-355111-europe-west3.cloudfunctions.net/image-pipeline-dev-thumbnail_image")

QUEUE_URL = os.environ.get("QUEUE_URL", "projects/faas-355111/locations/europe-west3/queues/image-pipeline-dev-queue")


"""
Clients
"""

storage_client = storage.Client()
tasks_client = tasks.CloudTasksClient()

"""
Helper
"""

def return_message(code: int = 200, message = None) -> dict:
    return {
        "statusCode": code,
        "message": message
    }

"""
Handlers
"""

def distribute_work(request):
    """
    Distribute Work to process image.

    Reads all images from a bucket order and calls a function async to process them.
    """
    print(os.environ)

    image_blobs = storage_client.list_blobs(
        COLLECION_BUCKET,
        prefix="nature/",
        delimiter="/")

    messages = []
    for image_blob in image_blobs:
        if str(image_blob.name).endswith("/"):
            continue

        task = tasks.Task(
            http_request=tasks.HttpRequest(
                headers={"Content-type": "application/json"},
                http_method=tasks.HttpMethod.POST,
                url=PROCESS_FUNCTION,
                body=json.dumps({ 
                    "blob_name": image_blob.name,
                    "bucket_name": image_blob.bucket.name
                }).encode("utf-8"),
                oidc_token=tasks.OidcToken(
                    service_account_email=SERVICE_ACCOUNT,
                    audience=PROCESS_FUNCTION)))

        tasks_client.create_task(
            task=task,
            parent=QUEUE_URL)

        messages.append(
            f"Invoke async {PROCESS_FUNCTION} function for image {image_blob.name}")
   
    return return_message(message=messages)


def process_image(request):
    """
    Edits a single image.
    Saves the original image to EFS and calls functions to edit the image.
    """
    print(request.data)
    print(request.headers)

    data = request.get_json()

    image_bucket, blob_name = data.get("bucket_name"), data.get("blob_name")
    if not image_bucket or not blob_name:
        return return_message(code=400, message="Please provide a bucket name and blob name")

    ratios = [5, 10]

    for ratio in ratios:
        task = tasks.Task(
            http_request=tasks.HttpRequest(
                headers={"Content-type": "application/json"},
                http_method=tasks.HttpMethod.POST,
                url=THUMBNAIL_FUNCTION,
                body=json.dumps({ 
                    "blob_name": blob_name,
                    "bucket_name": image_bucket,
                    "ratio": ratio
                }).encode("utf-8"),
                oidc_token=tasks.OidcToken(
                    service_account_email=SERVICE_ACCOUNT,
                    audience=THUMBNAIL_FUNCTION)))

        tasks_client.create_task(
            task=task,
            parent=QUEUE_URL)

        logger.info(
            f"Invoked async {THUMBNAIL_FUNCTION} to thumbnail {blob_name} with ratio {ratio}")

    return return_message(message="Invoked thumbnailer")


def thumbnail_image(request):
    """
    Create thumbnail for given image and ratio. Stores image in thumbnail bucket.
    """
    print(request.data)
    print(request.headers)

    data = request.get_json()

    image_bucket, blob_name = data.get("bucket_name"), data.get("blob_name")
    if not image_bucket or not blob_name:
        return return_message(code=400, message="Please provide a bucket name and blob name")

    ratio = int(data.get("ratio"))
    if not ratio:
        return return_message(code=400, message="Please provide a thumbnail ration")

    sample_bucket = storage_client.bucket(image_bucket)
    thumnail_bucket = storage_client.bucket(THUMBNAIL_BUCKET)

    logger.info(f"Get Cloud image (bucket={image_bucket}, name={blob_name})")
    blob = sample_bucket.get_blob(blob_name)
    image_bytes = io.BytesIO(blob.download_as_string())
    
    logger.info("Load image.")
    image = Image.open(image_bytes)

    logger.info(f"Make thumbail (ratio={ratio}).")
    image.thumbnail(tuple(x / ratio for x in image.size))

    thumbnail_name = "thumbnail_{id}.jpg".format(id=uuid.uuid4())
    thumbnail_path = os.path.abspath(os.path.join("/", "tmp", thumbnail_name))
    logger.info(f"Save thumbail to {thumbnail_path}.")
    image.save(thumbnail_path)

    logger.info(f"Upload thumbail from {thumbnail_path} to {THUMBNAIL_BUCKET}.")
    thumbnail_blob = thumnail_bucket.blob(thumbnail_name)
    thumbnail_blob.upload_from_filename(thumbnail_path)

    return return_message(message=f"Thumbnail for {blob_name} in ratio {ratio} created.")

