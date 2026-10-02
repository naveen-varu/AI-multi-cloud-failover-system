import os
import requests


def send_telegram_notification(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram configuration missing.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message,
            },
            timeout=10,
        )

        response.raise_for_status()

        print("Telegram notification sent.")
        return True

    except requests.RequestException as exc:
        print(f"Telegram notification failed: {exc}")
        return False