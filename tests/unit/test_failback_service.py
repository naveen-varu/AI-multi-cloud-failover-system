from app.extensions import db
from app.models.node_model import CloudNode
from app.models.event_model import FailoverEvent
from app.services.failback_service import FailbackService


def create_nodes():
    aws_node = CloudNode(
        name="AWS Primary",
        provider="AWS",
        instance_id="i-01a4f91dd0308e2c6",
        region="ap-south-1",
        status="FAILED"
    )

    gcp_node = CloudNode(
        name="GCP Backup",
        provider="GCP",
        instance_id="gcp-backup-node",
        region="asia-south1-b",
        status="ACTIVE"
    )

    db.session.add_all([aws_node, gcp_node])
    db.session.commit()

    return aws_node, gcp_node


class FakeAWSProvider:

    def get_health(self, node):
        return {
            "status": "RUNNING",
            "system_status": "ok",
            "instance_status": "ok",
            "endpoint_healthy": True
        }

    def switch_traffic(self, node):
        return {
            "success": True,
            "message": "AWS traffic restored"
        }


class FakeGCPProvider:

    def get_health(self, node):
        return {
            "status": "RUNNING",
            "endpoint_healthy": True
        }


def test_successful_failback(app, monkeypatch):
    with app.app_context():
        aws_node, gcp_node = create_nodes()

        monkeypatch.setattr(
            FailbackService,
            "verify_route",
            staticmethod(
                lambda backend: backend in (
                    FailbackService.GCP_BACKEND,
                    FailbackService.AWS_BACKEND
                )
            )
        )

        monkeypatch.setattr(
            "app.services.failback_service.ProviderFactory.get_provider",
            lambda provider: (
                FakeAWSProvider()
                if provider == "AWS"
                else FakeGCPProvider()
            )
        )

        monkeypatch.setattr(
            "app.services.failback_service.send_telegram_notification",
            lambda message: True
        )

        result = FailbackService.execute_failback()

        assert result["success"] is True
        assert result["aws_node_id"] == aws_node.id
        assert result["gcp_node_id"] == gcp_node.id

        event = FailoverEvent.query.filter_by(
            node_id=aws_node.id,
            event_type="AUTOMATIC_FAILBACK"
        ).first()

        assert event is not None
        assert event.new_status == "ACTIVE"
def test_failback_cancelled_when_aws_unhealthy(app, monkeypatch):
    with app.app_context():
        aws_node, gcp_node = create_nodes()

        monkeypatch.setattr(
            FailbackService,
            "verify_route",
            staticmethod(lambda backend: backend == FailbackService.GCP_BACKEND)
        )

        class UnhealthyAWSProvider:
            def get_health(self, node):
                return {
                    "status": "STOPPED",
                    "system_status": "ok",
                    "instance_status": "ok",
                    "endpoint_healthy": False
                }

        monkeypatch.setattr(
            "app.services.failback_service.ProviderFactory.get_provider",
            lambda provider: (
                UnhealthyAWSProvider()
                if provider == "AWS"
                else FakeGCPProvider()
            )
        )

        result = FailbackService.execute_failback()

        assert result["success"] is False
        assert "not fully healthy" in result["message"]
def test_failback_cancelled_when_gcp_is_not_active(app, monkeypatch):
    with app.app_context():
        create_nodes()

        monkeypatch.setattr(
            FailbackService,
            "verify_route",
            staticmethod(lambda backend: False)
        )

        result = FailbackService.execute_failback()

        assert result["success"] is False
        assert "GCP is not verified" in result["message"]
def test_failback_attempts_gcp_rollback_when_aws_switch_fails(app, monkeypatch):
    with app.app_context():
        create_nodes()

        class FailedAWSProvider:
            def get_health(self, node):
                return {
                    "status": "RUNNING",
                    "system_status": "ok",
                    "instance_status": "ok",
                    "endpoint_healthy": True
                }

            def switch_traffic(self, node):
                return {
                    "success": False,
                    "message": "Simulated AWS switching failure"
                }

        monkeypatch.setattr(
            FailbackService,
            "verify_route",
            staticmethod(lambda backend: backend == FailbackService.GCP_BACKEND)
        )

        monkeypatch.setattr(
            "app.services.failback_service.ProviderFactory.get_provider",
            lambda provider: (
                FailedAWSProvider()
                if provider == "AWS"
                else FakeGCPProvider()
            )
        )

        rollback_called = {"value": False}

        def fake_rollback():
            rollback_called["value"] = True
            return True

        monkeypatch.setattr(
            FailbackService,
            "rollback_to_gcp",
            staticmethod(fake_rollback)
        )

        result = FailbackService.execute_failback()

        assert result["success"] is False
        assert result["rollback_success"] is True
        assert rollback_called["value"] is True
