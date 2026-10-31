from app.models.node_model import CloudNode
from app.infrastructure.cloud_providers.provider_factory import ProviderFactory
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
                CloudNode.status == "ACTIVE"
            )
            .all()
        )

        healthy_nodes = []

        for node in nodes:
            try:
                provider = ProviderFactory.get_provider(node.provider)
                health = provider.get_health(node)

                cloud_status = str(
                    health.get("status", "UNKNOWN")
                ).upper()

                if cloud_status in ("STOPPED", "TERMINATED"):
                    healthy_nodes.append(node)
                    continue

                if cloud_status != "RUNNING":
                    continue

                if node.provider.upper() == "AWS":
                    system_status = str(
                        health.get("system_status", "UNKNOWN")
                    ).lower()
                    instance_status = str(
                        health.get("instance_status", "UNKNOWN")
                    ).lower()

                    if system_status != "ok" or instance_status != "ok":
                        continue

                healthy_nodes.append(node)

            except Exception as error:
                print(
                    f"Live health check failed for node {node.id}: {error}"
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
        import time

        failed_node = db.session.get(CloudNode, failed_node_id)
        if failed_node is None:
            return {"success": False, "message": "Failed node not found"}

        previous_failover = (
            FailoverEvent.query
            .filter_by(
                node_id=failed_node_id,
                event_type="AUTOMATIC_FAILOVER",
                new_status="FAILOVER_COMPLETED"
            )
            .order_by(FailoverEvent.id.desc())
            .first()
        )

        if previous_failover:
            return {
                "success": True,
                "failed_node_id": failed_node_id,
                "backup_node_id": None,
                "provider": None,
                "message": "Failover already completed for this node"
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
            if status != "RUNNING":
                return False

            if backup_node.provider.upper() == "AWS":
                return (
                    str(health.get("system_status", "")).lower() == "ok"
                    and str(health.get("instance_status", "")).lower() == "ok"
                )

            return True

        try:
            health = provider.get_health(backup_node)
            cloud_status = str(health.get("status", "UNKNOWN")).upper()

            if not is_healthy(health):
                if cloud_status not in ("STOPPED", "TERMINATED"):
                    return {
                        "success": False,
                        "backup_node_id": backup_node.id,
                        "message": (
                            "Backup node is not healthy or is in a transitional "
                            "state. No start or traffic-switch action was taken."
                        ),
                        "cloud_health": health
                    }

                start_result = provider.start_node(backup_node)
                if not start_result.get("success"):
                    return {
                        "success": False,
                        "backup_node_id": backup_node.id,
                        "message": "Failed to start backup node",
                        "details": start_result
                    }

                ready = False
                for _ in range(12):
                    time.sleep(5)
                    health = provider.get_health(backup_node)
                    if is_healthy(health):
                        ready = True
                        break

                if not ready:
                    return {
                        "success": False,
                        "backup_node_id": backup_node.id,
                        "message": "Backup node did not become healthy within 60 seconds",
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
            db.session.add(event)
            db.session.commit()

            if traffic_success:
                notification_sent = send_telegram_notification(
                    f"Automatic failover completed.\n"
                    f"Failed node: {failed_node_id}\n"
                    f"Backup node: {backup_node.name}"
                )
                print(f"Failover Telegram notification sent: {notification_sent}")

            return {
                "success": traffic_success,
                "failed_node_id": failed_node_id,
                "backup_node_id": backup_node.id,
                "provider": backup_node.provider,
                "message": traffic_result.get("message", "No routing message returned")
            }

        except Exception as error:
            db.session.rollback()
            return {
                "success": False,
                "backup_node_id": backup_node.id,
                "message": f"Failover aborted due to an error: {error}"
            }
