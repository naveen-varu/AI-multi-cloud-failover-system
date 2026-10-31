from types import SimpleNamespace

from app.extensions import db
from app.models.node_model import CloudNode
from app.models.event_model import FailoverEvent
from app.services.failover_service import FailoverService


def create_failed_node():
    node = CloudNode(
        name="AWS Primary",
        provider="AWS",
        region="ap-south-1",
        status="FAILED"
    )
    db.session.add(node)
    db.session.commit()
    return node


def create_backup_node():
    return SimpleNamespace(
        id=2,
        name="GCP Backup",
        provider="GCP"
    )


class FakeProvider:

    def get_health(self, node):
        return {"status": "RUNNING"}

    def start_node(self, node):
        return {"success": True}

    def switch_traffic(self, node):
        return {
            "success": True,
            "message": "Traffic switched successfully"
        }


def test_execute_failover(app, monkeypatch):
    with app.app_context():
        failed_node = create_failed_node()
        backup_node = create_backup_node()

        monkeypatch.setattr(
            FailoverService,
            "select_backup_node",
            lambda node_id: backup_node
        )

        monkeypatch.setattr(
            "app.services.failover_service.ProviderFactory.get_provider",
            lambda provider_name: FakeProvider()
        )

        monkeypatch.setattr(
            "app.services.failover_service.send_telegram_notification",
            lambda message: True
        )

        result = FailoverService.execute_failover(failed_node.id)

        assert result["success"] is True
        assert result["failed_node_id"] == failed_node.id
        assert result["backup_node_id"] == 2
        assert result["provider"] == "GCP"


def test_execute_failover_without_backup(app):
    with app.app_context():
        failed_node = create_failed_node()

        from app.services.failover_service import FailoverService

        result = FailoverService.execute_failover(failed_node.id)

        assert result["success"] is False
        assert result["message"] == "No healthy backup node available"


def test_execute_failover_records_event(app, monkeypatch):
    with app.app_context():
        failed_node = create_failed_node()
        backup_node = create_backup_node()

        monkeypatch.setattr(
            FailoverService,
            "select_backup_node",
            lambda node_id: backup_node
        )

        monkeypatch.setattr(
            "app.services.failover_service.ProviderFactory.get_provider",
            lambda provider_name: FakeProvider()
        )

        monkeypatch.setattr(
            "app.services.failover_service.send_telegram_notification",
            lambda message: True
        )

        result = FailoverService.execute_failover(failed_node.id)

        assert result["success"] is True

        event = FailoverEvent.query.filter_by(
            node_id=failed_node.id,
            event_type="AUTOMATIC_FAILOVER"
        ).first()

        assert event is not None
        assert event.new_status == "FAILOVER_COMPLETED"
