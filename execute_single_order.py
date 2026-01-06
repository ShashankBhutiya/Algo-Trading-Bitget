
import argparse
import sys
from core.bitget_client import BitgetClient

def run_single_order(symbol, side, size, margin_mode=None, leverage=None, dry_run=False, product_type="USDT-FUTURES"):
    """
    Executes a single market order.
    """
    print(f"--- Single Order Execution ---")
    print(f"Symbol:   {symbol}")
    print(f"Type:     {product_type}")
    print(f"Side:     {side}")
    print(f"Size:     {size}")
    print(f"Margin:   {margin_mode}")
    print(f"Leverage: {leverage}")
    print(f"Dry Run:  {dry_run}")
    print(f"------------------------------")

    if dry_run:
        print("[DRY RUN] Skipping API call. Order successfully SIMULATED.")
        return

    try:
        client = BitgetClient()
        
        if leverage and product_type != "SPOT":
            print(f"Setting leverage to {leverage}x...")
            lev_resp = client.set_leverage(symbol, leverage, product_type=product_type)
            print("Leverage Response:", lev_resp)
            
        response = client.place_market_order(symbol=symbol, side=side, size=size, margin_mode=margin_mode, product_type=product_type)
        print("API Response:", response)
        
        if response and response.get("code") == "00000":
            print("Order placed successfully!")
        elif response and response.get("code") == "400172":
            print(f"Order placement FAILED: {response.get('msg')}")
            print("HINT: Error '400172: side mismatch' usually means your account is in ONE-WAY MODE but you tried to use HEDGE MODE keys (open_long/open_short).")
            print("Try using '--side buy' or '--side sell' instead, OR switch your Bitget account to Hedge Mode.")
        else:
            print(f"Order placement FAILED. Response: {response}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute a single order on Bitget via CLI")
    
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol (default: BTCUSDT)")
    parser.add_argument("--side", type=str, default="open_long", help="Order side: 'open_long', 'open_short' (HEDGE) or 'buy', 'sell' (ONE-WAY)")
    parser.add_argument("--size", type=float, default=0.001, help="Order size (Min 0.001 for BTCUSDT)")
    parser.add_argument("--product-type", type=str, default="USDT-FUTURES", help="Product type: 'USDT-FUTURES' or 'SPOT'")
    parser.add_argument("--margin-mode", type=str, default=None, help="Margin mode: 'crossed', 'isolated', or leave empty to use Account Default")
    parser.add_argument("--leverage", type=int, default=None, help="Set leverage (e.g. 5, 10, 50, 100)")
    parser.add_argument("--dry-run", action="store_true", help="Run in simulation mode")

    args = parser.parse_args()
    
    if args.size < 0.001:
        print("WARNING: Size 0.001 is typically the minimum for BTCUSDT. Your order may fail with error 45111.")

    run_single_order(args.symbol, args.side, args.size, args.margin_mode, args.leverage, args.dry_run, args.product_type)
