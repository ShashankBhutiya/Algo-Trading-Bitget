
from web3 import Web3
from eth_account import Account
import os

def debug_signing():
    print(f"Web3 Version: {Web3.version if hasattr(Web3, 'version') else 'Unknown'}")
    
    # Generate random account
    acct = Account.create()
    print(f"Account: {acct.address}")
    
    # Dummy Tx
    tx = {
        'to': '0x0000000000000000000000000000000000000000',
        'value': 0,
        'gas': 21000,
        'gasPrice': 1000000000,
        'nonce': 0,
        'chainId': 1
    }
    
    # Sign
    print("Signing transaction...")
    signed_tx = Account.sign_transaction(tx, acct.key)
    
    print(f"Signed Tx Type: {type(signed_tx)}")
    print(f"Signed Tx Dir: {dir(signed_tx)}")
    
    try:
        print(f"rawTransaction (dot access): {signed_tx.rawTransaction.hex()}")
    except AttributeError as e:
        print(f"Error accessing .rawTransaction: {e}")
        
    try:
        print(f"rawTransaction (dict access): {signed_tx['rawTransaction'].hex()}")
    except Exception as e:
        print(f"Error accessing ['rawTransaction']: {e}")

if __name__ == "__main__":
    debug_signing()
