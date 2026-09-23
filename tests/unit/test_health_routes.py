from app import create_app


def test_health_api_returns_ai_prediction(monkeypatch):

    app = create_app()
    client = app.test_client()

    def fake_evaluate_node(node_id):
        return {
            "status": "FAILED",
            "ai_prediction": "FAILED"
        }

    monkeypatch.setattr(
        "app.api.health_routes.MonitoringService.evaluate_node",
        fake_evaluate_node
    )

    response = client.get(
        "/api/nodes/1/health"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["node_id"] == 1
    assert data["status"] == "FAILED"
    assert data["ai_prediction"] == "FAILED"