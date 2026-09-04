// Main Client JS for Savings Goal Tracker Agent

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatMessages = document.getElementById("chat-messages");
    const resetBtn = document.getElementById("reset-btn");
    const traceToggle = document.getElementById("trace-toggle");
    const traceContent = document.getElementById("trace-content");

    // Fetch initial progress on page load
    fetchProgress();

    // Toggle Trace Log Drawer
    traceToggle.addEventListener("click", () => {
        const traceBody = document.getElementById("trace-body");
        const chevron = document.getElementById("trace-chevron");
        if (traceBody.style.display === "none" || !traceBody.style.display) {
            traceBody.style.display = "block";
            chevron.style.transform = "rotate(180deg)";
        } else {
            traceBody.style.display = "none";
            chevron.style.transform = "rotate(0deg)";
        }
    });

    // Form Submit Handler
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = userInput.value.strip ? userInput.value.strip() : userInput.value.trim();
        if (!text) return;

        // Render user message
        appendMessage("user", text);
        userInput.value = "";

        // Send to API
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });

            const data = await res.json();
            if (res.ok) {
                appendMessage("agent", data.final_answer);
                if (data.trace_log) {
                    traceContent.textContent = data.trace_log;
                }
                if (data.progress) {
                    updateDashboard(data.progress);
                }
            } else {
                appendMessage("agent", "⚠️ " + (data.error || "Failed to process request."));
            }
        } catch (err) {
            appendMessage("agent", "⚠️ Connection error. Please check server.");
        }
    });

    // Reset State Handler
    resetBtn.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to reset your savings goal and memory?")) return;

        try {
            const res = await fetch("/api/reset", { method: "POST" });
            if (res.ok) {
                appendMessage("agent", "🔄 Goal memory has been reset.");
                fetchProgress();
                traceContent.textContent = "Memory reset.";
            }
        } catch (err) {
            alert("Failed to reset memory.");
        }
    });
});

// Helper: Quick Message Chips
function sendQuickMessage(msg) {
    const userInput = document.getElementById("user-input");
    userInput.value = msg;
    document.getElementById("chat-form").dispatchEvent(new Event("submit"));
}

// Append Message to Chat Container
function appendMessage(role, text) {
    const chatMessages = document.getElementById("chat-messages");

    const msgDiv = document.createElement("div");
    msgDiv.className = `message message-${role}`;

    const avatarDiv = document.createElement("div");
    avatarDiv.className = "message-avatar";
    avatarDiv.innerHTML = role === "user" ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";
    contentDiv.innerHTML = `<p>${text.replace(/\n/g, "<br>")}</p>`;

    msgDiv.appendChild(avatarDiv);
    msgDiv.appendChild(contentDiv);

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Fetch Goal Progress Metrics
async function fetchProgress() {
    try {
        const res = await fetch("/api/progress");
        if (res.ok) {
            const data = await res.json();
            updateDashboard(data);
        }
    } catch (err) {
        console.error("Error fetching progress:", err);
    }
}

// Update Dashboard UI Cards & Progress Bar
function updateDashboard(p) {
    const sym = p.currency_symbol || "₹";

    document.getElementById("stat-target").textContent = p.target ? `${sym}${p.target.toLocaleString()}` : `${sym}0`;
    document.getElementById("stat-saved").textContent = p.saved ? `${sym}${p.saved.toLocaleString()}` : `${sym}0`;
    document.getElementById("stat-remaining").textContent = p.remaining !== undefined ? `${sym}${p.remaining.toLocaleString()}` : `${sym}0`;
    document.getElementById("stat-monthly").textContent = p.required_monthly_saving ? `${sym}${p.required_monthly_saving.toLocaleString()} / mo` : `${sym}0 / mo`;

    // Progress Bar
    const pct = p.percentage !== undefined ? p.percentage : 0;
    document.getElementById("progress-percentage").textContent = `${pct}%`;
    document.getElementById("progress-bar").style.width = `${Math.min(100, Math.max(0, pct))}%`;

    // Deadline Tag
    const deadlineTag = document.getElementById("deadline-tag");
    if (p.deadline) {
        deadlineTag.textContent = `Deadline: ${p.deadline}`;
    } else {
        deadlineTag.textContent = "No Deadline Set";
    }

    // Recommendation Box
    if (p.recommendation) {
        document.getElementById("recommendation-text").innerHTML = `<i class="fa-solid fa-lightbulb"></i> ${p.recommendation}`;
    }

    // Status Pill
    const badge = document.getElementById("status-badge");
    const statusText = document.getElementById("status-text");

    const status = p.status || "NOT_STARTED";
    badge.className = `status-pill status-${status.toLowerCase()}`;
    statusText.textContent = status.replace(/_/g, " ");
}
