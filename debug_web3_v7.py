
from web3 import Web3
from eth_account import Account

def debug_signing():
    acct = Account.create()
    tx = {'to': acct.address, 'value': 0, 'gas': 21000, 'gasPrice': 1, 'nonce': 0, 'chainId': 1}
    signed_tx = Account.sign_transaction(tx, acct.key)
    
    print(f"Type: {type(signed_tx)}")
    print("Attributes:")
    for attr in dir(signed_tx):
        if not attr.startswith("_"):
            print(f" - {attr}")
            
    # Try snake case
    if hasattr(signed_tx, "raw_transaction"):
        print(f"Found 'raw_transaction'! Hex: {signed_tx.raw_transaction.hex()}")
    elif hasattr(signed_tx, "rawTransaction"):
        print(f"Found 'rawTransaction'! Hex: {signed_tx.rawTransaction.hex()}")

if __name__ == "__main__":
    debug_signing()
