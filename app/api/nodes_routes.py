from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models.node_model import CloudNode


nodes_bp = Blueprint(
    "nodes",
    __name__
)


@nodes_bp.route("/nodes", methods=["POST"])
def create_node():

    data = request.json


    node = CloudNode(
        name=data["name"],
        provider=data["provider"],
        region=data["region"]
    )


    db.session.add(node)

    db.session.commit()


    return jsonify({
        "message": "Cloud node created",
        "id": node.id
    })


@nodes_bp.route("/nodes", methods=["GET"])
def get_nodes():

    nodes = CloudNode.query.all()


    result = []

    for node in nodes:

        result.append({
            "id": node.id,
            "name": node.name,
            "provider": node.provider,
            "region": node.region,
            "status": node.status
        })


    return jsonify(result)