from app.models.node_model import CloudNode


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