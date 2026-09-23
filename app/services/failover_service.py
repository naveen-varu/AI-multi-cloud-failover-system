from app.models.node_model import CloudNode
from app.infrastructure.cloud_providers.provider_factory import ProviderFactory
from app.extensions import db
from app.models.event_model import FailoverEvent


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

        return nodes


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

        backup_node = FailoverService.select_backup_node(
            failed_node_id
        )

        if backup_node is None:
            return {
                "success": False,
                "message": "No healthy backup node available"
            }

        provider = ProviderFactory.get_provider(
            backup_node.provider
        )

        result = provider.start_node(backup_node)

        if not result["success"]:
            return {
                "success": False,
                "message": "Failed to start backup node",
                "backup_node_id": backup_node.id
            }

        traffic_result = provider.switch_traffic(
            backup_node
        )

        if traffic_result["success"]:

            event = FailoverEvent(
                node_id=failed_node_id,
                event_type="AUTOMATIC_FAILOVER",
                reason="Primary node failure detected",
                previous_status="FAILED",
                new_status="FAILOVER_COMPLETED"
            )

            db.session.add(event)
            db.session.commit()

        return {
            "success": traffic_result["success"],
            "failed_node_id": failed_node_id,
            "backup_node_id": backup_node.id,
            "provider": backup_node.provider,
            "message": traffic_result["message"]
        }