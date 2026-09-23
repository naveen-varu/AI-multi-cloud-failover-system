from flask import Blueprint, jsonify

from app.models.event_model import FailoverEvent
from app.services.failover_service import FailoverService


failover_bp = Blueprint(
    "failover",
    __name__
)


@failover_bp.route(
    "/failover/events",
    methods=["GET"]
)
def get_failover_events():

    events = (
        FailoverEvent.query
        .order_by(
            FailoverEvent.created_at.desc()
        )
        .all()
    )

    result = []

    for event in events:

        result.append({

            "id": event.id,

            "node_id": event.node_id,

            "event_type": event.event_type,

            "reason": event.reason,

            "previous_status":
                event.previous_status,

            "new_status":
                event.new_status,

            "created_at":
                event.created_at.isoformat()
        })

    return jsonify(result)

@failover_bp.route(
    "/failover/decision/<int:node_id>",
    methods=["GET"]
)
def get_failover_decision(node_id):

    backup = (
        FailoverService
        .select_backup_node(node_id)
    )

    if backup is None:

        return jsonify({
            "failed_node_id": node_id,
            "decision": "NO_BACKUP_AVAILABLE"
        })

    return jsonify({
        "failed_node_id": node_id,
        "decision": "FAILOVER_REQUIRED",
        "backup_node": {
            "id": backup.id,
            "name": backup.name,
            "provider": backup.provider,
            "region": backup.region,
            "status": backup.status
        }
    })
@failover_bp.route(
    "/failover/execute/<int:node_id>",
    methods=["POST"]
)
def execute_failover(node_id):

    result = FailoverService.execute_failover(
        node_id
    )

    if not result["success"]:
        return jsonify(result), 503

    return jsonify(result), 200