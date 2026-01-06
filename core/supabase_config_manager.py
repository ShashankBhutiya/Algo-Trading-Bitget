import os
import time
from supabase import create_client, Client
from dotenv import load_dotenv

# Load env to get credentials
load_dotenv()

# SUPABASE DEFAULTS
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class SupabaseConfigManager:
    def __init__(self):
        self.client: Client = None
        self.cache = {}
        self.last_fetch = 0
        self.cache_ttl = 5 # Seconds to cache config before re-fetching
        
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("Connected to Supabase for Config.")
            except Exception as e:
                print(f"Failed to connect to Supabase: {e}")
        else:
            print("Warning: SUPABASE_URL or SUPABASE_KEY missing.")

    def get_config(self):
        # 1. Check Cache
        if time.time() - self.last_fetch < self.cache_ttl and self.cache:
            return self.cache

        # 2. Fetch from Supabase
        if self.client:
            try:
                response = self.client.table("bot_config").select("*").limit(1).execute()
                if response.data and len(response.data) > 0:
                    self.cache = response.data[0]
                    self.last_fetch = time.time()
                    return self.cache
            except Exception as e:
                print(f"Error fetching from Supabase: {e}")
                # Fallback to cache if exists
                if self.cache: 
                    return self.cache
        
        # 3. Fallback Default
        return {
            "symbol": "ETHUSDT",
            "product_type": "SPOT",
            "buy_size_usdt": 5.0,
            "sell_size": "ALL",
            "leverage": 5,
            "enable_trading": True,
            "dry_run": False
        }

    def update_config(self, updates):
        if not self.client:
            return None
            
        try:
            # Check if a config row exists
            response = self.client.table("bot_config").select("id").limit(1).execute()
            
            if response.data and len(response.data) > 0:
                # Row exists, Update it
                first_id = response.data[0]["id"]
                result = self.client.table("bot_config").update(updates).eq("id", first_id).execute()
            else:
                # Row does not exist, Insert it
                # Merge updates with defaults to ensure complete row
                defaults = {
                     "symbol": "ETHUSDT",
                     "product_type": "SPOT",
                     "buy_size_usdt": 5.0,
                     "sell_size": "ALL",
                     "leverage": 5,
                     "enable_trading": True,
                     "dry_run": False
                }
                new_row = {**defaults, **updates}
                result = self.client.table("bot_config").insert(new_row).execute()
            
            if result.data and len(result.data) > 0:
                self.cache = result.data[0]
                self.last_fetch = time.time()
                return self.cache
            return None
            
        except Exception as e:
            print(f"Error updating Supabase: {e}")
            return None

    def log_trade(self, entry_data):
        """
        Logs a trade execution to Supabase 'trade_logs' table.
        entry_data should be a dict with keys like:
        symbol, side, size, price, status, type (LIVE/DRY)
        """
        if not self.client:
            print("Supabase client not connected. Skipping log.")
            return

        try:
            # Enforce some defaults
            if "status" not in entry_data:
                entry_data["status"] = "FILLED"
            
            # Add timestamp if relying on client, but Supabase usually handles created_at
            # entry_data["created_at"] = 'now()' 

            self.client.table("trade_logs").insert(entry_data).execute()
        except Exception as e:
            print(f"Error logging trade to Supabase: {e}")

    def get_logs(self, limit=20):
        """Fetch recent trade logs."""
        if not self.client:
            return []
        
        try:
            # Order by created_at desc
            response = self.client.table("trade_logs").select("*").order("created_at", desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []

    def log_balance(self, total_balance, breakdown=None):
        """Log the total wallet balance to history."""
        if not self.client:
            return
        try:
            row = {
                "total_balance": float(total_balance),
                "asset_breakdown": breakdown if breakdown else {}
            }
            self.client.table("balance_history").insert(row).execute()
        except Exception as e:
            print(f"Error logging balance: {e}")

    def get_balance_history(self, limit=100):
        """Fetch balance history for charts."""
        if not self.client:
            return []
        try:
            return self.client.table("balance_history").select("*").order("created_at", desc=True).limit(limit).execute().data
        except Exception as e:
            print(f"Error fetching balance history: {e}")
            return []

# Singleton instance
supabase_manager = SupabaseConfigManager()
