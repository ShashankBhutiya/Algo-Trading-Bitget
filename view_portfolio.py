
import os
import sys
from web3 import Web3
from dotenv import load_dotenv

def format_balance(balance, decimals=18):
    return float(balance) / (10 ** decimals)

def view_portfolio():
    load_dotenv()
    print("--- GMX Portfolio (Arbitrum) ---")
    
    # 1. Credentials
    rpc_url = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
    private_key = os.getenv("GMX_PRIVATE_KEY")
    
    if not private_key:
        print("Error: GMX_PRIVATE_KEY not found in .env")
        return

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            print("Error: Could not connect to RPC")
            return
            
        account = w3.eth.account.from_key(private_key)
        address = account.address
        print(f"Wallet Address: {address}")
        print("-" * 30)

        # 2. Wallet Balances (Arbitrum)
        # ETH
        eth_wei = w3.eth.get_balance(address)
        eth_bal = w3.from_wei(eth_wei, 'ether')
        print(f"ETH:   {eth_bal:.6f}")

        # Tokens
        tokens = [
            {"name": "USDT", "address": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", "decimals": 6},
            {"name": "USDC.e", "address": "0xFF970A61a04b1cA14834A43f5dE4533eBDDB5CC8", "decimals": 6},
            {"name": "USDC", "address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", "decimals": 6},
            {"name": "ARB", "address": "0x912CE59144191C1204E64559FE8253a0e49E6548", "decimals": 18}
        ]

        erc20_abi = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

        for token in tokens:
            try:
                contract = w3.eth.contract(address=token['address'], abi=erc20_abi)
                raw_bal = contract.functions.balanceOf(address).call()
                formatted = format_balance(raw_bal, token['decimals'])
                if formatted > 0:
                    print(f"{token['name']}:  {formatted:.4f}")
            except Exception as e:
                print(f"{token['name']}: Error fetching balance")

        print("-" * 30)
        
        # 3. Open Positions
        # Note: True position fetching requires querying the GMX DataStore/Reader contracts which involves complex ABI decoding.
        # This is a placeholder until that implementation is added to GMXClient.
        print("Open Positions:")
        print("   (Position fetching is currently under development)")
        print("   Checking local logic... No active trades tracked by bot memory.")

        print("-" * 30)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    view_portfolio()
