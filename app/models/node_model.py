from datetime import datetime

from app.extensions import db


class CloudNode(db.Model):

    __tablename__ = "cloud_nodes"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    name = db.Column(
        db.String(100),
        nullable=False
    )


    provider = db.Column(
        db.String(50),
        nullable=False
    )


    region = db.Column(
        db.String(100),
        nullable=False
    )


    status = db.Column(
        db.String(50),
        default="UNKNOWN"
    )


    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    metrics = db.relationship(
        "HealthMetric",
        backref="node",
        lazy=True
    )

    def __repr__(self):
        return f"<CloudNode {self.name}>"