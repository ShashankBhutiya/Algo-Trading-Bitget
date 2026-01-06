from core.bitget_client import BitgetClient
import json

def check():
    client = BitgetClient()
    # Check positions (might be empty if no open positions)
    print("Checking Positions...")
    positions = client.get_positions(symbol="BTCUSDT")
    print(json.dumps(positions, indent=2))
    
    # We might also want to check something that returns account config, 
    # but BitgetClient currently only has get_positions.
    # get_positions returns the configuration if available? 
    # Usually it returns a list of positions. 
    # If list is not empty, we can see 'marginMode' and 'holdMode'.
    
    if positions:
        print("\n--- Insight ---")
        for p in positions:
            print(f"Margin Mode: {p.get('marginMode')}")
            print(f"Hold Mode: {p.get('holdMode')}") # Some APIs call it holdSide or similar
            print(f"Side: {p.get('holdSide')}") 

if __name__ == "__main__":
    check()
