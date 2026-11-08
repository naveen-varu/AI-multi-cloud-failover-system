from flask import Blueprint, jsonify

from app.models.node_model import CloudNode
from app.models.metric_model import HealthMetric
from app.infrastructure.cloud_providers.provider_factory import ProviderFactory
from app.services.ai_prediction_service import AIPredictionService


health_bp = Blueprint("health", __name__)


@health_bp.route("/nodes/<int:node_id>/health", methods=["GET"])
def check_node_health(node_id):

    node = CloudNode.query.get(node_id)

    if node is None:
        return jsonify({"error": "Cloud node not found"}), 404

    try:
        provider = ProviderFactory.get_provider(node.provider)
        cloud_health = provider.get_health(node)
    except Exception as error:
        return jsonify({
            "node_id": node.id,
            "provider": node.provider,
            "status": "ERROR",
            "message": str(error),
            "ai_prediction": None
        }), 502

    raw_status = str(cloud_health.get("status", "UNKNOWN")).upper()

    if raw_status == "RUNNING":
        if node.provider.upper() == "AWS":
            system_status = str(
                cloud_health.get("system_status", "UNKNOWN")
            ).lower()
            instance_status = str(
                cloud_health.get("instance_status", "UNKNOWN")
            ).lower()

            if system_status == "impaired" or instance_status == "impaired":
                status = "FAILED"
            elif system_status == "ok" and instance_status == "ok":
                status = "ACTIVE"
            else:
                status = "WARNING"
        else:
            status = "ACTIVE"

    elif raw_status in ("STOPPED", "TERMINATED"):
        status = "INACTIVE"
    elif raw_status in ("STOPPING", "PENDING", "STARTING"):
        status = "WARNING"
    else:
        status = raw_status

    metric = (
        HealthMetric.query
        .filter_by(node_id=node.id)
        .order_by(HealthMetric.created_at.desc())
        .first()
    )

    # Preserve infrastructure health separately from resource health.
    infrastructure_status = status
    resource_status = str(node.status or "UNKNOWN").upper()

    # Combine both statuses without hiding infrastructure failures.
    if infrastructure_status in ("ACTIVE", "WARNING"):
        if resource_status == "FAILED":
            status = "FAILED"
        elif infrastructure_status == "WARNING" or resource_status == "WARNING":
            status = "WARNING"
        else:
            status = "ACTIVE"

    ai_prediction = None

    if metric is not None:
        try:
            ai_prediction = AIPredictionService.predict_metric(metric)
        except Exception as error:
            ai_prediction = "Prediction unavailable"
            print(f"AI prediction error for node {node.id}: {error}")

    return jsonify({
        "node_id": node.id,
        "node_name": node.name,
        "provider": node.provider,
        "region": node.region,
        "instance_id": node.instance_id,
        "status": status,
        "infrastructure_status": infrastructure_status,
        "resource_status": resource_status,
        "cloud_health": cloud_health,
        "ai_prediction": ai_prediction,
        "metrics_available": metric is not None
    })
