from flask import Blueprint, jsonify

from app.models.node_model import CloudNode
from app.models.event_model import FailoverEvent
from app.services.failover_service import FailoverService
from app.infrastructure.cloud_providers.provider_factory import ProviderFactory


failover_bp = Blueprint("failover", __name__)


@failover_bp.route("/failover/events", methods=["GET"])
def get_failover_events():

    events = (
        FailoverEvent.query
        .order_by(FailoverEvent.created_at.desc())
        .all()
    )

    result = []

    for event in events:
        result.append({
            "id": event.id,
            "node_id": event.node_id,
            "event_type": event.event_type,
            "reason": event.reason,
            "previous_status": event.previous_status,
            "new_status": event.new_status,
            "created_at": event.created_at.isoformat()
        })

    return jsonify(result)


@failover_bp.route("/failover/decision/<int:node_id>", methods=["GET"])
def get_failover_decision(node_id):

    from flask import request

    primary = CloudNode.query.get(node_id)

    if primary is None:
        return jsonify({
            "decision": "NODE_NOT_FOUND",
            "failed_node_id": node_id
        }), 404

    simulate_failure = (
        request.args.get("simulate_failure", "").lower() == "true"
    )

    if simulate_failure and primary.provider.upper() != "AWS":
        return jsonify({
            "decision": "SIMULATION_NOT_SUPPORTED",
            "message": "Failure simulation is currently supported for AWS only."
        }), 400

    try:
        provider = ProviderFactory.get_provider(primary.provider)
        health = provider.get_health(primary)

        if simulate_failure:
            health = {
                **health,
                "status": "UNHEALTHY",
                "endpoint_healthy": False,
                "simulation": "AWS failure simulated; real AWS instance untouched"
            }
            primary_healthy = False
        else:
            cloud_status = str(
                health.get("status", "UNKNOWN")
            ).upper()

            primary_healthy = cloud_status == "RUNNING"

            if primary.provider.upper() == "AWS":
                primary_healthy = (
                    primary_healthy
                    and str(health.get("system_status", "")).lower() == "ok"
                    and str(health.get("instance_status", "")).lower() == "ok"
                    and health.get("endpoint_healthy") is True
                )

    except Exception as error:
        return jsonify({
            "failed_node_id": node_id,
            "decision": "HEALTH_CHECK_FAILED",
            "message": str(error)
        }), 503

    if primary_healthy:
        return jsonify({
            "failed_node_id": node_id,
            "decision": "NO_FAILOVER_REQUIRED",
            "primary_health": health
        })

    backup = FailoverService.select_backup_node(node_id)

    if backup is None:
        return jsonify({
            "failed_node_id": node_id,
            "decision": "NO_BACKUP_AVAILABLE",
            "primary_health": health,
            "simulation": simulate_failure
        })

    return jsonify({
        "failed_node_id": node_id,
        "decision": "FAILOVER_REQUIRED",
        "primary_health": health,
        "backup_node": {
            "id": backup.id,
            "name": backup.name,
            "provider": backup.provider,
            "region": backup.region,
            "status": backup.status
        },
        "simulation": simulate_failure,
        "message": (
            "Simulation only. No cloud resources or traffic were changed."
            if simulate_failure else "Failover decision generated."
        )
    })


@failover_bp.route("/failover/execute/<int:node_id>", methods=["POST"])
def execute_failover(node_id):

    result = FailoverService.execute_failover(node_id)

    if not result["success"]:
        return jsonify(result), 503

    return jsonify(result), 200
