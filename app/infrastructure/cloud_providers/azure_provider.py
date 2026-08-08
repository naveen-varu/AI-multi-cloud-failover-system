from app.domain.interfaces.i_cloud_provider import ICloudProvider


class AzureProvider(ICloudProvider):

    def get_health(self, node):
        return {
            "provider": "Azure",
            "node_id": node.id,
            "status": node.status
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