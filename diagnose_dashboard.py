
import os
import sys
import time

# Add current directory to path so we can import core modules
sys.path.append(os.getcwd())

try:
    from core.supabase_config_manager import supabase_manager
    print("[1] Successfully imported supabase_manager")
except Exception as e:
    print(f"[FAIL] Could not import supabase_manager: {e}")
    sys.exit(1)

def test_supabase_connectivity():
    print("\n--- Testing Supabase Connectivity ---")
    
    # 1. Config Test
    print("Fetching Config...")
    try:
        cfg = supabase_manager.get_config()
        print(f"Config Fetched: {cfg}")
    except Exception as e:
        print(f"[FAIL] Error fetching config: {e}")
        return

    # 2. Log Insertion Test
    print("Inserting Test Log...")
    test_entry = {
        "symbol": "TEST-DIAGNOSTIC",
        "side": "buy",
        "size": "0.00",
        "price": "0.00",
        "type": "TEST",
        "status": "DIAGNOSTIC",
        "info": "This is a test log from diagnose_dashboard.py"
    }
    try:
        supabase_manager.log_trade(test_entry)
        print("Log Inserted.")
    except Exception as e:
        print(f"[FAIL] Error inserting log: {e}")
        return

    # 3. Log Retrieval Test
    print("Fetching Logs...")
    try:
        logs = supabase_manager.get_logs(limit=5)
        print(f"Logs Fetched: {len(logs)} records")
        for l in logs:
            print(f" - {l.get('symbol')} {l.get('side')} [{l.get('status')}]")
    except Exception as e:
        print(f"[FAIL] Error fetching logs: {e}")

if __name__ == "__main__":
    test_supabase_connectivity()
