from types import SimpleNamespace

from app.services.failover_service import FailoverService
from app import create_app


def test_execute_failover(monkeypatch):

    app = create_app()

    failed_node = SimpleNamespace(
        id=1,
        provider="AWS"
    )

    backup_node = SimpleNamespace(
        id=2,
        provider="Azure"
    )

    monkeypatch.setattr(
        FailoverService,
        "select_backup_node",
        lambda failed_node_id: backup_node
    )

    class FakeProvider:

        def start_node(self, node):
            return {
                "success": True
            }

        def switch_traffic(self, node):
            return {
                "success": True,
                "message": "Traffic switched successfully"
            }

    monkeypatch.setattr(
        "app.services.failover_service.ProviderFactory.get_provider",
        lambda provider_name: FakeProvider()
    )

    with app.app_context():

        monkeypatch.setattr(
            "app.services.failover_service.FailoverEvent.query",
            SimpleNamespace(
                filter_by=lambda **kwargs: SimpleNamespace(
                    order_by=lambda *args: SimpleNamespace(
                        first=lambda: None
                    )
                )
            )
        )

        result = FailoverService.execute_failover(
            failed_node.id
        )

    assert result["success"] is True
    assert result["failed_node_id"] == 1
    assert result["backup_node_id"] == 2
    assert result["provider"] == "Azure"
def test_execute_failover_without_backup(monkeypatch):

    app = create_app()

    monkeypatch.setattr(
        FailoverService,
        "select_backup_node",
        lambda failed_node_id: None
    )

    with app.app_context():

        monkeypatch.setattr(
            "app.services.failover_service.FailoverEvent.query",
            SimpleNamespace(
                filter_by=lambda **kwargs: SimpleNamespace(
                    order_by=lambda *args: SimpleNamespace(
                        first=lambda: None
                    )
                )
            )
        )

        result = FailoverService.execute_failover(1)

    assert result["success"] is False
    assert result["message"] == "No healthy backup node available"


def test_execute_failover_records_event(monkeypatch):

    app = create_app()

    class FakeProvider:

        def start_node(self, node):
            return {
                "success": True
            }

        def switch_traffic(self, node):
            return {
                "success": True,
                "message": "Traffic switched successfully"
            }

    backup_node = SimpleNamespace(
        id=2,
        provider="Azure"
    )

    monkeypatch.setattr(
        FailoverService,
        "select_backup_node",
        lambda failed_node_id: backup_node
    )

    monkeypatch.setattr(
        "app.services.failover_service.ProviderFactory.get_provider",
        lambda provider_name: FakeProvider()
    )

    with app.app_context():

        result = FailoverService.execute_failover(1)

        assert result["success"] is True

        from app.models.event_model import FailoverEvent

        event = (
            FailoverEvent.query
            .filter_by(
                node_id=1,
                event_type="AUTOMATIC_FAILOVER"
            )
            .order_by(FailoverEvent.id.desc())
            .first()
        )

        assert event is not None
        assert event.node_id == 1
        assert event.event_type == "AUTOMATIC_FAILOVER"