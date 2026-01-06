
import os
import time
import hmac
import hashlib
import base64
import requests
from dotenv import load_dotenv

# Load env
load_dotenv()

API_KEY = os.getenv("BITGET_API_KEY")
SECRET = os.getenv("BITGET_SECRET")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")

print("--- Bitget Auth Debugger ---")
print(f"API_KEY Loaded: {'Yes' if API_KEY else 'NO'}")
print(f"SECRET Loaded: {'Yes' if SECRET else 'NO'}")
print(f"PASSPHRASE Loaded: {'Yes' if PASSPHRASE else 'NO'}")

if not all([API_KEY, SECRET, PASSPHRASE]):
    print("❌ ERROR: Missing one or more environment variables in .env file.")
    exit()

BASE_URL = "https://api.bitget.com"

def get_sign(timestamp, method, path, body=""):
    msg = f"{timestamp}{method}{path}{body}"
    mac = hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def test_auth():
    # Endpoint: Spot Assets (Simple private endpoint)
    path = "/api/v2/spot/account/assets"
    method = "GET"
    
    timestamp = str(int(time.time() * 1000))
    sign = get_sign(timestamp, method, path, "")
    
    headers = {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json"
    }
    
    print(f"\nAttempting request to {path}...")
    print(f"Timestamp: {timestamp}")
    
    try:
        resp = requests.get(BASE_URL + path, headers=headers)
        print(f"Status Code: {resp.status_code}")
        print(f"Response Body: {resp.text}")
        
        if "40014" in resp.text:
             print("\n❌ Error 40014: Invalid Sign. Usually means Incorrect Secret Key.")
        elif "40017" in resp.text:
             print("\n❌ Error 40017: Invalid Passphrase.")
        elif "40004" in resp.text:
             print("\n❌ Error 40004: Invalid API Key (not found or IP mismatch).")
        elif "00000" in resp.text:
             print("\n✅ SUCCESS! Authentication is working.")
        else:
             print("\n⚠️ Unknown Response. Check message above.")
             
    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    test_auth()
