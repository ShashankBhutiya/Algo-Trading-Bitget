# core/bitget_client.py

import time
import hmac
import hashlib
import base64
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BITGET_API_KEY")
SECRET = os.getenv("BITGET_SECRET")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")

BASE_URL = "https://api.bitget.com"


import urllib.parse

class BitgetClient:   # 👈 THIS NAME MUST MATCH EXACTLY

    def __init__(self):
        self.session = requests.Session()
        # Retry strategy: 3 retries, exponential backoff (1s, 2s, 4s), handle server errors
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def _sign(self, timestamp, method, path, body=""):
        msg = f"{timestamp}{method}{path}{body}"
        mac = hmac.new(SECRET.encode(), msg.encode(), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode()

    def _headers(self, method, path, body=""):
        ts = str(int(time.time() * 1000))
        sign = self._sign(ts, method, path, body)
        return {
            "ACCESS-KEY": API_KEY,
            "ACCESS-SIGN": sign,
            "ACCESS-TIMESTAMP": ts,
            "ACCESS-PASSPHRASE": PASSPHRASE,
            "Content-Type": "application/json"
        }

    def get_candles(self, symbol="BTCUSDT", granularity="1m", limit=100, productType="USDT-FUTURES"):
        path = "/api/v2/mix/market/candles"
        if productType == "SPOT":
             path = "/api/v2/spot/market/candles"
             # Spot uses "1min" instead of "1m"
             if granularity == "1m":
                 granularity = "1min"
        
        params = {
            "symbol": symbol,
            "granularity": granularity,
            "limit": limit
        }
        if productType != "SPOT":
            params["productType"] = productType

        try:
            res = self.session.get(BASE_URL + path, params=params, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"Request error in get_candles: {e}")
            return None
        data = res.json()


        # print("FULL API RESPONSE:", data)

        if data.get("code") != "00000":
            return None

        return data["data"]

    def get_positions(self, symbol="BTCUSDT"):
        path = "/api/v2/mix/position/single-position"
        params = {
            "symbol": symbol,
            "productType": "USDT-FUTURES",
            "marginCoin": "USDT"
        }
        
        query_string = urllib.parse.urlencode(params)
        full_path = f"{path}?{query_string}"

        headers = self._headers("GET", full_path)
        try:
            res = self.session.get(BASE_URL + full_path, headers=headers, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"Request error in get_positions: {e}")
            return None
        data = res.json()

        if data.get("code") != "00000":
            print("Position API error:", data)
            return None

        return data["data"]

    def place_market_order(self, symbol, side, size, margin_mode=None, product_type="USDT-FUTURES"):
        if product_type == "SPOT":
             path = "/api/v2/spot/trade/place-order"
             
             # Map Futures signals to Spot sides
             spot_side = side
             if side in ["open_long", "buy"]:
                 spot_side = "buy"
             elif side in ["close_long", "sell", "open_short"]: # Treat open_short as sell for Spot (exiting base curr)? Or invalid? Usually sell.
                 spot_side = "sell"
                 
             
             # Spot logic: Buy=USDT amount, Sell=Coin amount. 
             # 4 decimals is generally safe for USDT and major coins.
             # Use the size value as-is, assuming upstream logic handled precision.
             # If it's a float, typical formatting. If string, pass through.
             fmt_size = str(size)
             if isinstance(size, float):
                 # Fallback if float passed: simple clean string
                 fmt_size = "{:.4f}".format(size).rstrip('0').rstrip('.')
             
             # Spot payload
             body = {
                 "symbol": symbol,
                 "side": spot_side, # buy/sell
                 "orderType": "market",
                 "force": "normal",
                 "size": fmt_size
             }
        else:
            # Futures Mix Payload
            path = "/api/v2/mix/order/place-order"
            
            # Mapping for Hedge Mode V2 (Futures only)
            final_side = side
            trade_side = None

            if side == "open_long":
                final_side = "buy"
                trade_side = "open"
            elif side == "open_short":
                final_side = "sell"
                trade_side = "open"
            elif side == "close_long":
                final_side = "sell"
                trade_side = "close"
            elif side == "close_short":
                final_side = "buy"
                trade_side = "close"
            elif side in ["buy", "sell"]:
                final_side = side
            # One-Way mode usually doesn't need tradeSide, or defaults.
            
        
            body = {
                "symbol": symbol,
                "productType": product_type,
                "marginCoin": "USDT",
                "orderType": "market",
                "side": final_side,
                "size": "{:.6f}".format(float(size)) # Format to avoid scientific notation
            }
            
            if trade_side:
                body["tradeSide"] = trade_side

            if margin_mode:
                 body["marginMode"] = margin_mode
        
        print("DEBUG: Sending Body:", json.dumps(body, indent=2))
        
        json_body = json.dumps(body, separators=(',', ':'))
        headers = self._headers("POST", path, json_body)
        
        try:
            res = self.session.post(BASE_URL + path, data=json_body, headers=headers, timeout=10)
            return res.json()
        except requests.exceptions.RequestException as e:
            print(f"Order error: {e}")
            return None

    def get_spot_assets(self, coin=None):
        path = "/api/v2/spot/account/assets"
        params = {}
        if coin:
            params["coin"] = coin
            
        full_path = path
        if params:
             import urllib.parse
             full_path += "?" + urllib.parse.urlencode(params)

        headers = self._headers("GET", full_path)
        try:
            res = self.session.get(BASE_URL + full_path, headers=headers, timeout=10)
            return res.json()
        except Exception as e:
            print(f"Asset Check Error: {e}")
            return None

    def set_position_mode(self, mode="hedge_mode"):
        path = "/api/v2/mix/account/set-position-mode"
        body = {
            "productType": "USDT-FUTURES",
            "posMode": mode
        }
        json_body = json.dumps(body)
        headers = self._headers("POST", path, json_body)
        try:
             res = self.session.post(BASE_URL + path, data=json_body, headers=headers, timeout=10)
             return res.json()
        except Exception as e:
            print(f"Set Mode Error: {e}")
            return None

    def set_leverage(self, symbol, leverage, margin_coin="USDT", product_type="USDT-FUTURES"):
        path = "/api/v2/mix/account/set-leverage"
        body = {
            "symbol": symbol,
            "productType": product_type,
            "marginCoin": margin_coin,
            "leverage": str(leverage)
            # In Hedge mode, this sets both long and short leverage if not split.
            # If we needed distinct, we'd use longLeverage/shortLeverage. 
            # For simplicity, we assume symmetric leverage.
        }
        json_body = json.dumps(body)
        headers = self._headers("POST", path, json_body)
        try:
             res = self.session.post(BASE_URL + path, data=json_body, headers=headers, timeout=10)
             return res.json()
        except Exception as e:
            print(f"Set Leverage Error: {e}")
            return None

    def get_symbols(self, product_type="USDT-FUTURES"):
        path = "/api/v2/mix/market/contracts"
        params = {"productType": product_type}
        
        try:
            res = self.session.get(BASE_URL + path, params=params, timeout=10)
            data = res.json()
            if data.get("code") == "00000":
                return data["data"]
            return []
        except Exception as e:
            print(f"Get Symbols Error: {e}")
            return []

    def get_spot_symbol_info(self, symbol):
        """Fetch spot symbol details like precision and min size."""
        path = "/api/v2/spot/public/symbols"
        params = {"symbol": symbol}
        try:
            res = self.session.get(BASE_URL + path, params=params, timeout=10)
            data = res.json()
            if data.get("code") == "00000" and data.get("data"):
                 # Returns list of symbols. Filter for exact match just in case.
                 for s in data["data"]:
                     if s["symbol"] == symbol:
                         return s
            return None
        except Exception as e:
            print(f"Get Spot Symbol Info Error: {e}")
            return None

    def get_symbol_info(self, symbol, product_type="USDT-FUTURES"):
        """Fetch specific contract details like min size and precision."""
        if product_type == "SPOT":
            return self.get_spot_symbol_info(symbol)
            
        try:
            # We have to fetch all and filter because typical Get Contract endpoint is list-based
            contracts = self.get_symbols(product_type)
            if not contracts: return None
            
            for c in contracts:
                if c["symbol"] == symbol:
                    return c
            return None
        except Exception as e:
            print(f"Get Symbol Info Error: {e}")
            return None

    def get_ticker(self, symbol, product_type="USDT-FUTURES"):
        path = "/api/v2/mix/market/ticker"
        params = {"symbol": symbol, "productType": product_type}
        
        try:
            res = self.session.get(BASE_URL + path, params=params, timeout=5)
            data = res.json()
            if data.get("code") == "00000" and data.get("data"):
                return data["data"][0] # Returns dict with 'lastPr', etc.
            return None
        except Exception as e:
             print(f"Get Ticker Error: {e}")
             return None
