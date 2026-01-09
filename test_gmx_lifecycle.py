
import os
import sys
import time
from dotenv import load_dotenv

# Ensure we can import from core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.gmx_client import GMXClient

def test_gmx_account_lifecycle():
    print("--- 🔄 Debugging GMX Account & Trading Lifecycle 🔄 ---")
    
    # 1. Load Credentials
    load_dotenv()
    private_key = os.getenv("GMX_PRIVATE_KEY")
    if not private_key:
        print("❌ CRITICAL: GMX_PRIVATE_KEY not found in .env via load_dotenv() or os.getenv()")
        print("   Cannot proceed with account verification.")
        return
        
    print("✅ GMX_PRIVATE_KEY is present.")

    # 2. Initialize Client
    try:
        client = GMXClient()
        if not client.account:
             print("❌ Client initialized but 'account' is None. Check Private Key validity.")
             return
        print(f"✅ GMX Client Active. Wallet Address: {client.account.address}")
    except Exception as e:
        print(f"❌ Failed to initialize GMXClient: {e}")
        return

    # 3. Check Native Balance (ETH for Gas)
    try:
        print("\n--- Checking NATIVE Balance (Gas) ---")
        # Direct Web3 check
        eth_wei = client.web3.eth.get_balance(client.account.address)
        eth_bal = client.web3.from_wei(eth_wei, 'ether')
        print(f"   Balance: {eth_bal} ETH")
        
        if eth_bal == 0:
            print("⚠️ WARNING: Balance is 0.0 ETH. Transactions will fail due to lack of Gas.")
    except Exception as e:
        print(f"❌ Error checking balance: {e}")

    # 4. Check Collateral Balance (Mock vs Real)
    try:
        print("\n--- Checking ASSET Balance (Simulated view via Client) ---")
        assets = client.get_spot_assets()
        print(f"   Assets Response: {assets}")
    except Exception as e:
         print(f"❌ Error checking assets: {e}")

    # 5. Check Market Data Access
    print("\n--- Checking Market Data Feed ---")
    ticker = client.get_ticker("BTCUSDT")
    if ticker:
        print(f"✅ Market Data OK. BTC Price: {ticker.get('lastPr')}")
    else:
         print("❌ Market Data Failed.")

    # 6. Simulate Trade Logic (Order Creation)
    print("\n--- Validating Trade Execution Logic (Dry Run) ---")
    print("   Attempting to create a 'Buy' order object...")
    
    try:
        # We call place_market_order directly to see what it generates/returns
        # Using specific params
        res = client.place_market_order(
            symbol="BTCUSDT",
            side="open_long",
            size=10.0, # $10
            product_type="USDT-FUTURES"
        )
        print(f"   Execution Result: {res}")
        
        if res.get("msg") == "GMX Order Simulation (Not Implemented)":
             print("\nℹ️ Status: Logic is correctly routed to GMX Client Stub.")
             print("   To Enable REAL TRADING, 'core/gmx_client.py' must be updated with ExchangeRouter ABI and calls.")
        else:
             print("\n❓ Unexpected response from client.")
             
    except Exception as e:
        print(f"❌ Execution Logic Error: {e}")

    print("\n--- End of Lifecycle Test ---")

if __name__ == "__main__":
    test_gmx_account_lifecycle()
