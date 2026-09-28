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
            "vyuhstack": {
                "configured": True
            }
        }