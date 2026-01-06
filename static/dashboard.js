let currentSymbol = "ETHUSDT";
let tvWidget = null;

document.addEventListener("DOMContentLoaded", () => {
    // Cross-page navigation handler
    const target = localStorage.getItem('navTarget');
    if (target) {
        localStorage.removeItem('navTarget');
        // Small delay to ensure render
        setTimeout(() => {
            const element = document.getElementById(target);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
                // Optional: Flash highlights
                element.style.animation = "flash-highlight 1s";
            }
        }, 500);
    }

    loadConfig();

    // Top Bar: Refresh
    const refreshBtn = document.getElementById("refresh-btn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", () => {
            const icon = refreshBtn.querySelector("i");
            if (icon) icon.classList.add("fa-spin");

            loadConfig();
            loadBalance();
            loadLogs().then(() => {
                setTimeout(() => {
                    if (icon) icon.classList.remove("fa-spin");
                    showToast("Dashboard Data Refreshed", "success");
                }, 800);
            });
        });
    }

    // Top Bar: Theme Toggle
    // We try to find the moon icon, then get its parent button
    const themeIcon = document.querySelector(".header-actions .fa-moon");
    if (themeIcon && themeIcon.parentElement) {
        themeIcon.parentElement.addEventListener("click", () => {
            document.body.classList.toggle("light-mode");
            const isLight = document.body.classList.contains("light-mode");
            showToast(isLight ? "Light Mode Enabled (Beta)" : "Dark Mode Enabled", "info");
        });
    }

    // Load available symbols
    fetchSymbols();

    // Close dropdown when clicking outside
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".custom-select-wrapper")) {
            document.getElementById("symbol-options").classList.remove("open");
        }
    });

    // Sidebar Navigation
    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            // Mobile: Close sidebar on click
            if (window.innerWidth <= 768) {
                document.querySelector('.sidebar').classList.remove('open');
            }

            const targetId = item.getAttribute("data-target");
            const href = item.getAttribute("href");

            // If it's a real page link (starts with /), let it work naturally
            if (href && href.startsWith("/")) {
                return;
            }

            // Otherwise, if it has a data-target, handle smooth scroll
            if (targetId) {
                e.preventDefault();

                // Update Active State
                navItems.forEach(nav => nav.classList.remove("active"));
                item.classList.add("active");

                // Scroll to Section
                const section = document.getElementById(targetId);
                if (section) {
                    section.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            }
        });
    });

    // Initial Loads
    loadBalance();
    loadLogs();

    // Auto-refresh logs every 10s
    setInterval(loadLogs, 10000);
});

async function loadConfig() {
    const statusEl = document.getElementById("disp-status");
    const modeEl = document.getElementById("disp-mode");
    const symbolEl = document.getElementById("disp-symbol");

    // Safety check
    if (statusEl) statusEl.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

    try {
        const res = await fetch("/config");
        if (!res.ok) throw new Error("Failed to fetch config");
        const c = await res.json();

        // Populate Form (Check existence first to be safe)
        // Populate Form (Check existence first to be safe)
        if (document.getElementById("symbol")) {
            const sym = c.symbol || "ETHUSDT";
            // Check if selectSymbol is available, else fallback
            if (typeof selectSymbol === "function") {
                selectSymbol(sym);
            } else {
                document.getElementById("symbol").value = sym;
            }
        }
        if (document.getElementById("product_type")) {
            document.getElementById("product_type").value = c.product_type || "USDT-FUTURES";
        }
        if (document.getElementById("size")) document.getElementById("size").value = c.buy_size_usdt;
        if (document.getElementById("sell_size")) document.getElementById("sell_size").value = c.sell_size;
        if (document.getElementById("leverage")) document.getElementById("leverage").value = c.leverage;
        if (document.getElementById("enable")) document.getElementById("enable").checked = c.enable_trading;
        if (document.getElementById("dry_run")) document.getElementById("dry_run").checked = c.dry_run;

        // Populate Stats
        if (symbolEl) symbolEl.innerText = c.symbol || "N/A";

        if (statusEl) {
            if (c.enable_trading) {
                statusEl.innerText = "ACTIVE";
                statusEl.style.color = "var(--success)";
            } else {
                statusEl.innerText = "PAUSED";
                statusEl.style.color = "var(--warning)";
            }
        }

        if (modeEl) {
            if (c.dry_run) {
                modeEl.innerText = "DRY RUN";
                modeEl.style.color = "var(--warning)";
            } else {
                modeEl.innerText = "LIVE TRADING";
                modeEl.style.color = "var(--danger)";
            }
        }

        // Init Chart if symbol changed or first run
        if ((currentSymbol !== c.symbol || !tvWidget) && typeof initTradingView === "function") {
            currentSymbol = c.symbol;
            initTradingView(currentSymbol);
        }

    } catch (e) {
        showToast("Error loading config: " + e.message, "error");
        if (statusEl) statusEl.innerText = "Error";
    }
}

