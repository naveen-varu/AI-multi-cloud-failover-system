# Flask application factory will be implemented on Day 2.
from flask import Flask

from app.config import DevelopmentConfig
from app.extensions import db, migrate


def create_app():

    app = Flask(__name__)

    app.config.from_object(
        DevelopmentConfig
    )

    db.init_app(app)

    migrate.init_app(
        app,
        db
    )


    @app.route("/")
    def home():

        return {
            "project":
            "AI-Driven Multi-Cloud High Availability and Automatic Failover System",

            "status":
            "running",
        }


    return app