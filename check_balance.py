from core.bitget_client import BitgetClient
import json

def check_balances():
    client = BitgetClient()
    
    print("--- Spot Wallet Assets ---")
    spot_resp = client.get_spot_assets()
    if spot_resp and spot_resp.get("code") == "00000":
        data = spot_resp.get("data", [])
        # Filter for non-zero
        found = False
        for asset in data:
            available = float(asset.get("available", 0))
            if available > 0:
                print(f"Coin: {asset['coin']} | Available: {available} | Frozen: {asset.get('frozen', 0)}")
                found = True
        if not found:
            print("No assets found in Spot wallet.")
    else:
        print(f"Error fetching spot assets: {spot_resp}")

if __name__ == "__main__":
    check_balances()
