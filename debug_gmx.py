
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.gmx_client import GMXClient

def debug_gmx_connection():
    print("--- 🛠️ GMX Connection & Data Debugger 🛠️ ---")
    
    # 1. Load Env
    load_dotenv()
    private_key = os.getenv("GMX_PRIVATE_KEY")
    
    if private_key:
        masked_key = private_key[:4] + "..." + private_key[-4:]
        print(f"✅ GMX_PRIVATE_KEY found: {masked_key}")
    else:
        print("⚠️ GMX_PRIVATE_KEY not found in .env (Read-Only Mode)")

    # 2. Initialize Client
    try:
        client = GMXClient()
        print("✅ GMXClient initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize GMXClient: {e}")
        return

    # 3. Test Ticker (Price Check)
    symbol = "BTCUSDT"
    print(f"\n--- Testing Ticker Fetch for {symbol} ---")
    ticker = client.get_ticker(symbol)
    if ticker:
        print(f"✅ Ticker Data Received: {ticker}")
        if 'lastPr' in ticker:
             print(f"   Price: {ticker['lastPr']}")
    else:
        print("❌ Failed to fetch ticker.")

    # 4. Test Candles (Historical Data)
    print(f"\n--- Testing Candles Fetch for {symbol} ---")
    candles = client.get_candles(symbol, limit=5)
    if candles and isinstance(candles, list) and len(candles) > 0:
        print(f"✅ Received {len(candles)} candles.")
        first_candle = candles[0]
        # Binance kline format: [Time, Open, High, Low, Close, ...]
        print(f"   Latest Candle (Close): {first_candle[4]}")
    else:
        print("❌ Failed to fetch candles.")

    # 5. Test Assets (Wallet Balance)
    print("\n--- Testing Spot Assets (Wallet Balance) ---")
    try:
        assets = client.get_spot_assets()
        print(f"✅ Assets Response: {assets}")
    except Exception as e:
        print(f"❌ Failed to fetch assets: {e}")

if __name__ == "__main__":
    debug_gmx_connection()
