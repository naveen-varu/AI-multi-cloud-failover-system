# Flask extensions will be initialized on Day 2.
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()

migrate = Migrate()