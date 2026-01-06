from core.bitget_client import BitgetClient
import json

def test():
    client = BitgetClient()
    print("Testing Futures Candles (1m)...")
    c_gut = client.get_candles(symbol="BTCUSDT", granularity="1m", productType="USDT-FUTURES")
    if c_gut: print(f"Futures Success: {len(c_gut)} candles")
    else: print("Futures Failed")

    print("\nTesting Spot Candles (1m)...")
    c_spot = client.get_candles(symbol="ETHUSDT", granularity="1m", productType="SPOT")
    if c_spot: print(f"Spot (1m) Success: {len(c_spot)} candles")
    else: print("Spot (1m) Failed")
    
    print("\nTesting Spot Candles (1min)...")
    c_spot_min = client.get_candles(symbol="ETHUSDT", granularity="1min", productType="SPOT")
    if c_spot_min: 
        print(f"Spot (1min) Success: {len(c_spot_min)} candles")
        print(f"Sample Candle (Length {len(c_spot_min[0])}): {c_spot_min[0]}")
    else: print("Spot (1min) Failed")

if __name__ == "__main__":
    test()
