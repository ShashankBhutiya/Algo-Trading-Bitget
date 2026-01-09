import os
import secrets
from flask import Flask, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from core.gmx_client import GMXClient
from core.executor import execute_trade
# REPLACE local manager with Supabase manager
from core.supabase_config_manager import supabase_manager 
from core.notifier import telegram_bot
from dotenv import load_dotenv

# Load environment variables (API keys, etc.)
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(16)) # Secure session key
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin") # Default password if not set

# Initialize the GMX Client
client = GMXClient()

@app.before_request
def require_login():
    # Allow static resources, webhook, login page, and health check
    if request.path == '/' or request.path.startswith('/static') or request.path.startswith('/webhook') or request.path == '/login' or request.path == '/api/health':
        return
    
    # If not logged in, redirect to login
    if not session.get('logged_in'):
        # If it's an API call, return 401
        if request.path.startswith('/api') or request.path.startswith('/config'):
             return jsonify({"error": "Unauthorized"}), 401
        return redirect('/login')

def get_auth_password():
    """Get the active password (Supabase > Env > Default)."""
    try:
        cfg = supabase_manager.get_config()
        if cfg.get("dashboard_password"):
            return cfg.get("dashboard_password")
    except:
        pass
    return os.getenv("DASHBOARD_PASSWORD", "admin")

def verify_password_secure(stored, provided):
    """Verify password against stored value (hash or plaintext)."""
    if not stored or not provided:
        return False
    # Try verifying as hash
    try:
        if check_password_hash(stored, provided):
            return True
    except:
        pass
    # Fallback to plaintext comparison (legacy)
    return stored == provided

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('logged_in'):
            return redirect('/dashboard')
        return app.send_static_file('login.html')
    
    # POST
    data = request.json
    stored_pass = get_auth_password()
    
    if data and verify_password_secure(stored_pass, data.get('password')):
        session['logged_in'] = True
        return jsonify({"status": "success", "redirect": "/dashboard"})
    
    return jsonify({"message": "Invalid Password"}), 401

@app.route('/api/change_password', methods=['POST'])
def change_password():
    """Update the dashboard password."""
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    current_input = data.get('current_password')
    new_pass = data.get('new_password')
    
    if not current_input or not new_pass:
        return jsonify({"error": "Missing fields"}), 400
        
    real_current_stored = get_auth_password()
    # Verify current password using the secure helper
    if not verify_password_secure(real_current_stored, current_input):
        return jsonify({"error": "Incorrect current password"}), 401
        
    # Hash the NEW password before storing
    hashed_new = generate_password_hash(new_pass)
    
    # Update in Supabase
    success = supabase_manager.update_config({"dashboard_password": hashed_new})
    if success:
        # Notify Admin via Telegram
        try:
            telegram_bot.send_message("🔒 *Security Alert*\n\nDashboard password has been changed successfully.", test_mode=True)
        except Exception as e:
            print(f"Failed to send password notification: {e}")
            
        return jsonify({"status": "success"})
    else:
        return jsonify({"error": "Failed to save. Ensure DB is updated."}), 500

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/login')

@app.route('/', methods=['GET'])
def health_check():
    cfg = supabase_manager.get_config()
    status = "Active" if cfg.get("enable_trading") else "Paused"
    mode = "Dry Run" if cfg.get("dry_run") else "Live"
    source = "Supabase" if supabase_manager.client else "Local Default"
    return app.send_static_file("index.html")

@app.route('/api/health', methods=['GET'])
def api_health():
    """Return system status as JSON for the landing page."""
    cfg = supabase_manager.get_config()
    return jsonify({
        "status": "Active" if cfg.get("enable_trading") else "Paused",
        "mode": "Dry Run" if cfg.get("dry_run") else "Live",
        "source": "Supabase" if supabase_manager.client else "Local Default"
    })

# --- CONTROL PLANE API (PROXY TO SUPABASE) ---

@app.route("/config", methods=["GET"])
def get_config():
    """Return the current bot configuration from Supabase."""
    return jsonify(supabase_manager.get_config())

