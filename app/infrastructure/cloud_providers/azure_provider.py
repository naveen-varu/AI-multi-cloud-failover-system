from app.domain.interfaces.i_cloud_provider import ICloudProvider
from app.infrastructure.cloud_providers.azure_client import AzureClient


class AzureProvider(ICloudProvider):

    def __init__(self, subscription_id=None):
        self.client = AzureClient(subscription_id)

    def get_health(self, node):
        if not node.instance_id:
            return {
                "provider": "Azure",
                "node_id": node.id,
                "status": "UNKNOWN",
                "message": "Azure VM instance ID is not configured"
            }

        try:
            compute = self.client.get_compute_client()

            instance_view = compute.virtual_machines.instance_view(
                resource_group_name=self.client.resource_group,
                vm_name=node.instance_id
            )

            for status in instance_view.statuses:
                 if status.code.startswith("PowerState/"):
                    return {
                       "provider": "Azure",
                       "node_id": node.id,
                       "status": status.code.split("/", 1)[1]
                  }

        except Exception as e:
            return {
                "provider": "Azure",
                "node_id": node.id,
                "status": "ERROR",
                "message": str(e)
            }

    def start_node(self, node):
        return {
            "success": True,
            "message": f"Azure node {node.id} start requested"
        }

    def stop_node(self, node):
        return {
            "success": True,
            "message": f"Azure node {node.id} stop requested"
        }

    def switch_traffic(self, node):
        return {
            "success": True,
            "message": f"Traffic switched to Azure node {node.id}"
        }