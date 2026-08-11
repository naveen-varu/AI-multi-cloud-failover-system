import os

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient


class AzureClient:

    def __init__(self):
        self.subscription_id = os.getenv(
            "AZURE_SUBSCRIPTION_ID"
        )

    def get_compute_client(self):

        if not self.subscription_id:
            raise ValueError(
                "AZURE_SUBSCRIPTION_ID is not configured"
            )

        credential = DefaultAzureCredential()

        return ComputeManagementClient(
            credential,
            self.subscription_id
        )