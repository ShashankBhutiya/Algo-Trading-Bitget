
import os
from web3 import Web3
from dotenv import load_dotenv

def check_mainnet():
    load_dotenv()
    pk = os.getenv("GMX_PRIVATE_KEY")
    if not pk:
        print("No Private Key Configured")
        return

    w3 = Web3(Web3.HTTPProvider("https://rpc.ankr.com/eth"))
    account = w3.eth.account.from_key(pk)
    address = account.address
    
    print(f"Checking Ethereum Mainnet for: {address}")
    
    try:
        if w3.is_connected():
            balance = w3.eth.get_balance(address)
            eth = w3.from_wei(balance, 'ether')
            print(f"💰 Ethereum Mainnet Balance: {eth:.6f} ETH")
            if eth > 0:
                print("✅ Funds found on Ethereum Mainnet!")
                print("ℹ️  You need to BRIDGE these funds to Arbitrum One to use GMX.")
            else:
                print("❌ No funds found on Ethereum Mainnet either.")
        else:
            print("Could not connect to Mainnet RPC")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_mainnet()