async function loadBalance() {
    try {
        const res = await fetch("/api/balance");
        const data = await res.json();

        let balance = "--";

        if (data.data) {
            const usdt = data.data.find(a => a.coin === "USDT");
            if (usdt) {
                balance = parseFloat(usdt.available).toFixed(2);
            } else {
                balance = "0.00";
            }
        }

        const card = document.querySelector(".card.stat-card:nth-child(4) .value");
        if (card) card.innerText = `$ ${balance}`;

    } catch (e) {
        console.error("Balance Load Error", e);
    }
}

async function loadLogs() {
    try {
        const res = await fetch("/api/logs");
        const logs = await res.json();

        const tbody = document.getElementById("trade-log-table");
        if (!tbody) return;

        tbody.innerHTML = "";

        logs.forEach(log => {
            const row = document.createElement("tr");

            // Format Time
            const date = new Date(log.created_at || Date.now());
            const timeStr = date.toLocaleTimeString();

            // Status Badge
            let statusClass = "sim";
            if (log.status === "FILLED") statusClass = "success";
            else if (log.status === "ERROR") statusClass = "error";

            row.innerHTML = `
                <td><small>${timeStr}</small></td>
                <td><b>${log.symbol}</b></td>
                <td><span style="color: ${(log.side && (log.side.includes('buy') || log.side.includes('long'))) ? 'var(--success)' : 'var(--danger)'}">${log.side}</span></td>
                <td><span class="badge ${statusClass}">${log.status}</span></td>
            `;
            tbody.appendChild(row);
        });

    } catch (e) {
        console.error("Logs Load Error", e);
    }
}

