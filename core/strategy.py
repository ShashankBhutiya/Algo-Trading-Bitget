import pandas as pd
import numpy as np

def ut_bot_strategy(candles, key_value=2, atr_period=10):
    """
    UT Bot Strategy implementation.
    Returns 'open_long', 'open_short', or None based on the latest signal.
    """
    # Truncate to first 7 columns (Spot has 8, Futures 7)
    safe_candles = [c[:7] for c in candles]
    df = pd.DataFrame(
        safe_candles,
        columns=["ts","open","high","low","close","vol", "turnover"]
    )
    # Convert necessary columns to float
    for col in ["high", "low", "close"]:
        df[col] = df[col].astype(float)

    # 1. Calculate ATR
    # TR = max(high-low, abs(high-prev_close), abs(low-prev_close))
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    
    # SMA of TR usually for UT Bot
    df['xATR'] = df['tr'].rolling(window=atr_period).mean()

    # 2. Calculate Trailing Stop (Iterative)
    # nLoss = key_value * xATR
    df['nLoss'] = key_value * df['xATR']
    
    # Initialize implementation columns
    df['trailing_stop'] = 0.0
    df['position'] = 0 # 1 for Long, -1 for Short

    # Iterating is necessary for recursive logic of Trailing Stop
    # optimizing by converting to numpy arrays
    src = df['close'].values
    nLoss = df['nLoss'].values
    trailing_stop = np.zeros(len(df))
    # We need to track 'position' state to detect Buy/Sell flips
    # Interpretation:
    # If price > trailing_stop => Buy
    # If price < trailing_stop => Sell
    
    # Start loop from atr_period
    for i in range(1, len(df)):
        if np.isnan(nLoss[i]): 
            continue
            
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
        else: # price < prev_stop
            trailing_stop[i] = price + loss

    df['trailing_stop'] = trailing_stop

    # 3. Generate Signals
    # Buy: Close crosses Above Trailing Stop
    # Sell: Close crosses Below Trailing Stop
    # But usually UT Bot maintains a "state" (Buy or Sell Zone).
    # We want to signal ONLY on the FLIP.
    
    # Let's determine the "trend" state:
    # If close > trailing_stop => 1 (Bullish)
    # If close < trailing_stop => -1 (Bearish)
    
    # Note: logic above for trailing_stop implicitly handles the "crossover" update.
    # Current bar check:
    current_close = df['close'].iloc[-1]
    current_stop = df['trailing_stop'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    prev_stop = df['trailing_stop'].iloc[-2]

    is_bullish = current_close > current_stop
    was_bullish = prev_close > prev_stop

    if is_bullish and not was_bullish:
        return "open_long"
    elif not is_bullish and was_bullish:
        return "open_short"
    
    return None

def ema_strategy(candles):
    # Truncate to first 7 columns
    safe_candles = [c[:7] for c in candles]
    df = pd.DataFrame(
        safe_candles,
        columns=["ts","open","high","low","close","vol", "turnover"]
    )
    df["close"] = df["close"].astype(float)

    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    if df["ema20"].iloc[-1] > df["ema50"].iloc[-1]:
        return "open_long"
    elif df["ema20"].iloc[-1] < df["ema50"].iloc[-1]:
        return "open_short"
    return None
