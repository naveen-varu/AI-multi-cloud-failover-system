import subprocess
import requests
import time

from app.domain.interfaces.i_cloud_provider import ICloudProvider
from app.infrastructure.cloud_providers.aws_client import AWSClient


class AWSProvider(ICloudProvider):

    PRIMARY_INSTANCE_ID = "i-01a4f91dd0308e2c6"
    APPLICATION_URL = "http://3.110.224.29:5001/health"
    SWITCH_SCRIPT = "/usr/local/sbin/set-failover-backend"

    def __init__(self, region=None):
        self.client = AWSClient(region or "ap-south-1")

    def get_health(self, node):

        if (
            not node.instance_id
            or node.instance_id != self.PRIMARY_INSTANCE_ID
        ):
            return {
                "provider": "AWS",
                "node_id": node.id,
                "status": "UNKNOWN",
                "endpoint_healthy": False,
                "message": "Invalid or missing AWS instance ID"
            }

        try:
            ec2 = self.client.get_ec2_client()

            response = ec2.describe_instance_status(
                InstanceIds=[node.instance_id],
                IncludeAllInstances=True
            )

            statuses = response.get("InstanceStatuses", [])

            if not statuses:
                return {
                    "provider": "AWS",
                    "node_id": node.id,
                    "status": "UNKNOWN",
                    "endpoint_healthy": False,
                    "message": "AWS instance status not available"
                }

            instance_status = statuses[0]

            try:
                app_response = requests.get(
                    self.APPLICATION_URL,
                    timeout=5
                )

                endpoint_healthy = (
                    app_response.status_code == 200
                    and app_response.json().get("status") == "healthy"
                )

            except Exception:
                endpoint_healthy = False

            return {
                "provider": "AWS",
                "node_id": node.id,
                "status": instance_status["InstanceState"]["Name"].upper(),
                "system_status": instance_status["SystemStatus"]["Status"].lower(),
                "instance_status": instance_status["InstanceStatus"]["Status"].lower(),
                "endpoint_healthy": endpoint_healthy
            }

        except Exception as error:
            return {
                "provider": "AWS",
                "node_id": node.id,
                "status": "ERROR",
                "endpoint_healthy": False,
                "message": str(error)
            }

    def start_node(self, node):
        return {
            "success": False,
            "message": "AWS instance start operation is not enabled in this project"
        }

    def stop_node(self, node):
        return {
            "success": False,
            "message": "AWS instance stop operation is not enabled in this project"
        }

    def switch_traffic(self, node):

        if (
            node.provider.upper() != "AWS"
            or node.instance_id != self.PRIMARY_INSTANCE_ID
        ):
            return {
                "success": False,
                "message": "Invalid AWS primary node"
            }

        proxy_url = "http://127.0.0.1/"
        expected_backend = "3.110.224.29:5001"

        try:
            result = subprocess.run(
                [
                    "sudo",
                    self.SWITCH_SCRIPT,
                    "primary"
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            # Retry route verification after Nginx reload.
            active_backend = ""
            last_status = None

            for attempt in range(10):
                try:
                    response = requests.get(
                        proxy_url,
                        timeout=5,
                        headers={"Connection": "close"}
                    )

                    last_status = response.status_code
                    active_backend = response.headers.get(
                        "X-Active-Backend", ""
                    )

                    if (
                        response.status_code == 200
                        and active_backend == expected_backend
                    ):
                        return {
                            "success": True,
                            "message": "AWS primary traffic switch verified",
                            "active_backend": active_backend,
                            "attempts": attempt + 1,
                            "output": result.stdout.strip()
                        }

                except requests.RequestException:
                    pass

                time.sleep(1)

            return {
                "success": False,
                "message": "AWS route verification failed after 10 attempts",
                "http_status": last_status,
                "active_backend": active_backend
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Nginx traffic switching timed out"
            }

        except subprocess.CalledProcessError as error:
            return {
                "success": False,
                "message": error.stderr.strip() or str(error)
            }

        except Exception as error:
            return {
                "success": False,
                "message": f"AWS route verification or switching failed: {error}"
            }