async function manualTrade(action) {
    if (!confirm(`Are you sure you want to FORCE ${action.toUpperCase()}?`)) return;

    // Find the button to show loading state
    const btn = document.querySelector(`.action-btn.${action}`);
    const originalContent = btn ? btn.innerHTML : "";
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Executing...`;
    }

    try {
        // Determine correct size input based on side
        let chosenSize = document.getElementById("size").value; // Default to Buy Size

        if (action === 'sell') {
            const sellInput = document.getElementById("sell_size").value;
            // If empty, assume placeholder "ALL", otherwise use value
            chosenSize = sellInput.trim() === "" ? "ALL" : sellInput;
        }

        const payload = {
            side: action === 'buy' ? 'open_long' : 'open_short',
            symbol: document.getElementById("symbol").value,
            size: chosenSize,
            product_type: document.getElementById("product_type") ? document.getElementById("product_type").value : "USDT-FUTURES"
        };

        const res = await fetch("/api/manual_trade", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            let msg = `Manual ${action.toUpperCase()} Executed`;
            if (data.mode === 'DRY') msg += " (Dry Run)";

            showToast(`${msg}: ${data.message}`, "success");
            loadLogs();
            // Refresh balance to show updated funds immediately
            setTimeout(loadBalance, 1000);
        } else {
            showToast(`Trade Failed: ${data.message || data.error}`, "error");
        }

    } catch (e) {
        showToast("Request Failed: " + e.message, "error");
    } finally {
        // Reset button state
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalContent;
        }
    }
}

async function saveConfig() {
    const btn = document.getElementById("save-btn");
    const originalText = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

    try {
        const payload = {
            symbol: document.getElementById("symbol").value,
            product_type: document.getElementById("product_type") ? document.getElementById("product_type").value : "USDT-FUTURES",
            buy_size_usdt: parseFloat(document.getElementById("size").value),
            sell_size: document.getElementById("sell_size").value,
            leverage: parseInt(document.getElementById("leverage").value),
            enable_trading: document.getElementById("enable").checked,
            dry_run: document.getElementById("dry_run").checked
        };

        const res = await fetch("/config", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            showToast("Configuration saved successfully!", "success");
            loadConfig();
        } else {
            throw new Error(data.message || "Unknown error");
        }

    } catch (e) {
        showToast("Failed to save: " + e.message, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function initTradingView(symbol) {
    // Map internal symbol to TradingView format
    const tvSymbol = "BITGET:" + symbol.replace("-", "");

    const container = document.getElementById("tv-chart-container");
    if (!container) return;

    container.innerHTML = "";

    if (typeof TradingView !== 'undefined') {
        new TradingView.widget({
            "autosize": true,
            "symbol": tvSymbol,
            "interval": "15",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "allow_symbol_change": false,
            "container_id": "tv-chart-container",
            "hide_side_toolbar": false
        });
    }
}

function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    // Smart Error Handling
    if (type === "error") {
        if (message.includes("Failed to fetch")) {
            message += "<br><br><small><b>💡 Remedy:</b> Check if the Python Bot Server is running.</small>";
        }
        else if (message.toLowerCase().includes("unknown error")) {
            message += "<br><br><small><b>💡 Remedy:</b> Restart the Bot or Check Supabase Connection Logs.</small>";
        }
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let icon = "fa-circle-info";
    if (type === "success") icon = "fa-circle-check";
    if (type === "error") icon = "fa-circle-xmark";

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000); // Extended time for user to read remedy
}

// --- Custom Symbol Dropdown Logic ---

let symbolsCache = [];

async function fetchSymbols() {
    try {
        const res = await fetch("/api/symbols");
        if (res.ok) {
            symbolsCache = await res.json();
            renderSymbols(symbolsCache);
        }
    } catch (e) {
        console.error("Failed to fetch symbols", e);
    }
}

function renderSymbols(list) {
    const container = document.getElementById("options-list-container");
    if (!container) return;

    container.innerHTML = "";

    if (list.length === 0) {
        container.innerHTML = '<div class="option">No symbols found</div>';
        return;
    }

    list.forEach(s => {
        const div = document.createElement("div");
        div.className = "option";
        // Try to guess coin code for logo (e.g. BTCUSDT -> btc)
        const baseCoin = s.symbol.replace("USDT", "").toLowerCase();

        div.innerHTML = `
            <img src="https://assets.coincap.io/assets/icons/${baseCoin}@2x.png" onerror="this.src='/static/fallback-icon.svg'; this.onerror=null; this.style.opacity=0.5" alt="">
            <span>${s.symbol}</span>
        `;
        div.onclick = () => selectSymbol(s.symbol);
        container.appendChild(div);
    });
}

function toggleSymbolDropdown() {
    const opts = document.getElementById("symbol-options");
    opts.classList.toggle("open");
    if (opts.classList.contains("open")) {
        document.getElementById("symbol-search").focus();
    }
}

function filterSymbols() {
    const query = document.getElementById("symbol-search").value.toLowerCase();
    const filtered = symbolsCache.filter(s => s.symbol.toLowerCase().includes(query));
    renderSymbols(filtered);
}

function selectSymbol(val) {
    if (!val) return;

    // Set hidden input
    const input = document.getElementById("symbol");
    if (input) input.value = val;

    // Update UI
    const textSpan = document.getElementById("selected-text");
    const iconImg = document.getElementById("selected-icon");

    if (textSpan) textSpan.innerText = val;

    // Update Icon
    if (iconImg) {
        const baseCoin = val.replace("USDT", "").toLowerCase();
        // Reset src to force reload if changed
        iconImg.src = `https://assets.coincap.io/assets/icons/${baseCoin}@2x.png`;
        iconImg.style.display = "block";
    }

    // Close Dropdown
    const opts = document.getElementById("symbol-options");
    if (opts) opts.classList.remove("open");
}
