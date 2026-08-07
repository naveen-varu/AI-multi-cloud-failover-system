# Application configuration will be implemented on Day 2.
import os


class BaseConfig:
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "development-secret-key"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///multicloud_ha.db"
    )


class TestingConfig(BaseConfig):

    TESTING = True

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///:memory:"
    )


class ProductionConfig(BaseConfig):

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL"
    )