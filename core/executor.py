from core.position import get_open_position_side
from core.safety_manager import safety_manager
from core.notifier import telegram_bot
from core.supabase_config_manager import supabase_manager
import time

DRY_RUN = False # Default fallback

def format_api_error(resp):
    """Parse Bitget API errors into user-friendly messages."""
    if not resp:
        return "No response from Exchange"
    
    code = resp.get("code")
    msg = resp.get("msg", "Unknown Error")
    
    # Common Bitget Error Codes
    if code == "45110":
        return f"Order Size too small. (Min 5 USDT). Exchange Msg: {msg}"
    if code == "40768":
        return "Insufficient Balance in Account"
    if code == "400172":
        return "Invalid Symbol or Product Type"
    if code == "43012":
        return "Insufficient Balance (or Market Volatility). Check Funds."
    if code in ["40004", "40014", "40017", "40015"] or "unauthorized" in msg.lower():
        return "Authentication Failed: Check API Key, Secret, and Passphrase."
    
    return f"Exchange Error ({code}): {msg}"

def place_order_with_retry(client, symbol, side, size, product_type, retries=3):
    """Attempts to place an order, retrying on specific volatility errors."""
    for i in range(retries + 1):
        # Explicit keyword arguments to avoid positional mismatch
        resp = client.place_market_order(
            symbol=symbol, 
            side=side, 
            size=size, 
            product_type=product_type
        )
        
        # If successful, return immediately
        if resp and resp.get("code") == "00000":
            return resp
            
        # If Volatility Error (43012) or System Busy, wait and retry
        code = resp.get("code") if resp else "unknown"
        if code in ["43012", "40009"] and i < retries: # 40009 is system busy
             print(f"⚠️ Exchange Warning ({code}). Retrying in 1.0s... (Attempt {i+1}/{retries})")
             time.sleep(1.0) # Longer backoff
             continue
             
        # Return the last response (even if error)
        return resp
    return resp

