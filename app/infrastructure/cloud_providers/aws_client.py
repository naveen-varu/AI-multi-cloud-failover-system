import boto3


class AWSClient:

    def __init__(self, region=None):
        self.region = region

    def get_ec2_client(self):
        return boto3.client(
            "ec2",
            region_name=self.region
        )