import subprocess
import os
import requests
import time

from google.cloud import compute_v1
from google.api_core.exceptions import GoogleAPIError

from app.domain.interfaces.i_cloud_provider import ICloudProvider


class GCPProvider(ICloudProvider):

    APPLICATION_URL = "http://127.0.0.1:5000/"

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
                "endpoint_healthy": False,
                "message": "GCP instance name is not configured"
            }

        try:
            instance = self.client.get(
                project=self.project_id,
                zone=node.region or self.zone,
                instance=instance_name
            )

            try:
                response = requests.get(
                    self.APPLICATION_URL,
                    timeout=5
                )

                endpoint_healthy = (
                    response.status_code == 200
                    and response.json().get("status") == "running"
                )

            except Exception:
                endpoint_healthy = False

            return {
                "provider": "GCP",
                "node_id": node.id,
                "status": str(instance.status).upper(),
                "endpoint_healthy": endpoint_healthy
            }

        except GoogleAPIError as error:
            return {
                "provider": "GCP",
                "node_id": node.id,
                "status": "ERROR",
                "endpoint_healthy": False,
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

        if (
            node.provider.upper() != "GCP"
            or node.instance_id != "gcp-backup-node"
        ):
            return {
                "success": False,
                "message": "Invalid GCP backup node"
            }

        aws_backend = "3.110.224.29:80"
        gcp_backend = "127.0.0.1:5000"
        proxy_url = "http://127.0.0.1/"

        # Confirm AWS is active before attempting failover.
        try:
            response = requests.get(proxy_url, timeout=5)
            current_backend = response.headers.get(
                "X-Active-Backend", ""
            )

            if (
                response.status_code != 200
                or current_backend != aws_backend
            ):
                return {
                    "success": False,
                    "message": "AWS primary route could not be verified. No traffic change attempted.",
                    "http_status": response.status_code,
                    "active_backend": current_backend
                }

        except Exception as error:
            return {
                "success": False,
                "message": f"Could not verify current AWS route. No traffic change attempted: {error}"
            }

        # Attempt to switch traffic to GCP.
        failure_message = None
        switch_output = ""

        try:
            result = subprocess.run(
                [
                    "sudo",
                    "/usr/local/sbin/set-failover-backend",
                    "backup"
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            switch_output = result.stdout

            active_backend = ""
            http_status = None
            verification_error = None

            for attempt in range(5):
                try:
                    response = requests.get(proxy_url, timeout=5)
                    http_status = response.status_code
                    active_backend = response.headers.get(
                        "X-Active-Backend", ""
                    )

                    if (
                        response.status_code == 200
                        and active_backend == gcp_backend
                    ):
                        return {
                            "success": True,
                            "message": "GCP backup traffic switch verified",
                            "active_backend": active_backend,
                            "output": switch_output,
                            "verification_attempts": attempt + 1
                        }

                except requests.RequestException as error:
                    verification_error = str(error)

                if attempt < 4:
                    time.sleep(1)

            failure_message = (
                "GCP traffic switch executed, but route verification failed. "
                f"Last HTTP status: {http_status}; "
                f"last backend: {active_backend}; "
                f"verification error: {verification_error}"
            )

        except subprocess.TimeoutExpired:
            failure_message = "GCP traffic switching timed out"

        except subprocess.CalledProcessError as error:
            failure_message = error.stderr or str(error)

        except Exception as error:
            failure_message = str(error)

        # Attempt to restore AWS after any failed switch or verification.
        rollback_command_error = None

        try:
            subprocess.run(
                [
                    "sudo",
                    "/usr/local/sbin/set-failover-backend",
                    "primary"
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

        except Exception as error:
            rollback_command_error = str(error)

        # Verify the actual route, even if the rollback command reported an error.
        try:
            response = requests.get(proxy_url, timeout=5)
            restored_backend = response.headers.get(
                "X-Active-Backend", ""
            )

            rollback_success = (
                response.status_code == 200
                and restored_backend == aws_backend
            )

            rollback_message = (
                "AWS primary route restored and verified"
                if rollback_success
                else "AWS route restoration could not be verified"
            )

        except Exception as error:
            restored_backend = ""
            rollback_success = False
            rollback_message = f"AWS route verification failed: {error}"

        return {
            "success": False,
            "message": failure_message,
            "rollback_success": rollback_success,
            "rollback_message": rollback_message,
            "active_backend": restored_backend,
            "rollback_command_error": rollback_command_error,
            "switch_output": switch_output
        }
