from flask import Blueprint, jsonify, render_template
from app.models.event_model import FailoverEvent
from app.models.node_model import CloudNode


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

    result = []

    for event in events:
        node = CloudNode.query.get(event.node_id)

        provider = node.provider if node else "UNKNOWN"
        node_name = node.name if node else "Unknown Node"

        role = {
            "AWS": "PRIMARY",
            "GCP": "BACKUP"
        }.get(str(provider).upper(), "UNKNOWN")

        result.append({
            "id": event.id,
            "node_id": event.node_id,
            "cloud_provider": provider,
            "node_name": node_name,
            "node_role": role,
            "event_type": event.event_type,
            "reason": event.reason,
            "previous_status": event.previous_status,
            "new_status": event.new_status,
            "created_at": event.created_at.isoformat()
        })

    return jsonify(result)
