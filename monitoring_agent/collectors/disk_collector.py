import psutil


def get_disk_usage():

    disk = psutil.disk_usage("/")

    return disk.percent