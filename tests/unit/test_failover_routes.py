from dotenv import dotenv_values
from app import create_app


def test_execute_failover_api(monkeypatch):

    app = create_app()
    client = app.test_client()

    def fake_execute_failover(node_id):
        return {
            "success": True,
            "failed_node_id": node_id,
            "backup_node_id": 1,
            "provider": "GCP",
            "message": "Traffic switched successfully"
        }

    monkeypatch.setattr(
        "app.api.failover_routes.FailoverService.execute_failover",
        fake_execute_failover
    )

    api_key = dotenv_values(".env").get("FAILOVER_API_KEY")
    assert api_key, "FAILOVER_API_KEY is missing from .env"

    response = client.post(
        "/api/failover/execute/2",
        headers={"X-API-Key": api_key}
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["failed_node_id"] == 2
    assert data["backup_node_id"] == 1
    assert data["provider"] == "GCP"
