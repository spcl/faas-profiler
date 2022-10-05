
import sys
import urllib.request


def handler(event, context):
    """
    Download Example.org website
    """

    request = urllib.request.urlopen('http://www.example.org/')
    webpage = request.read().decode('utf-8')

    return {
        "statusCode": 200,
        "message": sys.getsizeof(webpage)
    }
