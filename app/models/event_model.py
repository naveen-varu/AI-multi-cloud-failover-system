from datetime import datetime

from app.extensions import db


class FailoverEvent(db.Model):

    __tablename__ = "failover_events"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    node_id = db.Column(
        db.Integer,
        db.ForeignKey("cloud_nodes.id"),
        nullable=False
    )

    event_type = db.Column(
        db.String(50),
        nullable=False
    )

    reason = db.Column(
        db.String(255),
        nullable=False
    )

    previous_status = db.Column(
        db.String(20),
        nullable=True
    )

    new_status = db.Column(
        db.String(20),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )