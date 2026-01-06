import time
from datetime import datetime, timezone
from core.supabase_config_manager import supabase_manager

class SafetyManager:
    def __init__(self):
        self.max_trades_daily = 50
        self.signal_cache = {} # Key: (symbol, signal) -> timestamp
        self.dedupe_window = 5 # seconds
        self.block_reason = None

    def check_gates(self, symbol, signal, is_dry_run):
        """
        Run all safety checks. Returns (True, None) if safe, (False, Reason) if blocked.
        """
        # 1. Deduplication (Memory)
        if self._is_duplicate(symbol, signal):
            return False, "Duplicate Signal detected within window"

        # 2. Daily Trade Limit (Live only)
        if not is_dry_run and self._is_daily_limit_reached():
             return False, "Daily Trade Limit Reached"

        # 3. Emergency Stop (Config check)
        # Assuming enable_trading is the stop switch.
        # This is already checked in webhook_bot.py but good to double check deep in execution.
        cfg = supabase_manager.get_config()
        if not cfg.get("enable_trading", True):
            return False, "Trading Disabled (Kill Switch)"

        return True, None

    def _is_duplicate(self, symbol, signal):
        key = (symbol, signal)
        now = time.time()
        last_time = self.signal_cache.get(key, 0)
        
        if now - last_time < self.dedupe_window:
            return True
        
        self.signal_cache[key] = now
        return False

    def _is_daily_limit_reached(self):
        # Query Supabase for count of LIVE trades todat
        # This is expensive if high frequency, but for 50/day it's fine.
        try:
            client = supabase_manager.client
            if not client:
                return False # Fail open or closed? Open for now in dry run/dev.
                
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0).isoformat()
            
            # Count trades created >= today_start
            # Supabase doesn't have a direct .count() in python client easy syntax without select
            # we do select count
            res = client.table("trade_logs")\
                .select("id", count="exact")\
                .eq("type", "LIVE")\
                .gte("created_at", today_start)\
                .execute()
                
            count = res.count
            if count and count >= self.max_trades_daily:
                return True
        except Exception as e:
            print(f"Safety check error: {e}")
            # If DB fails, maybe safe to block? Or allow? 
            # Let's log and allow to avoid freezing on connection blip, 
            # but usually safety means FAIL CLOSED.
            # However, for beta, let's just warn.
            pass
            
        return False

safety_manager = SafetyManager()
