from core.gmx_client import GMXClient

def set_hedge():
    print("--- GMX V2 Configuration ---")
    print("GMX does not use 'One-way' vs 'Hedge' mode settings like Bitget.")
    print("You can manage Longs and Shorts independently on GMX V2 markets.")
    
    client = GMXClient()
    if client.account:
        print(f"Client Active: {client.account.address}")
    else:
        print("Client in Read-Only Mode")

if __name__ == "__main__":
    set_hedge()
