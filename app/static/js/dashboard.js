console.log("Dashboard JavaScript loaded");


async function loadNodeStatus() {
    try {
        const response = await fetch("/api/nodes/1/health");
        const health = await response.json();

        const awsStatus = document.getElementById("aws-status");
        const aiStatus = document.getElementById("ai-status");

        awsStatus.textContent = health.status;
        aiStatus.textContent = health.ai_prediction;

        awsStatus.className =
            "status " + health.status.toLowerCase();

        aiStatus.className =
            "status " + health.ai_prediction.toLowerCase();

    } catch (error) {
        console.error("Failed to load node status:", error);
    }
}


async function loadBackupStatus() {
    try {
        const response = await fetch("/api/nodes");
        const nodes = await response.json();

        const backup = nodes.find(node => node.id === 2);

        if (!backup) {
            return;
        }

        const backupStatus = document.getElementById("backup-status");

        backupStatus.textContent = backup.status;

        backupStatus.className =
            "status " + backup.status.toLowerCase();

    } catch (error) {
        console.error("Failed to load backup status:", error);
    }
}


async function loadMetrics() {
    try {
        const response = await fetch("/api/metrics");
        const metrics = await response.json();

        if (!metrics.length) {
            return;
        }

        const latest = metrics[metrics.length - 1];

        document.getElementById("cpu").textContent = latest.cpu;
        document.getElementById("memory").textContent = latest.memory;
        document.getElementById("disk").textContent = latest.disk;
        document.getElementById("response").textContent = latest.response_time;

    } catch (error) {
        console.error("Failed to load metrics:", error);
    }
}


async function loadFailoverEvents() {
    try {
        const response = await fetch("/api/failover/events");
        const events = await response.json();

        const container = document.getElementById("events");

        if (!events.length) {
            container.innerHTML = "<p>No failover events recorded.</p>";
            return;
        }

        container.innerHTML = "";

        events.slice(0, 10).forEach(event => {

            const eventCard = document.createElement("div");
            eventCard.className = "event";

            eventCard.innerHTML = `
                <div class="event-header">
                    <strong>${event.event_type}</strong>
                    <span>${event.new_status}</span>
                </div>

                <p>${event.reason}</p>

                <small>
                    ${event.previous_status} → ${event.new_status}
                </small>
            `;

            container.appendChild(eventCard);
        });

    } catch (error) {
        console.error("Failed to load failover events:", error);
    }
}


loadNodeStatus();
loadBackupStatus();
loadMetrics();
loadFailoverEvents();

setInterval(() => {
    loadNodeStatus();
    loadBackupStatus();
    loadMetrics();
    loadFailoverEvents();
}, 30000);
