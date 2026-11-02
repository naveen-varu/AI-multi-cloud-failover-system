import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("DIAGNOSTICS_BASE_URL", "http://127.0.0.1:5000")
API_KEY = os.getenv("FAILOVER_API_KEY")

results = []


def record(name, passed, details):
    status = "PASS" if passed else "FAIL"
    results.append((name, status, str(details)))
    print(f"[{status}] {name}: {details}")


def check_api(name, path, headers=None):
    try:
        response = requests.get(
            f"{BASE_URL}{path}",
            headers=headers or {},
            timeout=10
        )
        record(
            name,
            response.status_code == 200,
            f"HTTP {response.status_code}"
        )
    except requests.RequestException as error:
        record(name, False, error)


def check_cloud_health(name, node_id):
    try:
        response = requests.get(
            f"{BASE_URL}/api/nodes/{node_id}/health",
            timeout=30
        )

        if response.status_code != 200:
            record(name, False, f"HTTP {response.status_code}")
            return

        data = response.json()
        cloud = data.get("cloud_health") or {}
        status = str(data.get("status", cloud.get("status", "UNKNOWN"))).upper()
        endpoint_ok = cloud.get("endpoint_healthy") is True

        passed = status in ("ACTIVE", "RUNNING") and endpoint_ok

        record(
            name,
            passed,
            f"Instance status: {status}; application endpoint healthy: {endpoint_ok}"
        )

    except (requests.RequestException, ValueError) as error:
        record(name, False, error)


def send_summary():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("\nTelegram configuration missing; report was not sent.")
        return

    passed = sum(status == "PASS" for _, status, _ in results)
    failed = len(results) - passed

    lines = [
        "🔎 MULTI-CLOUD API DIAGNOSTICS",
        "",
        f"Overall: {'ALL CHECKS PASSED' if failed == 0 else 'ISSUES DETECTED'}",
        f"Passed: {passed} | Failed: {failed}",
        ""
    ]

    for name, status, details in results:
        lines.append(f"{'✅' if status == 'PASS' else '❌'} {name}: {status}")
        lines.append(f"   {details}")

    message = "\n".join(lines)

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10
        )
        response.raise_for_status()
        print("\nTelegram diagnostics summary sent.")
    except requests.RequestException as error:
        print(f"\nTelegram notification failed: {error}")


def main():
    print("Starting read-only API and cloud health diagnostics...\n")

    check_api("Flask application", "/")
    check_api("Nodes API", "/api/nodes")
    check_api("Metrics API", "/api/metrics")
    check_api("Cloud configuration API", "/api/config/cloud")
    check_api("Dashboard events API", "/dashboard/events")

    if API_KEY:
        check_api(
            "Protected failover events API",
            "/api/failover/events",
            {"X-API-Key": API_KEY}
        )
    else:
        record("Protected failover events API", False, "FAILOVER_API_KEY is not configured")

    check_cloud_health("AWS primary health API", 2)
    check_cloud_health("GCP backup health API", 1)

    print("\nSending one diagnostics summary...")
    send_summary()


if __name__ == "__main__":
    main()
