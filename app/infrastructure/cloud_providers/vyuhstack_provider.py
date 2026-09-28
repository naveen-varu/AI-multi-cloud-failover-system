from app.domain.interfaces.i_cloud_provider import ICloudProvider


class VyuhStackProvider(ICloudProvider):

    def get_health(self, node):
        if not node.instance_id:
            return {
                "provider": "VyuhStack",
                "node_id": node.id,
                "status": "UNKNOWN",
                "message": "VyuhStack VM instance ID is not configured"
            }

        return {
            "provider": "VyuhStack",
            "node_id": node.id,
            "status": node.status
        }

    def start_node(self, node):
        return {
            "success": True,
            "message": f"VyuhStack node {node.id} start requested"
        }

    def stop_node(self, node):
        return {
            "success": True,
            "message": f"VyuhStack node {node.id} stop requested"
        }

    def switch_traffic(self, node):
        return {
            "success": True,
            "message": f"Traffic switched to VyuhStack node {node.id}"
        }