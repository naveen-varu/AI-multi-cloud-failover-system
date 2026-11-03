from flask import current_app
from app.extensions import db
from app.models.node_model import CloudNode
from app.models.metric_model import HealthMetric
from app.services.event_log_service import EventLogService
from app.services.ai_prediction_service import AIPredictionService
from app.services.failover_service import FailoverService
from app.services.failback_service import FailbackService
from app.services.notification_service import send_telegram_notification

class MonitoringService:

    CPU_WARNING = 70
    CPU_FAILED = 90

    MEMORY_WARNING = 75
    MEMORY_FAILED = 90

    DISK_WARNING = 80
    DISK_FAILED = 95

    RESPONSE_WARNING = 500
    RESPONSE_FAILED = 2000

    @staticmethod
    def evaluate_metric(metric):

        failed = (
            metric.cpu_usage >= MonitoringService.CPU_FAILED
            or metric.memory_usage >= MonitoringService.MEMORY_FAILED
            or metric.disk_usage >= MonitoringService.DISK_FAILED
            or metric.response_time >= MonitoringService.RESPONSE_FAILED
        )

        if failed:
            return "FAILED"

        warning = (
            metric.cpu_usage >= MonitoringService.CPU_WARNING
            or metric.memory_usage >= MonitoringService.MEMORY_WARNING
            or metric.disk_usage >= MonitoringService.DISK_WARNING
            or metric.response_time >= MonitoringService.RESPONSE_WARNING
        )

        if warning:
            return "WARNING"

        return "ACTIVE"


    @staticmethod
    def evaluate_node(node_id):
        node = CloudNode.query.get(node_id)

        if node is None:
            return None

        metric = (
            HealthMetric.query
            .filter_by(node_id=node_id)
            .order_by(HealthMetric.created_at.desc())
            .first()
        )

        if metric is None:
            return None

        status = MonitoringService.evaluate_metric(metric)
        ai_prediction = AIPredictionService.predict_metric(metric)
        previous_status = node.status
        node.status = status

        failover_result = None
        failback_result = None
        notification_error = None

        if status == "FAILED" and previous_status != "FAILED":
            EventLogService.log_event(
                node_id=node.id,
                event_type="NODE_FAILURE",
                reason=(
                    f"Health check failed: "
                    f"CPU={metric.cpu_usage}%, "
                    f"Memory={metric.memory_usage}%, "
                    f"Disk={metric.disk_usage}%, "
                    f"Response={metric.response_time}ms"
                ),
                previous_status=previous_status,
                new_status=status
            )

            try:
                send_telegram_notification(
                    f"🔴 {node.name} node failed.\\n"
                    f"CPU: {metric.cpu_usage}%\\n"
                    f"Memory: {metric.memory_usage}%\\n"
                    f"Disk: {metric.disk_usage}%\\n"
                    f"Response: {metric.response_time} ms"
                )
            except Exception as exc:
                notification_error = str(exc)
                current_app.logger.exception(
                    "Failure notification raised an unexpected error"
                )

            if (
                node.provider.upper() == "AWS"
                and node.instance_id == "i-01a4f91dd0308e2c6"
                and current_app.config.get("AUTO_FAILOVER_ENABLED", False)
            ):
                failover_result = FailoverService.execute_failover(node.id)

        # Attempt failback whenever AWS metrics are healthy.
        # FailbackService independently verifies both cloud nodes and the active route.
        if (
            status == "ACTIVE"
            and node.provider.upper() == "AWS"
            and current_app.config.get("AUTO_FAILBACK_ENABLED", False)
        ):
            failback_result = FailbackService.execute_failback()

        db.session.commit()

        return {
            "status": status,
            "ai_prediction": ai_prediction,
            "failover_result": failover_result,
            "failback_result": failback_result,
            "notification_error": notification_error
        }
