import os

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient


class AzureClient:

    def __init__(self, subscription_id=None):
        self.subscription_id = subscription_id or os.getenv(
            "AZURE_SUBSCRIPTION_ID"
        )

        self.resource_group = os.getenv(
            "AZURE_RESOURCE_GROUP"
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