@app.route("/config", methods=["PUT"])
def update_bot_config():
    """Update bot configuration parameters in Supabase."""
    data = request.json
    if not data:
        return jsonify({"error": "Invalid payload"}), 400

    # Whitelist allowed keys
    allowed_keys = {
        "symbol",
        "product_type",
        "buy_size_usdt",
        "sell_size",
        "leverage",
        "enable_trading",
        "dry_run",
        "telegram_token",
        "telegram_chat_id",
        "enable_notifications"
    }

    filtered = {k: v for k, v in data.items() if k in allowed_keys}
    
    # Get old config for diff
    old_config = supabase_manager.get_config()
    
    updated = supabase_manager.update_config(filtered)

    if updated:
        # Calculate Diff and Notify
        changes = []
        try:
            for key, new_val in filtered.items():
                old_val = old_config.get(key)
                if str(old_val) != str(new_val):
                    # Mask secrets in notification
                    if "token" in key or "chat" in key:
                        changes.append(f"• *{key}*: `(hidden)` -> `(updated)`")
                    else:
                        changes.append(f"• *{key}*: `{old_val}` -> `{new_val}`")
            
            if changes:
                msg = "⚙️ *Configuration Updated*\n\n" + "\n".join(changes)
                # Use test_mode=True to ensure config alerts go through even if 'enable_notifications' was just toggled
                telegram_bot.send_message(msg, test_mode=True)
        except Exception as e:
            print(f"Error sending config notification: {e}")

        return jsonify({
            "status": "success",
            "updated_config": updated
        })
    else:
         return jsonify({
            "status": "error",
            "message": "Failed to update Supabase"
        }), 500

@app.route("/dashboard")
def dashboard():
    """Serve the dashboard HTML."""
    return app.send_static_file("dashboard.html")

@app.route("/settings")
def settings_page():
    """Serve the settings HTML."""
    return app.send_static_file("settings.html")

# --- DASHBOARD API EXTENSIONS ---

@app.route("/api/balance", methods=["GET"])
def get_balance():
    """Fetch wallet balance from Bitget."""
    try:
        # We can implement Futures balance check too, but let's start with Spot Assets
        # coin = request.args.get("coin") # Optional filter
        assets = client.get_spot_assets()
        if assets:
            return jsonify(assets) # Returns raw Bitget response structure
        return jsonify({"code": "error", "msg": "Failed to fetch assets"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/logs", methods=["GET"])
def get_trade_logs():
    """Fetch trade history from Supabase."""
    try:
        logs = supabase_manager.get_logs(limit=50)
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    """Fetch balance history for PnL chart."""
    try:
        limit = request.args.get("limit", 50)
        history = supabase_manager.get_balance_history(limit=int(limit))
        # Format for chart (reverse chronological usually for frontend? or let frontend reverse?)
        # Supabase returns desc. We probably want asc for charts (oldest to newest).
        return jsonify(history[::-1]) 
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/symbols", methods=["GET"])
def get_symbols_list():
    """Fetch available trading pairs from Bitget."""
    try:
        # Defaults to futures mix, but could accept param
        ptype = request.args.get("product_type", "USDT-FUTURES")
        symbols = client.get_symbols(product_type=ptype)
        
        # Optimize payload size if needed, but returning full list is fine for now
        # Format: [{symbol: 'BTCUSDT', ...}, ...]
        return jsonify(symbols)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/analytics")
def analytics_page():
    return app.send_static_file("analytics.html")

@app.route("/api/snapshot_balance", methods=["POST"])
def snapshot_balance():
    """Manually trigger a balance snapshot with equity valuation."""
    try:
        # Get context to value holdings
        cfg = supabase_manager.get_config()
        symbol = cfg.get("symbol", "ETHUSDT")
        product_type = cfg.get("product_type", "SPOT")
        
        # Get Price
        current_price = 0.0
        try:
            candles = client.get_candles(symbol, limit=1, granularity="1m", productType=product_type)
            if candles and len(candles) > 0:
                current_price = float(candles[0][4]) # Close price
        except:
            pass # Ignore price fetch errors

        assets = client.get_spot_assets()
        # Handle dict response with 'data'
        asset_list = []
        if isinstance(assets, dict):
            asset_list = assets.get('data', [])
        elif isinstance(assets, list):
            asset_list = assets

        if asset_list:
            total_usdt = 0.0
            breakdown = {}
            for asset in asset_list:
                coin = asset.get('coin')
                available = float(asset.get('available', 0))
                # frozen = float(asset.get('frozen', 0)) # Ignored for now
                
                if coin == 'USDT':
                     total_usdt += available
                elif current_price > 0 and coin in symbol:
                     # Valuation for base asset (e.g. ETH in ETHUSDT)
                     total_val = available * current_price
                     total_usdt += total_val
                
                breakdown[coin] = available
            
            supabase_manager.log_balance(total_usdt, breakdown)
            return jsonify({"status": "success"})
        return jsonify({"error": "Failed to fetch assets"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/manual_trade", methods=["POST"])
def manual_trade():
    """Trigger a manual trade from the dashboard."""
    try:
        data = request.json
        side = data.get("side") # buy/sell/open_long etc
        symbol = data.get("symbol")
        size = data.get("size")
        
        if not all([side, symbol, size]):
            return jsonify({"error": "Missing params"}), 400
            
        # Security: Force check config for Dry Run state if not overridden?
        # Or allow dashboard to specify? Let's use config's dry_run default
        cfg = supabase_manager.get_config()
        dry_run = cfg.get("dry_run", True)
        # Prioritize payload product_type, else config, else default
        product_type = data.get("product_type", cfg.get("product_type", "USDT-FUTURES"))
        
        # Execute
        result = execute_trade(
            client=client,
            signal=side,
            symbol=symbol,
            product_type=product_type,
            size=float(size) if size != "ALL" else 0.0, # Handle numeric
            sell_size=size, # Pass literal "ALL" if needed
            dry_run=dry_run
        )
        
        # If result is None (legacy safety), assume dry run success
        if not result:
             return jsonify({"status": "executed", "mode": "DRY" if dry_run else "LIVE", "message": "Command sent"})
             
        status_code = 200 if result.get("success") else 400
        
        return jsonify({
            "status": result.get("status", "UNKNOWN"), 
            "mode": "DRY" if dry_run else "LIVE",
            "message": result.get("message", "No details")
        }), status_code
    except Exception as e:
        print(f"Manual trade error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/test_notification", methods=["POST"])
def api_test_notification():
    """Send a test notification to Telegram."""
    try:
        from core.notifier import telegram_bot
        # Use test_mode=True to bypass the 'enabled' check
        success, msg = telegram_bot.send_message(
            "👋 *Test Alert*\n\nYour Algorithm Bot is connected and ready to send notifications!", 
            test_mode=True
        )
        
        if success:
            return jsonify({"status": "success", "message": msg})
        else:
            return jsonify({"error": msg}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Endpoint to receive TradingView alerts.
    Uses 'core/supabase_config_manager.py' as the authoritative source.
    """
    try:
        # --- DEBUG LOGGING START ---
        print("\n=== INCOMING WEBHOOK ===")
        print(f"Headers: {request.headers}")
        raw_body = request.get_data(as_text=True)
        print(f"Raw Body: {raw_body}")
        # --- DEBUG LOGGING END ---

        data = request.json
        if not data:
            # Fallback: try to parse manual text if content-type was wrong
            import json
            try:
                data = json.loads(raw_body)
            except:
                pass
        
        if not data:
             print("❌ Error: No JSON data found in request")
             return jsonify({"status": "error", "message": "Invalid JSON/No Info"}), 400

        print(f"Parsed Payload: {data}")

        # 1. Load Dynamic Config (From Supabase)
        config = supabase_manager.get_config()

        # 2. Check Global Switch
        if not config.get("enable_trading", True):
            print("Trading is disabled in Supabase config. Ignoring signal.")
            return jsonify({"status": "ignored", "message": "Trading disabled"}), 200

        # 3. Security (Optional)
        env_passphrase = os.getenv("WEBHOOK_PASSPHRASE")
        if env_passphrase and data.get("passphrase") != env_passphrase:
            print("Unauthorized access attempt.")
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        # 4. Extract Parameters
        signal = data.get("signal")
        if not signal:
            return jsonify({"status": "error", "message": "Missing 'signal' field"}), 400

        # Use config defaults
        symbol = data.get("symbol", config.get("symbol", "ETHUSDT"))
        product_type = data.get("product_type", config.get("product_type", "SPOT"))
        
        # Risk / Size Management from Config
        buy_size = float(config.get("buy_size_usdt", 5.0))
        # Prioritize webhook payload for sell_size, else global config
        sell_config = data.get("sell_size", config.get("sell_size", "ALL"))

        trade_size_arg = buy_size
        sell_size_arg = sell_config
        
        dry_run_mode = config.get("dry_run", False)

        execute_trade(
            client=client,
            signal=signal,
            symbol=symbol,
            product_type=product_type,
            size=trade_size_arg,
            sell_size=sell_size_arg,
            dry_run=dry_run_mode
        )

        return jsonify({"status": "success", "message": f"Processed {signal} for {symbol}", "mode": "DRY" if dry_run_mode else "LIVE"}), 200

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Webhook Server with Supabase Config on port {port}...")
    app.run(host='0.0.0.0', port=port)
