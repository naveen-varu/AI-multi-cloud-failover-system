from types import SimpleNamespace

from app.infrastructure.cloud_providers.provider_factory import ProviderFactory


def test_aws_provider():
    provider = ProviderFactory.get_provider("AWS")
    assert provider.__class__.__name__ == "AWSProvider"


def test_gcp_provider():
    provider = ProviderFactory.get_provider("GCP")
    assert provider.__class__.__name__ == "GCPProvider"


def test_unsupported_provider():
    try:
        ProviderFactory.get_provider("Google")
        assert False, "Expected ValueError for unsupported provider"
    except ValueError:
        pass


def test_aws_region():
    provider = ProviderFactory.get_provider("AWS")
    assert provider.client.region == "ap-south-1"


def test_aws_health_without_instance_id():
    provider = ProviderFactory.get_provider("AWS")
    node = SimpleNamespace(id=1, instance_id=None)

    result = provider.get_health(node)

    assert result["status"] == "UNKNOWN"


def test_gcp_health_without_instance_id():
    provider = ProviderFactory.get_provider("GCP")
    node = SimpleNamespace(id=2, instance_id=None)

    result = provider.get_health(node)

    assert result["status"] == "UNKNOWN"
    assert result["endpoint_healthy"] is False


def test_gcp_health(monkeypatch):
    provider = ProviderFactory.get_provider("GCP")

    node = SimpleNamespace(
        id=2,
        instance_id="gcp-backup-node",
        region="asia-south1-b"
    )

    monkeypatch.setattr(
        provider.client,
        "get",
        lambda **kwargs: SimpleNamespace(status="RUNNING")
    )

    monkeypatch.setattr(
        "app.infrastructure.cloud_providers.gcp_provider.requests.get",
        lambda *args, **kwargs: SimpleNamespace(
            status_code=200,
            json=lambda: {"status": "healthy"}
        )
    )

    result = provider.get_health(node)

    assert result["status"] == "RUNNING"
    assert result["endpoint_healthy"] is True


def test_aws_switch_traffic_successfully_verifies_route(monkeypatch):
    provider = ProviderFactory.get_provider("AWS")
    node = SimpleNamespace(
        id=2,
        provider="AWS",
        instance_id=provider.PRIMARY_INSTANCE_ID
    )

    monkeypatch.setattr(
        "app.infrastructure.cloud_providers.aws_provider.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(stdout="Traffic switched")
    )
    monkeypatch.setattr(
        "app.infrastructure.cloud_providers.aws_provider.requests.get",
        lambda *args, **kwargs: SimpleNamespace(
            status_code=200,
            headers={"X-Active-Backend": "3.110.224.29:5001"}
        )
    )

    result = provider.switch_traffic(node)

    assert result["success"] is True
    assert result["active_backend"] == "3.110.224.29:5001"


def test_aws_switch_traffic_fails_when_route_verification_fails(monkeypatch):
    provider = ProviderFactory.get_provider("AWS")
    node = SimpleNamespace(
        id=2,
        provider="AWS",
        instance_id=provider.PRIMARY_INSTANCE_ID
    )

    monkeypatch.setattr(
        "app.infrastructure.cloud_providers.aws_provider.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(stdout="Traffic switched")
    )
    monkeypatch.setattr(
        "app.infrastructure.cloud_providers.aws_provider.requests.get",
        lambda *args, **kwargs: SimpleNamespace(
            status_code=200,
            headers={"X-Active-Backend": "127.0.0.1:5001"}
        )
    )

    result = provider.switch_traffic(node)

    assert result["success"] is False
    assert "route verification failed" in result["message"]
    assert result["active_backend"] == "127.0.0.1:5001"


def test_gcp_switch_traffic_successfully_verifies_route(monkeypatch):
    provider = ProviderFactory.get_provider("GCP")
    node = SimpleNamespace(
        id=1,
        provider="GCP",
        instance_id="gcp-backup-node"
    )

    responses = iter([
        SimpleNamespace(
            status_code=200,
            headers={"X-Active-Backend": "3.110.224.29:5001"}
        ),
        SimpleNamespace(
            status_code=200,
            headers={"X-Active-Backend": "127.0.0.1:5001"}
        )
    ])

    monkeypatch.setattr(
        "app.infrastructure.cloud_providers.gcp_provider.requests.get",
        lambda *args, **kwargs: next(responses)
    )

    monkeypatch.setattr(
        "app.infrastructure.cloud_providers.gcp_provider.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(stdout="Traffic switched")
    )

    result = provider.switch_traffic(node)

    assert result["success"] is True
    assert result["active_backend"] == "127.0.0.1:5001"


def test_gcp_switch_rejects_non_200_aws_route(monkeypatch):
    provider = ProviderFactory.get_provider("GCP")
    node = SimpleNamespace(
        id=1,
        provider="GCP",
        instance_id="gcp-backup-node"
    )

    monkeypatch.setattr(
        "app.infrastructure.cloud_providers.gcp_provider.requests.get",
        lambda *args, **kwargs: SimpleNamespace(
            status_code=503,
            headers={"X-Active-Backend": "3.110.224.29:5001"}
        )
    )

    switch_called = {"value": False}

    def fake_switch(*args, **kwargs):
        switch_called["value"] = True
        return SimpleNamespace(stdout="Unexpected switch")

    monkeypatch.setattr(
        "app.infrastructure.cloud_providers.gcp_provider.subprocess.run",
        fake_switch
    )

    result = provider.switch_traffic(node)

    assert result["success"] is False
    assert "AWS primary route could not be verified" in result["message"]
    assert switch_called["value"] is False
