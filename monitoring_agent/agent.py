from collectors.cpu_collector import get_cpu_usage
from collectors.memory_collector import get_memory_usage
from collectors.disk_collector import get_disk_usage


def collect_metrics():

    data = {

        "cpu_usage":
        get_cpu_usage(),

        "memory_usage":
        get_memory_usage(),

        "disk_usage":
        get_disk_usage()

    }


    return data



if __name__ == "__main__":

    metrics = collect_metrics()

    print(metrics)