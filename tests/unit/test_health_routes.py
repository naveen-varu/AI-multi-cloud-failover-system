from app.extensions import db
from app.models.node_model import CloudNode
from app.models.metric_model import HealthMetric


def test_health_api_returns_ai_prediction(app, client, monkeypatch):
    with app.app_context():
        node = CloudNode(
            name="GCP Backup",
            provider="GCP",
            region="asia-south1",
            status="ACTIVE"
        )
        db.session.add(node)
        db.session.commit()

        metric = HealthMetric(
            node_id=node.id,
            cpu_usage=20,
            memory_usage=30,
            disk_usage=40,
            response_time=100
        )
        db.session.add(metric)
        db.session.commit()

        node_id = node.id

    class FakeProvider:
        def get_health(self, node):
            return {"status": "RUNNING"}

    monkeypatch.setattr(
        "app.api.health_routes.ProviderFactory.get_provider",
        lambda provider_name: FakeProvider()
    )

    monkeypatch.setattr(
        "app.api.health_routes.AIPredictionService.predict_metric",
        lambda metric: "FAILED"
    )

    response = client.get(f"/api/nodes/{node_id}/health")

    assert response.status_code == 200

    data = response.get_json()
    assert data["node_id"] == node_id
    assert data["status"] == "ACTIVE"
    assert data["ai_prediction"] == "FAILED"
    assert data["metrics_available"] is True