def execute_trade(client, signal, symbol="BTCUSDT", product_type="USDT-FUTURES", size=0.001, sell_size="ALL", dry_run=False):
    if not signal:
        return {"success": False, "status": "IGNORED", "message": "No signal provided"}

    # Check if dry_run passed, else fallback to global (or just use passed arg)
    is_dry_run = dry_run or DRY_RUN

    # Signal Translation (TradingView "buy"/"sell" -> "open_long"/"open_short")
    if product_type.endswith("FUTURES") or product_type == "PERP":
        if signal.lower() == "buy":
            signal = "open_long"
        elif signal.lower() == "sell":
            signal = "open_short"

    # --- SAFETY GATES ---
    is_safe, reason = safety_manager.check_gates(symbol, signal, is_dry_run)
    if not is_safe:
        print(f"🛑 BLOCKED: {reason}")
        if not is_dry_run: 
             telegram_bot.send_message(f"⚠️ *Trade Blocked*\n\nReason: {reason}\nSignal: {signal} on {symbol}")
        return {"success": False, "status": "BLOCKED", "message": reason, "blocked": True}

    if is_dry_run:
        print(f"-------- DRY RUN: {signal} [{symbol} {product_type}] --------")
    
    # --- SPOT TRADING LOGIC ---
    if product_type == "SPOT":
        if is_dry_run:
            print(f"[DRY RUN] Would Execute SPOT {signal} on {symbol} with size {size}")
            # Log Dry Run
            supabase_manager.log_trade({
                "symbol": symbol,
                "side": signal,
                "size": str(size),
                "price": "MARKET",
                "type": "DRY_RUN",
                "status": "SIMULATED",
                "info": "Spot entry simulated"
            })
            return {"success": True, "status": "SIMULATED", "message": "Dry Run Spot Trade Executed"}
            
        print(f"Executing SPOT Trade: {signal}")
        
        spot_side = None
        spot_size = str(size) 
        
        if signal in ["open_long", "close_short", "buy"]:
            spot_side = "buy"
        elif signal in ["open_short", "close_long", "sell"]:
            spot_side = "sell"
            
            # robust check for "ALL"
            normalized_sell = str(sell_size).upper().strip()
            
            if normalized_sell != "ALL":
                spot_size = str(sell_size)
                print(f"DEBUG: Configured Sell Size is '{sell_size}' (Treated as coin amount, NOT 'ALL')")
                print(f"Selling Fixed Size: {spot_size} {symbol.replace('USDT','')}")
            else:
                base_coin = symbol.replace("USDT", "")
                assets = client.get_spot_assets(coin=base_coin)
                if assets and assets.get("data"):
                    avail = float(assets["data"][0]["available"])
                    if avail > 0:
                         # Fetch Precision dynamically
                         precision = 4 # Default fallback
                         try:
                             s_info = client.get_spot_symbol_info(symbol)
                             if s_info and 'quantityPrecision' in s_info:
                                 precision = int(s_info['quantityPrecision'])
                         except Exception as px:
                             print(f"Precision Fetch Error: {px}")
                         
                         import math
                         factor = 10 ** precision
                         # Floor to precision to avoid rounding up
                         floored_val = math.floor(avail * factor) / factor
                         spot_size = "{:.{p}f}".format(floored_val, p=precision)
                         print(f"Found {avail} {base_coin}. Sell Max (Prec: {precision}): {spot_size}")
                    else:
                        print(f"No {base_coin} balance to sell.")
                        return {"success": False, "status": "SKIPPED", "message": "Insufficient Balance"}
                else:
                     print(f"Could not verify {base_coin} balance. Trying configured size {size}")
        
        if spot_side:
            # Use Retry Logic Here Too
            resp = place_order_with_retry(client, symbol, spot_side, spot_size, "SPOT")
            print("Order Response:", resp)
            
            status = "FILLED" if resp and resp.get("code") == "00000" else "ERROR"
            info = str(resp) if resp else "No Response"
            
            supabase_manager.log_trade({
                "symbol": symbol,
                "side": signal,
                "size": str(spot_size),
                "price": "MARKET",
                "type": "LIVE",
                "status": status,
                "info": info
            })
            
            if status == "FILLED":
                telegram_bot.send_trade_alert(symbol, signal, str(spot_size), "MARKET", status, is_dry_run=False)
                return {"success": True, "status": "FILLED", "message": "Spot Trade Executed"}
            else:
                 friendly_error = format_api_error(resp)
                 telegram_bot.send_message(f"❌ *Trade Failed*\n\nError: {friendly_error}")
                 return {"success": False, "status": "ERROR", "message": friendly_error}
                 
        return {"success": False, "status": "Ignored", "message": "Invalid Spot Signal"}

    # --- FUTURES TRADING LOGIC ---
    try:
        # ... (Same Position Logic) ...
        if is_dry_run:
            current_position = None
        else:
            positions = client.get_positions(symbol)
            current_position = get_open_position_side(positions)
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return {"success": False, "status": "ERROR", "message": f"Position Check Error: {e}"}

    desired_side = "long" if signal == "open_long" else "short"

    # --- CLOSE ALL LOGIC ---
    if signal == "close_all":
        if is_dry_run:
             print(f"[DRY RUN] Would CLOSE ALL positions for {symbol}")
             return {"success": True, "status": "SIMULATED", "message": "Dry Run Close All"}
        
        try:
            positions = client.get_positions(symbol)
            if not positions:
                return {"success": True, "status": "SKIPPED", "message": "No positions found"}
            
            closed_cnt = 0
            for pos in positions:
                # Based on core/position.py structure
                p_size = float(pos.get("total", 0))
                p_side = pos.get("holdSide") # long/short
                
                if p_size > 0:
                     # Determine opposite side
                     # To close LONG -> SELL
                     # To close SHORT -> BUY
                     close_side = "sell" if p_side == "long" else "buy"
                     
                     print(f"Executing CLOSE ALL: Closing {p_side} ({p_size}) with {close_side}")
                     
                     # Force size to string format if needed, simplistic approach
                     # Ideally use precision formatting from logic below, but we'll try raw first or reuse helper?
                     # Let's trust place_order_with_retry to handle basic strings
                     
                     resp = place_order_with_retry(
                        client=client,
                        symbol=symbol,
                        side=close_side,
                        size=str(p_size),
                        product_type=product_type
                     )
                     print(f"Close Response: {resp}")
                     closed_cnt += 1
                     
            if closed_cnt > 0:
                 telegram_bot.send_message(f"📉 *Closed All Positions* for {symbol}")
                 return {"success": True, "status": "FILLED", "message": f"Closed {closed_cnt} positions"}
            else:
                 return {"success": True, "status": "SKIPPED", "message": "No open positions"}
                 
        except Exception as ex:
             print(f"Close All Error: {ex}")
             return {"success": False, "status": "ERROR", "message": str(ex)}

    # --- POSITION CHECK for OPEN ---
    if current_position == desired_side:
        print(f"[SKIP] Already in {current_position} position")
        return {"success": False, "status": "SKIPPED", "message": f"Already {desired_side}"}

    if current_position is not None:
        print(f"[SKIP] Position exists: {current_position}. Closing logic not implemented in simple executor.")
        return {"success": False, "status": "SKIPPED", "message": "Opposite position exists"}

    if is_dry_run:
        print(f"[DRY RUN] Would OPEN {desired_side} (Market Order)")
        
        supabase_manager.log_trade({
            "symbol": symbol,
            "side": signal,
            "size": str(size),
            "price": "MARKET",
            "type": "DRY_RUN",
            "status": "SIMULATED",
            "info": "Futures entry simulated"
        })
        telegram_bot.send_trade_alert(symbol, signal, str(size), "MARKET", "SIMULATED", is_dry_run=True)
        return {"success": True, "status": "SIMULATED", "message": "Dry Run Futures Triggered"}
    else:
        # Calculate Size in COINS (Contracts) if input is USDT
        actual_size = size
        try:
             # 1. Get Price
             ticker = client.get_ticker(symbol, product_type)
             current_price = 0.0
             if ticker and ticker.get("lastPr"):
                  current_price = float(ticker["lastPr"])
             
             if current_price > 0:
                  # 2. Get Symbol Rules (Min Size, Precision)
                  sym_info = client.get_symbol_info(symbol, product_type)
                  min_qty = 0.001 # Default fallback
                  precision = 3   # Default 3 decimals
                  
                  if sym_info:
                      # Bitget V2 usually provides 'minTradeNum' e.g. "0.001"
                      if sym_info.get("minTradeNum"):
                          min_qty = float(sym_info["minTradeNum"])
                          # Estimate precision from minTradeNum string length or value
                          # e.g. 0.001 -> 3 decimals
                          import decimal
                          d = decimal.Decimal(str(min_qty))
                          precision = abs(d.as_tuple().exponent) # simple way to get decimal places
                  
                  # 3. Calculate Raw Quantity
                  raw_qty = float(size) / current_price
                  
                  # 4. Round DOWN to precision (Floor)
                  # To avoid "Price moved too fast" due to insufficient margin for rounding up
                  factor = 10 ** precision
                  rounded_qty = int(raw_qty * factor) / factor
                  
                  print(f"DEBUG: Price={current_price}, SizeUSDT={size}, RawQty={raw_qty}, MinQty={min_qty}, RoundQty={rounded_qty}")
                  
                  if rounded_qty < min_qty:
                      min_usdt_req = min_qty * current_price
                      msg = f"Size too small. Calc: {rounded_qty} {symbol} < Min: {min_qty}. (Input: ${size}). Recommendation: Set Buy Size > ${min_usdt_req:.2f}"
                      print(f"🛑 {msg}")
                      return {"success": False, "status": "SKIPPED", "message": msg}
                  
                  # 5. Format String
                  actual_size = "{:.{p}f}".format(rounded_qty, p=precision)
                  print(f"EXEC: Sending Futures Order: {actual_size} {symbol.replace('USDT','')}")
             else:
                  print("⚠️ Could not fetch price. Defaulting to raw size.")
        except Exception as e:
             print(f"Size Calc Error: {e}")

        # Use Retry Logic
        resp = place_order_with_retry(
            client=client,
            symbol=symbol,
            side=signal,
            size=actual_size, 
            product_type=product_type
        )
        status = "FILLED" if resp and resp.get("code") == "00000" else "ERROR"
        info = str(resp) if resp else "No Response"
        
        supabase_manager.log_trade({
            "symbol": symbol,
            "side": signal,
            "size": str(size),
            "price": "MARKET",
            "type": "LIVE",
            "status": status,
            "info": info
        })
        telegram_bot.send_trade_alert(symbol, signal, str(size), "MARKET", status, is_dry_run=False)

        if client and status == "FILLED":
            # Log Balance Logic (simplified for brevity, main logic preserved above if needed)
            # Re-implementing balance log call
            try:
                 assets = client.get_spot_assets()
                 # Handle Bitget/GMX standardized response {'code':..., 'data': [...]}
                 asset_data = []
                 if isinstance(assets, dict):
                     asset_data = assets.get("data", [])
                 elif isinstance(assets, list):
                     asset_data = assets

                 if asset_data:
                     total = 0.0
                     breakdown = {}
                     for a in asset_data:
                         if a.get('coin') == 'USDT': 
                             total += float(a.get('available', 0))
                         breakdown[a.get('coin')] = float(a.get('available',0))
                     supabase_manager.log_balance(total, breakdown)
            except Exception as e: 
                print(f"Balance Log Error: {e}")
                pass
            return {"success": True, "status": "FILLED", "message": "Futures Trade Executed"}
        
        friendly_error = format_api_error(resp)
        return {"success": False, "status": "ERROR", "message": friendly_error}



