import os

from google.cloud import compute_v1
from google.api_core.exceptions import GoogleAPIError

from app.domain.interfaces.i_cloud_provider import ICloudProvider


class GCPProvider(ICloudProvider):

    def __init__(self, project_id=None, zone=None):
        self.project_id = project_id or os.getenv(
            "GCP_PROJECT_ID", "multi-cloud-failover"
        )
        self.zone = zone or os.getenv(
            "GCP_ZONE", "asia-south1-b"
        )
        self.client = compute_v1.InstancesClient()

    def _get_instance_name(self, node):
        return node.instance_id

    def get_health(self, node):
        instance_name = self._get_instance_name(node)

        if not instance_name:
            return {
                "provider": "GCP",
                "node_id": node.id,
                "status": "UNKNOWN",
                "message": "GCP instance name is not configured"
            }

        try:
            instance = self.client.get(
                project=self.project_id,
                zone=node.region or self.zone,
                instance=instance_name
            )

            return {
                "provider": "GCP",
                "node_id": node.id,
                "status": instance.status
            }

        except GoogleAPIError as error:
            return {
                "provider": "GCP",
                "node_id": node.id,
                "status": "ERROR",
                "message": str(error)
            }

    def start_node(self, node):
        try:
            operation = self.client.start(
                project=self.project_id,
                zone=node.region or self.zone,
                instance=node.instance_id
            )
            operation.result(timeout=120)

            return {
                "success": True,
                "message": f"GCP node {node.id} started successfully"
            }

        except Exception as error:
            return {
                "success": False,
                "message": str(error)
            }

    def stop_node(self, node):
        try:
            operation = self.client.stop(
                project=self.project_id,
                zone=node.region or self.zone,
                instance=node.instance_id
            )
            operation.result(timeout=120)

            return {
                "success": True,
                "message": f"GCP node {node.id} stopped successfully"
            }

        except Exception as error:
            return {
                "success": False,
                "message": str(error)
            }

    def switch_traffic(self, node):
        return {
            "success": False,
            "message": (
                "GCP traffic routing is not configured yet. "
                "A routing mechanism must be implemented before failover."
            )
        }
