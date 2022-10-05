import faas_profiler_python as fp

import sys
import urllib.request


@fp.profile()
def handler(event, context):
    """
    Calculate time shift
    """

    request = urllib.request.urlopen('http://www.example.org/')
    webpage = request.read().decode('utf-8')

    return {
        "statusCode": 200,
        "message": sys.getsizeof(webpage)
    }


if __name__ == "__main__":
    handler(None, None)