
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.gmx_client import GMXClient

def test_buy_eth():
    print("--- 🧪 Testing 'Buy ETH' (Spot Swap / Long) on GMX 🧪 ---")
    
    # 1. Init
    load_dotenv()
    client = GMXClient()
    
    if not client.account:
        print("❌ No Private Key found. Cannot trade.")
        return

    address = client.account.address
    print(f"🔑 Wallet: {address}")

    # 2. Check Gas (ETH) & USDT
    try:
        eth_bal_wei = client.web3.eth.get_balance(address)
        eth_bal = float(client.web3.from_wei(eth_bal_wei, 'ether'))
        print(f"⛽ ETH Balance (Gas): {eth_bal:.6f}")
        
        # Check USDT Balance
        usdt_addr = "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"
        abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]
        ctr = client.web3.eth.contract(address=usdt_addr, abi=abi)
        usdt_wei = ctr.functions.balanceOf(address).call()
        usdt_bal = float(usdt_wei) / 1e6
        print(f"💵 USDT Balance: {usdt_bal:.2f}")

        if eth_bal < 0.001: 
            print("⚠️ CRITICAL: Low/No ETH. Transactions require ETH for gas fees, even if you have USDT.")

    except Exception as e:
        print(f"⚠️ Could not fetch balances: {e}")

    # 3. Define Trade
    # GMX Spot Min is usually around $10 worth, but let's try 6.0 since user has 8.88
    amount_usdt = 6.0 
    symbol = "ETHUSDT"
    
    print(f"\n📝 Scenario: Buying ${amount_usdt} worth of ETH (Spot/Swap)")
    
    # 4. Excecute
    try:
        # Using product_type="SPOT" to indicate we want actual tokens (Swap) if supported
        res = client.place_market_order(
            symbol=symbol,
            side="buy",
            size=amount_usdt,
            product_type="SPOT"
        )
        
        print("\n--- Execution Response ---")
        print(res)
        
        if res.get("msg") == "GMX Order Simulation (Not Implemented)":
            print("\n🔍 DEBUG FINDINGS:")
            print("1. The GMX Client is correctly reachable.")
            print("2. The 'place_market_order' function was called.")
            print("3. 🛑 ACTION REQUIRED: The actual Blockchain Transaction logic is missing.")
            print("   You need to implement the 'ExchangeRouter.createOrder' call in 'core/gmx_client.py'.")
            print("   (This requires the GMX V2 Router ABI and Token Approvals).")
            
    except Exception as e:
        print(f"❌ Execution Failed: {e}")

if __name__ == "__main__":
    test_buy_eth()
