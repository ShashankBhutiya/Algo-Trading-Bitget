from core.gmx_client import GMXClient
import json

def check_mode():
    client = GMXClient()
    print("Checking Account Mode (GMX)...")
    # GMX V2 doesn't have "Hedge Mode" toggles like CEXs, 
    # but we can check if we can connect and fetch positions.
    try:
        positions = client.get_positions()
        print(f"Connection Successful. Active Positions: {len(positions)}")
        print("GMX uses isolated markets generally. No specific 'Hedge Mode' setting required.")
    except Exception as e:
        print(f"Error checking GMX: {e}")

if __name__ == "__main__":
    check_mode()
