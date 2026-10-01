console.log("Dashboard JavaScript loaded");


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


loadMetrics();
loadFailoverEvents();

setInterval(() => {
    loadMetrics();
    loadFailoverEvents();
}, 30000);
