
import hmac
import os

from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.metric_model import HealthMetric
from app.models.node_model import CloudNode
from app.services.monitoring_service import MonitoringService

metrics_bp = Blueprint("metrics", __name__)


def authorize_metrics_request():
    expected_key = os.getenv("FAILOVER_API_KEY")
    provided_key = request.headers.get("X-API-Key", "")

    if not expected_key or not hmac.compare_digest(
        provided_key, expected_key
    ):
        return False

    return True


@metrics_bp.route("/metrics", methods=["POST"])
def create_metric():

    if not authorize_metrics_request():
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"message": "Valid JSON body required"}), 400

    required = [
        "node_id",
        "cpu_usage",
        "memory_usage",
        "disk_usage",
        "response_time"
    ]

    if any(key not in data for key in required):
        return jsonify({"message": "Missing required metric fields"}), 400

    try:
        node_id = int(data["node_id"])
        cpu = float(data["cpu_usage"])
        memory = float(data["memory_usage"])
        disk = float(data["disk_usage"])
        response_time = float(data["response_time"])
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid metric values"}), 400

    import math

    values = [cpu, memory, disk, response_time]

    if not all(math.isfinite(value) for value in values):
        return jsonify({"message": "Metric values must be finite"}), 400

    if (
        node_id <= 0
        or not 0 <= cpu <= 100
        or not 0 <= memory <= 100
        or not 0 <= disk <= 100
        or response_time < 0
    ):
        return jsonify({"message": "Metric values outside valid ranges"}), 400

    if db.session.get(CloudNode, node_id) is None:
        return jsonify({"message": "Cloud node not found"}), 404

    metric = HealthMetric(
        node_id=node_id,
        cpu_usage=cpu,
        memory_usage=memory,
        disk_usage=disk,
        response_time=response_time
    )

    try:
        db.session.add(metric)
        db.session.commit()

        monitoring_result = MonitoringService.evaluate_node(node_id)

        return jsonify({
            "message": "Health metric stored",
            "id": metric.id,
            "monitoring": monitoring_result
        }), 201

    except Exception:
        db.session.rollback()
        raise


@metrics_bp.route("/metrics", methods=["GET"])
def get_metrics():

    metrics = HealthMetric.query.order_by(
        HealthMetric.created_at.asc(),
        HealthMetric.id.asc()
    ).all()

    result = []

    for metric in metrics:
        result.append({
            "node_id": metric.node_id,
            "cpu": metric.cpu_usage,
            "memory": metric.memory_usage,
            "disk": metric.disk_usage,
            "response_time": metric.response_time
        })

    return jsonify(result)
