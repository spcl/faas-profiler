import faas_profiler_python as fp

import json

from google.cloud import storage, tasks, pubsub
from uuid import uuid4

"""
Cloud Storage
"""

@fp.profile()
def cloud_storage(request):    
    storage_client = storage.Client()
    bucket = storage_client.bucket("benchmark-dev-bucket")

    obj = { "hello": "world" }

    for idx in range(0, 50):
        blob = bucket.blob(f"{uuid4()}_{idx}.json")
        blob.upload_from_string(json.dumps(obj))

    return {
        "statusCode": 200
    }


"""
Pub/Sub
"""

@fp.profile()
def pub_sub(request):
    pubsub_client = pubsub.PublisherClient()

    for idx in range(0, 50):
        response = pubsub_client.publish("projects/faas-355111/topics/benchmark-dev-topic", str(f"Message with ID {idx}").encode("utf-8"))
        print(f"Queued {response.result()}")

    return {
        "statusCode": 200
    }



"""
Cloud Tasks
"""

@fp.profile()
def cloud_tasks(request):
    cloud_tasks = tasks.CloudTasksClient()

    for idx in range(0, 50):
        task = tasks.Task(
            http_request=tasks.HttpRequest(
                headers={"Content-type": "application/json"},
                http_method=tasks.HttpMethod.POST,
                url="https://europe-west3-faas-355111.cloudfunctions.net/benchmarks-clean-dev-empty",
                body=json.dumps({ "message": f"Message with Id {idx}" }).encode("utf-8"),
                oidc_token=tasks.OidcToken(
                    service_account_email="faas-355111@appspot.gserviceaccount.com",
                    audience="https://europe-west3-faas-355111.cloudfunctions.net/benchmarks-clean-dev-empty")
        ))
        cloud_tasks.create_task(
            task=task,
            parent="projects/faas-355111/locations/europe-west3/queues/benchmark-dev-queue")


    return {
        "statusCode": 200
    }
