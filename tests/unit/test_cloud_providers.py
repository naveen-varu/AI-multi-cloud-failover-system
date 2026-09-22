from app.infrastructure.cloud_providers.provider_factory import (
    ProviderFactory
)
from types import SimpleNamespace


def test_aws_provider():

    provider = ProviderFactory.get_provider("AWS")

    assert provider.__class__.__name__ == "AWSProvider"


def test_azure_provider():

    provider = ProviderFactory.get_provider("Azure")

    assert provider.__class__.__name__ == "AzureProvider"


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

def test_azure_health_without_instance_id():

    provider = ProviderFactory.get_provider("Azure")

    node = SimpleNamespace(
        id=1,
        instance_id=None
    )

    result = provider.get_health(node)

    assert result["status"] == "UNKNOWN"

def test_azure_health_running_vm(monkeypatch):

    provider = ProviderFactory.get_provider("Azure")

    class FakeStatus:
        code = "PowerState/running"

    class FakeInstanceView:
        statuses = [FakeStatus()]

    class FakeVMs:
        def instance_view(self, resource_group_name, vm_name):
            return FakeInstanceView()

    class FakeCompute:
        virtual_machines = FakeVMs()

    def fake_get_compute_client():
        return FakeCompute()

    provider.client.resource_group = "test-resource-group"

    monkeypatch.setattr(
        provider.client,
        "get_compute_client",
        fake_get_compute_client
    )

    node = SimpleNamespace(
        id=1,
        instance_id="test-vm"
    )

    result = provider.get_health(node)

    assert result["status"] == "running"

def test_azure_health_deallocated_vm(monkeypatch):

    provider = ProviderFactory.get_provider("Azure")

    class FakeStatus:
        code = "PowerState/deallocated"

    class FakeInstanceView:
        statuses = [FakeStatus()]

    class FakeVMs:
        def instance_view(self, resource_group_name, vm_name):
            return FakeInstanceView()

    class FakeCompute:
        virtual_machines = FakeVMs()

    provider.client.resource_group = "test-resource-group"

    monkeypatch.setattr(
        provider.client,
        "get_compute_client",
        lambda: FakeCompute()
    )

    node = SimpleNamespace(
        id=1,
        instance_id="test-vm"
    )

    result = provider.get_health(node)

    assert result["status"] == "deallocated"