from app.infrastructure.cloud_providers.provider_factory import (
    ProviderFactory
)


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