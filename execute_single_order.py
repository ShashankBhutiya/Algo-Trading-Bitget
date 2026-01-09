
import argparse
import sys
from core.gmx_client import GMXClient

def run_single_order(symbol, side, size, margin_mode=None, leverage=None, dry_run=False, product_type="USDT-FUTURES"):
    """
    Executes a single market order on GMX.
    """
    print(f"--- Single Order Execution (GMX) ---")
    print(f"Symbol:   {symbol}")
    print(f"Type:     {product_type}")
    print(f"Side:     {side}")
    print(f"Size:     {size}")
    print(f"Dry Run:  {dry_run}")
    print(f"------------------------------------")

    if dry_run:
        print("[DRY RUN] Skipping API call. Order successfully SIMULATED.")
        return

    try:
        client = GMXClient()
        
        # GMX Doesn't set leverage per order in the same way, usually determined by collateral/size in Position Router
        if leverage:
            print(f"Note: Leverage ({leverage}x) is handled by collateral params in GMX V2. Ensure logic adapts.")

        response = client.place_market_order(symbol=symbol, side=side, size=size, margin_mode=margin_mode, product_type=product_type)
        print("API Response:", response)
        
        if response and response.get("code") == "00000":
            print("Order placed successfully (or Mocked)!")
        else:
            print(f"Order placement FAILED. Response: {response}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute a single order on GMX via CLI")
    
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="Trading symbol (default: BTCUSDT)")
    parser.add_argument("--side", type=str, default="open_long", help="Order side: 'open_long', 'open_short' (HEDGE) or 'buy', 'sell' (ONE-WAY)")
    parser.add_argument("--size", type=float, default=0.001, help="Order size (Min 0.001 for BTCUSDT)")
    parser.add_argument("--product-type", type=str, default="USDT-FUTURES", help="Product type: 'USDT-FUTURES' or 'SPOT'")
    parser.add_argument("--margin-mode", type=str, default=None, help="Ignored in GMX")
    parser.add_argument("--leverage", type=int, default=None, help="Ignored in GMX Stub")
    parser.add_argument("--dry-run", action="store_true", help="Run in simulation mode")

    args = parser.parse_args()
    
    run_single_order(args.symbol, args.side, args.size, args.margin_mode, args.leverage, args.dry_run, args.product_type)
