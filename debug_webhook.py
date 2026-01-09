
import requests
import json
import time

def test_webhook():
    print("--- 📡 Testing Webhook Bot Trigger 📡 ---")
    
    url = "http://127.0.0.1:5000/webhook"
    
    # Payload simulating TradingView
    # Using 'SOLUSDT' to avoid duplicate signal checks against BTC/ETH used in previous tests
    payload = {
        "signal": "open_long",
        "symbol": "SOLUSDT",
        "product_type": "USDT-FUTURES",
        "passphrase": "your_secure_passphrase_here", # Bot will ignore if ENV not set
        "buy_size_usdt": "12.0",
        "price": "145.50" 
    }
    
    print(f"Target: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start = time.time()
        resp = requests.post(url, json=payload, timeout=10)
        duration = time.time() - start
        
        print(f"\nResponse Time: {duration:.2f}s")
        print(f"Status Code: {resp.status_code}")
        try:
            print(f"Response Body: {json.dumps(resp.json(), indent=2)}")
        except:
            print(f"Response Text: {resp.text}")
            
    except Exception as e:
        print(f"❌ Request Failed: {e}")
        print("Ensure 'python run_bot.py' is running!")

if __name__ == "__main__":
    test_webhook()
