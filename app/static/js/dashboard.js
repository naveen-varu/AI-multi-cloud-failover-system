console.log("Multi-Cloud Dashboard Loaded");
let simulationActive = false;
async function loadCloudStatus(nodeId, elementId, provider) {
    const element = document.getElementById(elementId);

    try {
        const response = await fetch(`/api/nodes/${nodeId}/health`);

        if (!response.ok) {
            throw new Error(`Health API returned ${response.status}`);
        }

        const health = await response.json();

        element.textContent = health.status;
        element.className = "status " + health.status.toLowerCase();

        return health;

    } catch (error) {
        console.error(`${provider} health check failed:`, error);
        element.textContent = "Health unavailable";
        element.className = "status unknown";
        return null;
    }
}

async function loadCloudStatuses() {
    const aws = await loadCloudStatus(2, "aws-status", "AWS");
    const gcp = await loadCloudStatus(1, "backup-status", "GCP");

    return { aws, gcp };
}

async function loadAIPrediction() {
    const element = document.getElementById("ai-status");

    try {
        const response = await fetch("/api/nodes/1/health");

        if (!response.ok) {
            throw new Error("AI prediction unavailable");
        }

        const data = await response.json();

        element.textContent = data.ai_prediction || "Unavailable";
        element.className =
            "status " + (data.ai_prediction || "unknown").toLowerCase();

    } catch (error) {
        element.textContent = "Unavailable";
        element.className = "status unknown";
        console.error("AI prediction error:", error);
    }
}

async function loadMetrics() {
    try {
        const response = await fetch("/api/metrics");

        if (!response.ok) {
            throw new Error("Metrics API unavailable");
        }

        const metrics = await response.json();

        if (!Array.isArray(metrics) || !metrics.length) return;

        // API returns metrics in ascending timestamp order.
        // Therefore, the last record for each node is its latest metric.
        const latestForNode = (nodeId) => {
            const nodeMetrics = metrics.filter(
                metric => Number(metric.node_id) === nodeId
            );

            return nodeMetrics.length
                ? nodeMetrics[nodeMetrics.length - 1]
                : null;
        };

        const awsLatest = latestForNode(2);
        const gcpLatest = latestForNode(1);

        function updateCloudMetrics(prefix, latest) {
            if (!latest) return;

            document.getElementById(`${prefix}-cpu`).textContent =
                latest.cpu;
            document.getElementById(`${prefix}-memory`).textContent =
                latest.memory;
            document.getElementById(`${prefix}-disk`).textContent =
                latest.disk;
            document.getElementById(`${prefix}-response`).textContent =
                latest.response_time;

            document.getElementById(`${prefix}-metric-time`).textContent =
                "Latest metric received successfully";
        }

        updateCloudMetrics("aws", awsLatest);
        updateCloudMetrics("gcp", gcpLatest);

    } catch (error) {
        console.error("Metrics loading failed:", error);
    }
}

async function loadFailoverEvents() {
    try {
        const response = await fetch("/dashboard/events");

        if (!response.ok) {
            throw new Error("Failover events unavailable");
        }

        const events = await response.json();
        const container = document.getElementById("events");

        if (!events.length) {
            container.textContent = "No failover events recorded.";
            return;
        }

        container.innerHTML = "";

        events.slice(0, 10).forEach(event => {
            const eventCard = document.createElement("div");
            eventCard.className = "event";

            const heading = document.createElement("strong");
            heading.textContent = event.event_type;

            const status = document.createElement("span");
            status.textContent = event.new_status;

            const reason = document.createElement("p");
            reason.textContent = event.reason;

            const transition = document.createElement("small");
            transition.textContent =
                `${event.previous_status} → ${event.new_status}`;

            eventCard.append(heading, status, reason, transition);
            container.appendChild(eventCard);
        });

    } catch (error) {
        console.error("Failover events loading failed:", error);
    }
}

async function refreshDashboard() {
    await loadCloudStatuses();
    await loadAIPrediction();
    await loadMetrics();
    await loadFailoverEvents();
    await loadFailoverDecision();
}

refreshDashboard();

setInterval(refreshDashboard, 30000);
async function loadFailoverDecision() {
    const element = document.getElementById("failover-decision");

    try {
        const simulationQuery = simulationActive ? "?simulate_failure=true" : "";
const response = await fetch(`/api/failover/decision/2${simulationQuery}`);
        if (!response.ok) {
            throw new Error("Failover decision API unavailable");
        }

        const data = await response.json();

        if (data.decision === "NO_FAILOVER_REQUIRED") {
            element.textContent =
                "AWS Primary → GCP Backup | Primary healthy. No failover required.";
        } else if (data.decision === "FAILOVER_REQUIRED") {
            element.textContent =
                "AWS Primary → GCP Backup | Failover required. Backup: " +
                data.backup_node.name;
        } else {
            element.textContent = "Failover decision: " + data.decision;
        }

    } catch (error) {
        console.error("Failover decision error:", error);
        element.textContent = "Unable to retrieve failover decision.";
    }
}

document.getElementById("simulate-failure-btn").addEventListener("click", async () => {
    simulationActive = true;

    document.getElementById("simulation-status").textContent =
        "AWS failure simulation is active (no real resources changed).";
document.getElementById("simulation-status").style.background = "#7f1d1d";
document.getElementById("simulation-status").style.color = "#fca5a5";
    await loadFailoverDecision();
});

document.getElementById("reset-simulation-btn").addEventListener("click", async () => {
    simulationActive = false;

    document.getElementById("simulation-status").textContent =
        "Simulation inactive. Live cloud status restored.";
document.getElementById("simulation-status").style.background = "#14532d";
document.getElementById("simulation-status").style.color = "#4ade80";
    await loadFailoverDecision();
});
