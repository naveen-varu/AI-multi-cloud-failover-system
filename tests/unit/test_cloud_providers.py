from app.infrastructure.cloud_providers.provider_factory import (
    ProviderFactory
)
from types import SimpleNamespace


def test_aws_provider():

    provider = ProviderFactory.get_provider("AWS")

    assert provider.__class__.__name__ == "AWSProvider"


def test_vyuhstack_provider():

    provider = ProviderFactory.get_provider("VyuhStack")

    assert provider.__class__.__name__ == "VyuhStackProvider"


def test_unsupported_provider():

    try:
        ProviderFactory.get_provider("Google")

        assert False

    except ValueError:
        assert True


def test_aws_region():

    provider = ProviderFactory.get_provider("AWS")

    assert provider.client.region == "ap-south-1"


def test_aws_health_without_instance_id():

    provider = ProviderFactory.get_provider("AWS")

    node = SimpleNamespace(
        id=1,
        instance_id=None
    )

    result = provider.get_health(node)

    assert result["status"] == "UNKNOWN"


def test_vyuhstack_health_without_instance_id():

    provider = ProviderFactory.get_provider("VyuhStack")

    node = SimpleNamespace(
        id=2,
        instance_id=None
    )

    result = provider.get_health(node)

    assert result["status"] == "UNKNOWN"


def test_vyuhstack_health():

    provider = ProviderFactory.get_provider("VyuhStack")

    node = SimpleNamespace(
        id=2,
        instance_id="vyuhstack-vm-19055",
        status="ACTIVE"
    )

    result = provider.get_health(node)

    assert result["status"] == "ACTIVE"