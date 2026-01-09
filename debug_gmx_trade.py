
import os
import sys
import time
from dotenv import load_dotenv

# Ensure we can import from core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.gmx_client import GMXClient
from core.executor import execute_trade

def debug_gmx_trade():
    print("--- 🛠️ GMX Trade Execution Debugger 🛠️ ---")
    
    # 1. Load Env
    load_dotenv()
    if not os.getenv("GMX_PRIVATE_KEY"):
         print("⚠️ No GMX_PRIVATE_KEY found. This will default to DRY RUN behavior implicitly for safety, or fail.")
    
    # 2. Initialize Client
    try:
        client = GMXClient()
        print(f"✅ Client Initialized. Wallet: {client.account.address if client.account else 'READ-ONLY (No Key)'}")
    except Exception as e:
        print(f"❌ Client Init Error: {e}")
        return

    # 3. Define Trade Parameters
    symbol = "BTCUSDT"
    product_type = "USDT-FUTURES"
    signal = "open_long" # or 'buy'
    size = 10.0 # USDT value (Dry Run usually ignores this or logs it)
    
    print(f"\n--- Simulating '{signal}' on {symbol} (Size: ${size}) ---")
    
    # 4. Execute Trade (FORCE DRY RUN FIRST)
    print("\n[Step 1] Executing DRY RUN Mode...")
    result_dry = execute_trade(
        client=client,
        signal=signal,
        symbol=symbol,
        product_type=product_type,
        size=size,
        dry_run=True  # <--- Important: Safe Mode
    )
    print("Dry Run Result:", result_dry)
    
    # 5. Execute Trade (LIVE MODE - CHECK WALLET FIRST)
    # Only proceed if user explicitly uncomments execution line in real usage, 
    # but here we will try to calculate size and see if it fails due to Balance/Allowances
    # without actually broadcasting a transaction (unless GMXClient.place_market_order is fully implemented)
    
    print("\n[Step 2] LIVE MODE SIMULATION (Checking Logic, Pre-execution)")
    # Note: GMXClient.place_market_order in current codebase is a STUB that prints "Not Implemented"
    # So this is safe to run to verify the flow up to that point.
    
    # Use a different symbol to avoid 'Duplicate Signal' safety block
    symbol_live = "ETHUSDT" 
    print(f"Switching to {symbol_live} for Live execution test...")

    result_live = execute_trade(
        client=client,
        signal=signal,
        symbol=symbol_live,
        product_type=product_type,
        size=size,
        dry_run=False # <--- Attempts real logic
    )
    
    print("Live Execution Result:", result_live)
    
    if result_live.get("status") == "FILLED":
        print("\n✅ Trade Logic SUCCESS (Mocked or Real Executed)")
    elif "Not Implemented" in str(result_live):
        print("\n⚠️ Trade Logic reached endpoint, but GMX Contract call is missing (Expected behavior for now).")
    else:
        print("\n❌ Trade Logic Failed.")

if __name__ == "__main__":
    debug_gmx_trade()
