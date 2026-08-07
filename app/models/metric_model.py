from datetime import datetime

from app.extensions import db


class HealthMetric(db.Model):

    __tablename__ = "health_metrics"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    node_id = db.Column(
        db.Integer,
        db.ForeignKey("cloud_nodes.id"),
        nullable=False
    )


    cpu_usage = db.Column(
        db.Float,
        nullable=False
    )


    memory_usage = db.Column(
        db.Float,
        nullable=False
    )


    disk_usage = db.Column(
        db.Float,
        nullable=False
    )


    response_time = db.Column(
        db.Float,
        nullable=False
    )


    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )