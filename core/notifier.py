import requests
from core.supabase_config_manager import supabase_manager

class TelegramNotifier:
    def __init__(self):
        self.base_url = "https://api.telegram.org/bot{}/sendMessage"

    def _get_creds(self):
        """Fetch credentials from dynamic config."""
        cfg = supabase_manager.get_config()
        token = cfg.get("telegram_token")
        chat_id = cfg.get("telegram_chat_id")
        enabled = cfg.get("enable_notifications", False)
        return token, chat_id, enabled

    def send_message(self, text, test_mode=False):
        """
        Send a raw text message to the configured Telegram chat.
        Returns: (success: bool, info: str)
        """
        token, chat_id, enabled = self._get_creds()
        
        # In test mode, we ignore the 'enabled' switch check
        if not test_mode and not enabled:
            return False, "Notifications are disabled in settings."
            
        if not token or not chat_id:
            return False, "Missing Bot Token or Chat ID."

        try:
            url = self.base_url.format(token)
            payload = {
                "chat_id": chat_id,
                "text": text,
                # "parse_mode": "Markdown" # Disabled to prevent 'Can't parse entities' errors during debug
            }
            resp = requests.post(url, json=payload, timeout=5)
            
            if resp.status_code == 200:
                return True, "Message sent successfully."
            else:
                err_text = resp.text
                print(f"[Notifier] Telegram API Error: {err_text}")
                return False, f"Telegram API Error: {resp.status_code} - {err_text}"
                
        except Exception as e:
            print(f"[Notifier] Error sending Telegram: {e}")
            return False, f"Network/Internal Error: {str(e)}"

    def send_trade_alert(self, symbol, side, size, price, status, is_dry_run=False):
        """Format and send a trade alert."""
        mode_icon = "🟢 LIVE" if not is_dry_run else "🟠 DRY RUN"
        color_icon = "🚀" if "buy" in side.lower() or "long" in side.lower() else "📉"
        
        msg = (
            f"*{mode_icon} Trade Executed*\n\n"
            f"{color_icon} *Side:* {side.upper()}\n"
            f"🪙 *Symbol:* `{symbol}`\n"
            f"💰 *Size:* `{size}`\n"
            f"🏷 *Price:* `{price}`\n"
            f"ℹ️ *Status:* `{status}`"
        )
        success, msg = self.send_message(msg)
        if not success:
            print(f"[Notifier] Failed to send alert: {msg}")

telegram_bot = TelegramNotifier()
