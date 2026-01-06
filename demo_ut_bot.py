import time
import pandas as pd
from core.bitget_client import BitgetClient
from core.strategy import ut_bot_strategy

def run_demo():
    print("Fetching market data...")
    client = BitgetClient()
    candles = client.get_candles(limit=100)
    
    if not candles:
        print("Error: No candles fetched. Check API connection or Proxy.")
        return

    print(f"Fetched {len(candles)} candles.")

    # Re-implementing parts of strategy locally to show the DataFrame columns for demo purposes
    # faster than modifying the strategy function to return df
    df = pd.DataFrame(
        candles,
        columns=["ts","open","high","low","close","vol", "turnover"]
    )
    for col in ["high", "low", "close"]:
        df[col] = df[col].astype(float)
        
    # --- UT Bot Logic (Visualization) ---
    atr_period = 10
    key_value = 2
    
    # 1. ATR
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['xATR'] = df['tr'].rolling(window=atr_period).mean()
    df['nLoss'] = key_value * df['xATR']

    # 2. Trailing Stop
    trailing_stop = [0.0] * len(df)
    src = df['close'].values
    nLoss = df['nLoss'].values
    
    for i in range(1, len(df)):
        if pd.isna(nLoss[i]): continue
        
        prev_stop = trailing_stop[i-1]
        price = src[i]
        prev_price = src[i-1]
        loss = nLoss[i]
        
        if (price > prev_stop) and (prev_price > prev_stop):
            trailing_stop[i] = max(prev_stop, price - loss)
        elif (price < prev_stop) and (prev_price < prev_stop):
            trailing_stop[i] = min(prev_stop, price + loss)
        elif (price > prev_stop):
            trailing_stop[i] = price - loss
        else:
            trailing_stop[i] = price + loss
            
    df['trailing_stop'] = trailing_stop
    
    # 3. Determine Buy/Sell Zones
    # If close > trailing_stop => BUY ZONE
    df['signal_zone'] = df.apply(lambda row: 'BUY' if row['close'] > row['trailing_stop'] else 'SELL', axis=1)
    
    # 4. Detect Shifts
    df['prev_zone'] = df['signal_zone'].shift(1)
    df['action'] = df.apply(
        lambda row: "OPEN LONG" if (row['signal_zone'] == 'BUY' and row['prev_zone'] == 'SELL') 
        else ("OPEN SHORT" if (row['signal_zone'] == 'SELL' and row['prev_zone'] == 'BUY') else "-"), 
        axis=1
    )

    # Convert Timestamp
    df['time'] = pd.to_datetime(df['ts'].astype(int), unit='ms')

    print("\n--- UT Bot Indicator Data (Last 20 Candles) ---")
    print(df[['time', 'close', 'xATR', 'trailing_stop', 'signal_zone', 'action']].tail(20).to_string())

    latest_signal = ut_bot_strategy(candles)
    print(f"\nLive Strategy Function Returns: {latest_signal}")
    
    if latest_signal:
        print("✅ SUCCESS: Strategy producing signals.")
    else:
        print("ℹ️ INFO: No signal on the very last candle (normal).")

if __name__ == "__main__":
    run_demo()
