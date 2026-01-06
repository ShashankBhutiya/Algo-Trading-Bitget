from core.bitget_client import BitgetClient
import json

def set_hedge():
    client = BitgetClient()
    print("Setting Hedge Mode...")
    resp = client.set_position_mode("hedge_mode")
    print(json.dumps(resp, indent=2))

if __name__ == "__main__":
    set_hedge()
