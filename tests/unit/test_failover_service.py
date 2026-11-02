from types import SimpleNamespace

from app.extensions import db
from app.models.node_model import CloudNode
from app.models.event_model import FailoverEvent
from app.services.failover_service import FailoverService


def create_failed_node():
    node = CloudNode(
        name="AWS Primary",
        provider="AWS",
        instance_id="i-01a4f91dd0308e2c6",
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
        return {
            "status": "RUNNING",
            "endpoint_healthy": True
        }

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


def test_execute_failover_rejects_wrong_aws_instance(app, monkeypatch):
    with app.app_context():
        failed_node = create_failed_node()
        failed_node.instance_id = "i-invalid-instance"
        db.session.commit()

        backup_selection_called = {"value": False}

        def unexpected_backup_selection(node_id):
            backup_selection_called["value"] = True
            return create_backup_node()

        monkeypatch.setattr(
            FailoverService,
            "select_backup_node",
            unexpected_backup_selection
        )

        result = FailoverService.execute_failover(failed_node.id)

        assert result["success"] is False
        assert "restricted to the configured AWS primary" in result["message"]
        assert backup_selection_called["value"] is False


def test_successful_failover_when_event_logging_fails(app, monkeypatch):
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

        def fail_commit():
            raise RuntimeError("Simulated database logging failure")

        monkeypatch.setattr(db.session, "commit", fail_commit)

        result = FailoverService.execute_failover(failed_node.id)

        assert result["success"] is True
        assert result["event_logged"] is False
        assert "Simulated database logging failure" in result["event_log_error"]
