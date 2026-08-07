import time
import requests


def get_response_time(url):

    start = time.time()

    try:

        requests.get(url)

        end = time.time()

        return round(
            (end-start)*1000,
            2
        )

    except:

        return -1