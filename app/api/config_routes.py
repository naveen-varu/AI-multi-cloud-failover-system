from flask import Blueprint, jsonify

from app.services.cloud_config_service import CloudConfigService


config_bp = Blueprint(
    "config",
    __name__
)


@config_bp.route("/config/cloud", methods=["GET"])
def cloud_config_status():

    status = CloudConfigService.get_status()

    return jsonify(status)