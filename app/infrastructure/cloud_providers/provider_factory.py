from app.infrastructure.cloud_providers.aws_provider import AWSProvider
from app.infrastructure.cloud_providers.azure_provider import AzureProvider


class ProviderFactory:

    @staticmethod
    def get_provider(provider_name):

        provider_name = provider_name.upper()

        if provider_name == "AWS":
            return AWSProvider()

        if provider_name == "AZURE":
            return AzureProvider()

        raise ValueError(
            f"Unsupported cloud provider: {provider_name}"
        )