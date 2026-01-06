document.addEventListener("DOMContentLoaded", () => {
    loadSettings();
});

async function loadSettings() {
    try {
        const res = await fetch("/config");
        if (!res.ok) throw new Error("Failed to fetch config");
        const c = await res.json();

        // Populate fields
        if (document.getElementById("tg_token")) document.getElementById("tg_token").value = c.telegram_token || "";
        if (document.getElementById("tg_chat")) document.getElementById("tg_chat").value = c.telegram_chat_id || "";
        if (document.getElementById("enable_notif")) document.getElementById("enable_notif").checked = c.enable_notifications || false;

        // Update visual badge
        updateStatusBadge(c.telegram_token && c.telegram_chat_id && c.enable_notifications);

    } catch (e) {
        showToast("Error loading settings: " + e.message, "error");
    }
}

async function saveSettings() {
    // Collect data
    const token = document.getElementById("tg_token").value;
    const chat = document.getElementById("tg_chat").value;
    const enabled = document.getElementById("enable_notif").checked;

    // Visual Loading State
    const btn = document.querySelector(".primary-btn");
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Saving...';

    try {
        const payload = {
            telegram_token: token,
            telegram_chat_id: chat,
            enable_notifications: enabled
        };

        const res = await fetch("/config", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            showToast("Settings saved successfully!", "success");
            updateStatusBadge(token && chat && enabled);
        } else {
            throw new Error(data.message || "Unknown error");
        }

    } catch (e) {
        showToast("Failed to save: " + e.message, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;

        // Remove focus from button
        btn.blur();
    }
}

function updateStatusBadge(isActive) {
    const badge = document.getElementById("tg-status-badge");
    if (!badge) return;

    if (isActive) {
        badge.classList.add("connected");
        badge.innerHTML = '<i class="fa-solid fa-check-circle"></i> Active';
    } else {
        badge.classList.remove("connected");
        badge.innerHTML = '<i class="fa-solid fa-circle-pause"></i> Inactive';
    }
}

async function testNotification() {
    const btn = document.querySelector("button[onclick='testNotification()']");
    const originalContent = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';

    try {
        // First save any pending changes so we test the NEW config
        await saveSettings();

        const res = await fetch("/api/test_notification", { method: "POST" });
        const data = await res.json();

        if (res.ok) {
            showToast("Test message sent!", "success");
        } else {
            showToast("Failed: " + data.error, "error");
        }
    } catch (e) {
        showToast("Error: " + e.message, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    // Smart Error Handling
    if (type === "error" && message.includes("Failed to fetch")) {
        message += "<br><br><small><b>💡 Remedy:</b> Check if the Python Bot Server is running.</small>";
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let icon = "fa-circle-info";
    if (type === "success") icon = "fa-circle-check";
    if (type === "error") icon = "fa-circle-xmark";

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = "slideInRight 0.4s reverse forwards";
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}

async function updatePassword() {
    const curr = document.getElementById("curr_pass").value;
    const newP = document.getElementById("new_pass").value;

    if (!curr || !newP) {
        showToast("Please fill in both fields", "error");
        return;
    }

    const btn = document.querySelector("button[onclick='updatePassword()']");
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Updating...';

    try {
        const res = await fetch("/api/change_password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ current_password: curr, new_password: newP })
        });
        const data = await res.json();

        if (res.ok) {
            showToast("Password updated successfully!", "success");
            // Clear inputs
            document.getElementById("curr_pass").value = "";
            document.getElementById("new_pass").value = "";
        } else {
            showToast(data.error || "Failed to update", "error");
        }
    } catch (e) {
        showToast("Error: " + e.message, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}
