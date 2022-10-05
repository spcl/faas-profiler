import json
import os
import logging
import base64
import requests

from google.cloud.pubsub import PublisherClient
from google.cloud import tasks
from google.cloud import datastore    

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

QUOTES_API = os.environ.get("QUOTES_API", "api.quotable.io")

SCRAP_TOPIC = os.environ.get("PUBSUB_SCARP_TOPIC", "projects/faas-355111/topics/quotes-dev-scrap")

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def dispatch_scrappers(request):
    """
    Takes a list of quote tags and distribute its via Pub/Sub
    """
    pubsub_client = PublisherClient()

    tags = [
        "love", "inspirational", "humor", "philosophy", "god", "truth", "inspirational-quotes", "wisdom", "romance", "happiness"]
    for tag in tags:
        response = pubsub_client.publish(SCRAP_TOPIC, str(tag).encode("utf-8"))
        print(response.result())

    return {
        "statusCode": 200
    }



def scrap_quotes(event, context):
    """
    Gets invoke for a new Pub/Sub Message.
    Takes the tags and queries the API to load the quotes.
    """
    if not event or not 'data' in event:
        raise RuntimeError("Got event with no data")

    cloud_tasks = tasks.CloudTasksClient()

    tag = base64.b64decode(event['data'])

    logging.info(f"Fetching quotes for {tag}")

    get_request = requests.get(f"http://{QUOTES_API}/quotes", params=dict(tags=tag, limit=150))
    if not get_request.status_code == 200:
        logger.info(f"Failed to get quotes: {get_request.reason} (CODE: {get_request.status_code})")
        return { "statusCode": get_request.status_code, "message": get_request.reason }

    response = json.loads(get_request.content)
    quotes = response.get("results", [])

    logging.info(f"Fetched {len(quotes)} quotes for {tag}")

    url = "https://europe-west3-faas-355111.cloudfunctions.net/quotes-clean-dev-save_quotes"

    for chunk in chunks(quotes, 10):
        task = tasks.Task(
            http_request=tasks.HttpRequest(
                headers={"Content-type": "application/json"},
                http_method=tasks.HttpMethod.POST,
                url=url,
                body=json.dumps({ "quotes": chunk }).encode("utf-8"),
                oidc_token=tasks.OidcToken(
                    service_account_email="faas-355111@appspot.gserviceaccount.com",
                    audience="https://europe-west3-faas-355111.cloudfunctions.net/quotes-clean-dev-save_quotes")
        ))
        response = cloud_tasks.create_task(
            task=task,
            parent="projects/faas-355111/locations/europe-west3/queues/sample")


    return {
        "statusCode": 200
    }



def save_quotes(request):
    """
    Saves quotes to database
    """
    datastore_client = datastore.Client()
    kind = "quote"

    data = request.get_json()
    quotes = data.get("quotes", [])

    for quote in quotes:
        if not "_id" in quote:
            continue
        
        quote_key = datastore_client.key(kind, quote.get("_id"))
        quote_entry = datastore.Entity(key=quote_key)
        quote_entry["author"] = quote.get("author")
        quote_entry["content"] = quote.get("content")

        # Saves the entity
        datastore_client.put(quote_entry)

        print(f"Saved {quote_entry.key.name}")

    return {
        "statusCode": 200
    }

