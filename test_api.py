# test_api.py

from core.bitget_client import BitgetClient

client = BitgetClient()
candles = client.get_candles()

if candles is None:
    print("❌ Failed to fetch candles")
else:
    print("✅ Candles fetched:", len(candles))
    print("First candle:", candles[0])
    