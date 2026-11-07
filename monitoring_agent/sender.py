import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://127.0.0.1:5000/api/metrics"

def send_metrics(data):
    api_key = os.getenv("FAILOVER_API_KEY")

    if not api_key:
        return {"error": "FAILOVER_API_KEY is not configured"}

    try:
        response = requests.post(
            API_URL,
            json=data,
            headers={"X-API-Key": api_key},
            timeout=10
        )

        try:
            return response.json()
        except ValueError:
            return {
                "error": "Server returned a non-JSON response",
                "status_code": response.status_code
            }

    except requests.RequestException as error:
        return {"error": str(error)}
