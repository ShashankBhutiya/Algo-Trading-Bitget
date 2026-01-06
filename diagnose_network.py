import socket
import os
import requests
import time
from dotenv import load_dotenv

# Load .env first as the app does
load_dotenv()

print("Environment Variables (Proxy related):")
found_proxy = False
for k, v in os.environ.items():
    if "PROXY" in k.upper():
        print(f"{k}: {v}")
        found_proxy = True

if not found_proxy:
    print("No PROXY related environment variables found.")

print("\nAttempting DNS resolution for api.bitget.com...")
try:
    info = socket.getaddrinfo("api.bitget.com", 443)
    print(f"Success: {info}")
except Exception as e:
    print(f"DNS Resolution Failed: {e}")

print("\nAttempting Request to api.bitget.com (5 iterations)...")
for i in range(5):
    try:
        print(f"Iteration {i+1}: ", end="")
        res = requests.get("https://api.bitget.com/api/v2/mix/market/candles?symbol=BTCUSDT&granularity=1m&limit=1", timeout=5)
        print(f"Status: {res.status_code}")
    except Exception as e:
        print(f"Failed: {e}")
    time.sleep(1)
