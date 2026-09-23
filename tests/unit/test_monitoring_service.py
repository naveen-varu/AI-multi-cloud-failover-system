from types import SimpleNamespace

from app import create_app
from app.services.monitoring_service import MonitoringService


def test_failed_node_triggers_failover(monkeypatch):

    app = create_app()

    failed_node = SimpleNamespace(
        id=1,
        status="ACTIVE"
    )

    metric = SimpleNamespace(
        node_id=1,
        cpu_usage=95,
        memory_usage=50,
        disk_usage=50,
        response_time=100,
        created_at=None
    )

    with app.app_context():

        monkeypatch.setattr(
            "app.services.monitoring_service.CloudNode.query",
            SimpleNamespace(
                get=lambda node_id: failed_node
            )
        )

        class FakeHealthMetricQuery:

            def filter_by(self, **kwargs):
                return self

            def order_by(self, *args):
                return self

            def first(self):
                return metric

        monkeypatch.setattr(
            "app.services.monitoring_service.HealthMetric.query",
            FakeHealthMetricQuery()
        )

        monkeypatch.setattr(
            "app.services.monitoring_service.EventLogService.log_event",
            lambda **kwargs: None
        )

        failover_called = {"value": False}

        def fake_failover(node_id):
            failover_called["value"] = True
            return {
                "success": True,
                "backup_node_id": 2
            }

        monkeypatch.setattr(
            "app.services.monitoring_service.FailoverService.execute_failover",
            fake_failover
        )

        result = MonitoringService.evaluate_node(1)

    assert result["status"] == "FAILED"
    assert failover_called["value"] is True