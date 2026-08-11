from app.config import DevelopmentConfig


class CloudConfigService:

    @staticmethod
    def get_status():
        return {
            "aws": {
                "configured": bool(
                    DevelopmentConfig.AWS_ACCESS_KEY_ID
                    and DevelopmentConfig.AWS_SECRET_ACCESS_KEY
                ),
                "region": DevelopmentConfig.AWS_REGION
            },
            "azure": {
                "configured": bool(
                    DevelopmentConfig.AZURE_SUBSCRIPTION_ID
                    and DevelopmentConfig.AZURE_TENANT_ID
                    and DevelopmentConfig.AZURE_CLIENT_ID
                    and DevelopmentConfig.AZURE_CLIENT_SECRET
                )
            }
        }