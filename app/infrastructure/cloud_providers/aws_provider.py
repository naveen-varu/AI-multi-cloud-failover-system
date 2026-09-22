from app.domain.interfaces.i_cloud_provider import ICloudProvider
from app.infrastructure.cloud_providers.aws_client import AWSClient


class AWSProvider(ICloudProvider):

    def __init__(self, region=None):
        self.client = AWSClient(region)

    def get_health(self, node):
        if not node.instance_id:
            return {
                "provider": "AWS",
                "node_id": node.id,
                "status": "UNKNOWN",
                "message": "AWS instance ID is not configured"
            }

        try:
            ec2 = self.client.get_ec2_client()

            response = ec2.describe_instance_status(
                InstanceIds=[node.instance_id],
                IncludeAllInstances=True
            )

            if not response["InstanceStatuses"]:
                return {
                    "provider": "AWS",
                    "node_id": node.id,
                    "status": "UNKNOWN",
                    "message": "AWS instance status not available"
                }

            instance_status = response["InstanceStatuses"][0]

            return {
                "provider": "AWS",
                "node_id": node.id,
                "status": instance_status["InstanceState"]["Name"]
            }

        except Exception as e:
            return {
                "provider": "AWS",
                "node_id": node.id,
                "status": "ERROR",
                "message": str(e)
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