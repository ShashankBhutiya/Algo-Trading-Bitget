import time
import argparse
from core.bitget_client import BitgetClient
from core.strategy import ema_strategy, ut_bot_strategy
from core.executor import execute_trade

# REPLACE local constants with Supabase manager
from core.supabase_config_manager import supabase_manager

def main():
    client = BitgetClient()
    
    # Initial Config Fetch
    cfg = supabase_manager.get_config()
    symbol = cfg.get("symbol", "ETHUSDT")
    print(f"Bot starting... [{symbol}]")

    while True:
        try:
            # 1. Fetch Dynamic Config
            cfg = supabase_manager.get_config()
            
            # 2. Check Global Kill Switch
            if not cfg.get("enable_trading", True):
                print("Trading Paused...", end='\r')
                time.sleep(10)
                continue

            symbol = cfg.get("symbol", "ETHUSDT")
            product_type = cfg.get("product_type", "SPOT")
            buy_size = float(cfg.get("buy_size_usdt", 5.0))
            sell_size_val = cfg.get("sell_size", "ALL")
            dry_run = cfg.get("dry_run", False)

            # 3. Strategy Logic
            # Note: For Spot, we still need candles. 'get_candles' in client defaults to "USDT-FUTURES".
            # We must update get_candles call too if we want Spot Candles logic match.
            # But let's assume Futures candles are OK proxies for Spot trend?
            # Or better: Update get_candles call.
            # Fetch candles for the target Symbol and Product
            candles = client.get_candles(symbol=symbol, productType=product_type)
            
            if not candles:
                print(f"Failed to fetch candles for {symbol}, retrying...")
                time.sleep(10)
                continue
                
            # Use UT Bot Strategy
            signal = ut_bot_strategy(candles)
            
            if signal:
                print(f"Signal detected: {signal} | Mode: {'DRY' if dry_run else 'LIVE'}")
                
            execute_trade(client, signal, symbol=symbol, product_type=product_type, size=buy_size, sell_size=sell_size_val, dry_run=dry_run)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            
        time.sleep(60)

if __name__ == "__main__":
    # Removed ArgumentParser to rely solely on Remote Config for cleaner "Remote Control" experience
    main()
