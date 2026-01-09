from core.gmx_client import GMXClient
import json

def check_bal():
    client = GMXClient()
    print("Fetching GMX Balances...")
    try:
        assets = client.get_spot_assets()
        print(json.dumps(assets, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_bal()
