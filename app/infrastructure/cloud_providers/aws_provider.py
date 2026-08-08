from app.domain.interfaces.i_cloud_provider import ICloudProvider


class AWSProvider(ICloudProvider):

    def get_health(self, node):
        return {
            "provider": "AWS",
            "node_id": node.id,
            "status": node.status
        }

    def start_node(self, node):
        return {
            "success": True,
            "message": f"AWS node {node.id} start requested"
        }

    def stop_node(self, node):
        return {
            "success": True,
            "message": f"AWS node {node.id} stop requested"
        }

    def switch_traffic(self, node):
        return {
            "success": True,
            "message": f"Traffic switched to AWS node {node.id}"
        }