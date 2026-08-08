from flask import Blueprint, jsonify

from app.models.event_model import FailoverEvent


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