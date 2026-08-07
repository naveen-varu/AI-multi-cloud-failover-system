from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.metric_model import HealthMetric


metrics_bp = Blueprint(
    "metrics",
    __name__
)


@metrics_bp.route("/metrics", methods=["POST"])
def create_metric():

    data = request.json


    metric = HealthMetric(

        node_id=data["node_id"],

        cpu_usage=data["cpu_usage"],

        memory_usage=data["memory_usage"],

        disk_usage=data["disk_usage"],

        response_time=data["response_time"]

    )


    db.session.add(metric)

    db.session.commit()


    return jsonify({
        "message": "Health metric stored",
        "id": metric.id
    })



@metrics_bp.route("/metrics", methods=["GET"])
def get_metrics():

    metrics = HealthMetric.query.all()


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