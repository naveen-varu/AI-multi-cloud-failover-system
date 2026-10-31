import boto3

from app.config import DevelopmentConfig


class CloudConfigService:

    @staticmethod
    def get_status():
        credentials_available = bool(
            boto3.Session().get_credentials()
        )

        return {
            "aws": {
                "configured": credentials_available,
                "region": DevelopmentConfig.AWS_REGION
            },
            "gcp": {
                "configured": True,
                "project": DevelopmentConfig.GCP_PROJECT_ID
            }
        }
