import time

from collectors.cpu_collector import get_cpu_usage
from collectors.memory_collector import get_memory_usage
from collectors.disk_collector import get_disk_usage
from collectors.response_collector import get_response_time
from sender import send_metrics


NODE_ID = 1
INTERVAL = 30  # seconds


def collect_metrics():
    return {
        "node_id": NODE_ID,
        "cpu_usage": get_cpu_usage(),
        "memory_usage": get_memory_usage(),
        "disk_usage": get_disk_usage(),
        "response_time": get_response_time("http://127.0.0.1:5000")
    }


if __name__ == "__main__":
    while True:
        metrics = collect_metrics()

        print("Collected:")
        print(metrics)

        result = send_metrics(metrics)

        print("Server Response:")
        print(result)

        print("Waiting 30 seconds...\n")

        time.sleep(INTERVAL)