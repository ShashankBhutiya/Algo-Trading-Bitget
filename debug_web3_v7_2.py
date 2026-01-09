
from web3 import Web3
from eth_account import Account
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def debug_signing():
    acct = Account.create()
    tx = {'to': acct.address, 'value': 0, 'gas': 21000, 'gasPrice': 1, 'nonce': 0, 'chainId': 1}
    signed_tx = Account.sign_transaction(tx, acct.key)
    
    print(f"Type: {type(signed_tx)}")
    attrs = [a for a in dir(signed_tx) if not a.startswith("_")]
    print(f"Attributes: {attrs}")
            
    if hasattr(signed_tx, "raw_transaction"):
        print("YES: raw_transaction exists")
    if hasattr(signed_tx, "rawTransaction"):
        print("YES: rawTransaction exists")

if __name__ == "__main__":
    debug_signing()
