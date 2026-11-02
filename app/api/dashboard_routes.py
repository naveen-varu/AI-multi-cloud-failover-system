from flask import Blueprint, jsonify, render_template
from app.models.event_model import FailoverEvent


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@dashboard_bp.route("/dashboard/events")
def dashboard_events():
    events = (
        FailoverEvent.query
        .order_by(FailoverEvent.created_at.desc())
        .limit(10)
        .all()
    )

    return jsonify([
        {
            "id": event.id,
            "node_id": event.node_id,
            "event_type": event.event_type,
            "reason": event.reason,
            "previous_status": event.previous_status,
            "new_status": event.new_status,
            "created_at": event.created_at.isoformat()
        }
        for event in events
    ])
