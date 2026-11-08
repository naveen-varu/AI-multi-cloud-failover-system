import subprocess
import requests
import time

from app.extensions import db
from app.models.node_model import CloudNode
from app.models.event_model import FailoverEvent
from app.infrastructure.cloud_providers.provider_factory import ProviderFactory
from app.infrastructure.cloud_providers.aws_provider import AWSProvider
from app.services.notification_service import send_telegram_notification


class FailbackService:

    AWS_BACKEND = "3.110.224.29:5001"
    GCP_BACKEND = "127.0.0.1:5001"
    PROXY_URL = "http://127.0.0.1/"
    SWITCH_SCRIPT = "/usr/local/sbin/set-failover-backend"

    @staticmethod
    def verify_route(expected_backend):
        for attempt in range(10):
            try:
                response = requests.get(
                    FailbackService.PROXY_URL,
                    timeout=5,
                    headers={"Connection": "close"}
                )

                active_backend = response.headers.get(
                    "X-Active-Backend", ""
                )

                if (
                    response.status_code == 200
                    and active_backend == expected_backend
                ):
                    return True

            except requests.RequestException:
                pass

            time.sleep(1)

        return False
    @staticmethod
    def rollback_to_gcp():
        try:
            subprocess.run(
                [
                    "sudo",
                    FailbackService.SWITCH_SCRIPT,
                    "backup"
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            return FailbackService.verify_route(
                FailbackService.GCP_BACKEND
            )

        except Exception as error:
            print(f"GCP rollback failed: {error}")
            return False

    @staticmethod
    def execute_failback():

        aws_node = CloudNode.query.filter_by(
            provider="AWS"
        ).first()

        gcp_node = CloudNode.query.filter_by(
            provider="GCP"
        ).first()

        if aws_node is None or gcp_node is None:
            return {
                "success": False,
                "message": "AWS primary or GCP backup node not found"
            }

        if aws_node.instance_id != AWSProvider.PRIMARY_INSTANCE_ID:
            return {
                "success": False,
                "message": "AWS primary instance ID does not match configuration"
            }

        # Safety check: GCP must currently be serving traffic.
        if not FailbackService.verify_route(
            FailbackService.GCP_BACKEND
        ):
            return {
                "success": False,
                "message": "GCP is not verified as the active traffic route. Failback cancelled."
            }

        # Verify AWS cloud and application health.
        try:
            aws_provider = ProviderFactory.get_provider("AWS")
            aws_health = aws_provider.get_health(aws_node)

            aws_healthy = (
                str(aws_health.get("status", "")).upper() == "RUNNING"
                and str(aws_health.get("system_status", "")).lower() == "ok"
                and str(aws_health.get("instance_status", "")).lower() == "ok"
                and aws_health.get("endpoint_healthy") is True
            )

            if not aws_healthy:
                return {
                    "success": False,
                    "message": "AWS primary is not fully healthy. Failback cancelled.",
                    "aws_health": aws_health
                }

            # Confirm the GCP backup application is healthy too.
            gcp_provider = ProviderFactory.get_provider("GCP")
            gcp_health = gcp_provider.get_health(gcp_node)

            gcp_healthy = (
                str(gcp_health.get("status", "")).upper() == "RUNNING"
                and gcp_health.get("endpoint_healthy") is True
            )

            if not gcp_healthy:
                return {
                    "success": False,
                    "message": "GCP backup is not healthy. Failback cancelled.",
                    "gcp_health": gcp_health
                }

            # Switch traffic back to AWS.
            traffic_result = aws_provider.switch_traffic(aws_node)
            if not traffic_result.get("success"):
                rollback_success = FailbackService.rollback_to_gcp()

                return {
                    "success": False,
                    "message": "AWS traffic switch failed. GCP rollback attempted.",
                    "rollback_success": rollback_success,
                    "traffic_result": traffic_result
                }
            # Independently verify the actual route.
            if not FailbackService.verify_route(
                FailbackService.AWS_BACKEND
            ):
                rollback_success = FailbackService.rollback_to_gcp()

                return {
                    "success": False,
                    "message": "AWS route verification failed. GCP rollback attempted.",
                    "rollback_success": rollback_success
                }

            # Record successful failback.
            aws_node.status = "ACTIVE"

            event = FailoverEvent(
                node_id=aws_node.id,
                event_type="AUTOMATIC_FAILBACK",
                reason="AWS primary recovered and traffic routing was verified",
                previous_status="FAILED",
                new_status="ACTIVE"
            )

            try:
                db.session.add(event)
                db.session.commit()

            except Exception as logging_error:
                db.session.rollback()
                print(f"Failback succeeded, but event logging failed: {logging_error}")

            # Notify only after successful traffic verification.
            try:
                send_telegram_notification(
                    "Automatic failback completed successfully.\n"
                    f"AWS primary node: {aws_node.name}\n"
                    f"GCP backup node: {gcp_node.name}\n"
                    "Traffic is now routed to AWS."
                )
            except Exception as notification_error:
                print(f"Failback notification error: {notification_error}")

            return {
                "success": True,
                "message": "AWS primary traffic restored and verified",
                "aws_node_id": aws_node.id,
                "gcp_node_id": gcp_node.id,
                "active_backend": FailbackService.AWS_BACKEND
            }

        except Exception as error:
            db.session.rollback()

            rollback_attempted = False
            rollback_success = None

            try:
                if FailbackService.verify_route(FailbackService.AWS_BACKEND):
                    rollback_attempted = True
                    rollback_success = FailbackService.rollback_to_gcp()
            except Exception as rollback_error:
                rollback_attempted = True
                rollback_success = False
                print(f"Emergency GCP rollback error: {rollback_error}")

            return {
                "success": False,
                "message": f"Failback aborted: {error}",
                "rollback_attempted": rollback_attempted,
                "rollback_success": rollback_success
            }
