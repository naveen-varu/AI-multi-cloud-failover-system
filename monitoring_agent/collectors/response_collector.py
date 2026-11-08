import time
import requests


FAILURE_RESPONSE_TIME = 2001


def get_response_time(url):
    start = time.monotonic()

    try:
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return FAILURE_RESPONSE_TIME

        try:
            if response.json().get("status") != "healthy":
                return FAILURE_RESPONSE_TIME
        except (ValueError, AttributeError):
            return FAILURE_RESPONSE_TIME

        elapsed = (time.monotonic() - start) * 1000
        return round(elapsed, 2)

    except requests.RequestException:
        return FAILURE_RESPONSE_TIME
