from app.infrastructure.cloud_providers.aws_provider import AWSProvider
from app.infrastructure.cloud_providers.vyuhstack_provider import VyuhStackProvider
from app.infrastructure.cloud_providers.gcp_provider import GCPProvider


class ProviderFactory:

    @staticmethod
    def get_provider(provider_name):

        provider_name = provider_name.upper()

        if provider_name == "AWS":
            return AWSProvider("ap-south-1")

        if provider_name == "VYUHSTACK":
            return VyuhStackProvider()

        if provider_name == "GCP":
            return GCPProvider()

        raise ValueError(
            f"Unsupported cloud provider: {provider_name}"
        )