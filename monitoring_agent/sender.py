import requests


API_URL = "http://127.0.0.1:5000/api/metrics"


def send_metrics(data):

    try:

        response = requests.post(
            API_URL,
            json=data
        )

        return response.json()

    except Exception as e:

        return {
            "error": str(e)
        }