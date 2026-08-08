from flask import Blueprint, jsonify

from app.services.monitoring_service import MonitoringService


health_bp = Blueprint(
    "health",
    __name__
)


@health_bp.route(
    "/nodes/<int:node_id>/health",
    methods=["GET"]
)
def check_node_health(node_id):

    status = MonitoringService.evaluate_node(
        node_id
    )

    if status is None:

        return jsonify({
            "error": "Node or health metrics not found"
        }), 404

    return jsonify({
        "node_id": node_id,
        "status": status
    })