from app import create_app
from app.services.notification_service import send_telegram_notification

app = create_app()


if __name__ == "__main__":
    message = (
        "🚀 MULTI-CLOUD FAILOVER SYSTEM\n\n"
        "Flask application is starting.\n"
        "Primary: AWS\n"
        "Backup: GCP\n"
        f"Automatic Failover: {'ENABLED' if app.config.get('AUTO_FAILOVER_ENABLED') else 'DISABLED'}\n"
        "Status: STARTING"
    )

    send_telegram_notification(message)

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        use_reloader=False
    )
