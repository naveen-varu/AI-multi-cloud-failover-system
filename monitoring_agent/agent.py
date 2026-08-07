from collectors.cpu_collector import get_cpu_usage
from collectors.memory_collector import get_memory_usage
from collectors.disk_collector import get_disk_usage

from sender import send_metrics
from collectors.response_collector import get_response_time


NODE_ID = 1



def collect_metrics():

    return {

        "node_id": NODE_ID,

        "cpu_usage":
        get_cpu_usage(),

        "memory_usage":
        get_memory_usage(),

        "disk_usage":
        get_disk_usage(),

        "response_time":
        get_response_time(
           "http://127.0.0.1:5000"
        )

    }



if __name__ == "__main__":


    metrics = collect_metrics()


    print("Collected:")
    print(metrics)


    result = send_metrics(
        metrics
    )


    print("Server Response:")
    print(result)