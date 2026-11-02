from app.models.node_model import CloudNode
from app.infrastructure.cloud_providers.provider_factory import ProviderFactory
from app.infrastructure.cloud_providers.aws_provider import AWSProvider
from app.extensions import db
from app.models.event_model import FailoverEvent
from app.services.notification_service import send_telegram_notification


class FailoverService:

    @staticmethod
    def get_healthy_backup_nodes(failed_node_id):

        nodes = (
            CloudNode.query
            .filter(
                CloudNode.id != failed_node_id,
                CloudNode.provider == "GCP",
                CloudNode.status == "ACTIVE"
            )
            .all()
        )

        healthy_nodes = []

        for node in nodes:
            try:
                provider = ProviderFactory.get_provider("GCP")
                health = provider.get_health(node)

                cloud_status = str(
                    health.get("status", "UNKNOWN")
                ).upper()

                endpoint_healthy = health.get("endpoint_healthy") is True

                if cloud_status == "RUNNING" and endpoint_healthy:
                    healthy_nodes.append(node)

            except Exception as error:
                print(
                    f"GCP backup health check failed for node {node.id}: {error}"
                )

        return healthy_nodes


    @staticmethod
    def select_backup_node(failed_node_id):

        backup_nodes = (
            FailoverService
            .get_healthy_backup_nodes(
                failed_node_id
            )
        )

        if not backup_nodes:
            return None

        return backup_nodes[0]
    

    @staticmethod
    def execute_failover(failed_node_id):

        failed_node = db.session.get(CloudNode, failed_node_id)
        if failed_node is None:
            return {"success": False, "message": "Failed node not found"}

        if (
            failed_node.provider != "AWS"
            or failed_node.instance_id != AWSProvider.PRIMARY_INSTANCE_ID
        ):
            return {
                "success": False,
                "message": "Failover is restricted to the configured AWS primary node"
            }

        backup_node = FailoverService.select_backup_node(failed_node_id)

        if backup_node is None:
            return {
                "success": False,
                "message": "No healthy backup node available"
            }

        provider = ProviderFactory.get_provider(backup_node.provider)

        def is_healthy(health):
            status = str(health.get("status", "UNKNOWN")).upper()
            endpoint_healthy = health.get("endpoint_healthy") is True

            return status == "RUNNING" and endpoint_healthy

        try:
            health = provider.get_health(backup_node)
            if not is_healthy(health):
                return {
                    "success": False,
                    "backup_node_id": backup_node.id,
                    "message": (
                        "GCP backup is not running and application-healthy. "
                        "No instance start or traffic-switch action was taken."
                    ),
                    "cloud_health": health
                }

            traffic_result = provider.switch_traffic(backup_node)
            traffic_success = bool(traffic_result.get("success"))

            event = FailoverEvent(
                node_id=failed_node_id,
                event_type="AUTOMATIC_FAILOVER",
                reason=(
                    "Primary node failure detected; traffic routing succeeded"
                    if traffic_success else
                    "Backup node prepared, but traffic routing failed: "
                    + str(traffic_result.get("message", "Unknown reason"))
                ),
                previous_status="FAILED",
                new_status=(
                    "FAILOVER_COMPLETED" if traffic_success
                    else "FAILOVER_INCOMPLETE"
                )
            )
            event_logged = True
            event_log_error = None

            try:
                db.session.add(event)
                db.session.commit()
            except Exception as logging_error:
                db.session.rollback()
                event_logged = False
                event_log_error = str(logging_error)
                print(
                    f"Traffic result: {traffic_success}. "
                    f"Failover event could not be recorded: {logging_error}"
                )

            if traffic_success:
                try:
                    notification_sent = send_telegram_notification(
                        f"Automatic failover completed.\n"
                        f"Failed node: {failed_node_id}\n"
                        f"Backup node: {backup_node.name}"
                    )
                    print(
                        f"Failover Telegram notification sent: {notification_sent}"
                    )
                except Exception as notification_error:
                    print(
                        f"Failover succeeded, but Telegram notification failed: "
                        f"{notification_error}"
                    )

            return {
                "success": traffic_success,
                "failed_node_id": failed_node_id,
                "backup_node_id": backup_node.id,
                "provider": backup_node.provider,
                "message": traffic_result.get("message", "No routing message returned"),
                "traffic_result": traffic_result,
                "event_logged": event_logged,
                "event_log_error": event_log_error
            }

        except Exception as error:
            db.session.rollback()
            return {
                "success": False,
                "backup_node_id": backup_node.id,
                "message": f"Failover aborted due to an error: {error}"
            }
