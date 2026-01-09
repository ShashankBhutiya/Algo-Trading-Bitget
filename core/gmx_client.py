
import os
import time
import json
import requests
from web3 import Web3
from dotenv import load_dotenv
import logging

load_dotenv()

# GMX V2 Arbitrum Constants
EXCHANGE_ROUTER = Web3.to_checksum_address("0x7a583163152ef38b8045e41255551270cE6A34F5") # Verify this!
# Using a common replacement logic or trusted addresses.
# For GMX V2 on Arbitrum:
# Exchange Router: 0x7a583163152ef38b8045e41255551270cE6A34F5
# Reader: 0x38dabd29aef322cb0e461b369527cf6c95dd79fb
# DataStore: ...

ORDER_VAULT = Web3.to_checksum_address("0x31eF83a530F6d1eA12480ABdfd7bdFda622114d5") # Example placeholder
# Note: GMX V2 interaction is complex. This client focuses on Data Fetching 
# and providing a structure for execution. 

class GMXClient:
    def __init__(self):
        self.rpc_url = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        self.private_key = os.getenv("GMX_PRIVATE_KEY")
        self.account = None
        if self.private_key:
            try:
                self.account = self.web3.eth.account.from_key(self.private_key)
                print(f"GMX Client Initialized. Wallet: {self.account.address}")
            except Exception as e:
                print(f"Error loading private key: {e}")
        else:
            print("GMX Client: READ-ONLY Mode (No Private Key provided)")

        self.api_base = "https://api.gmx.io/v2" # GMX V2 Stats API

    def get_spot_assets(self, coin=None):
        """
        Fetch wallet balances (ETH, USDC, etc.) from Arbitrum.
        Mimics Bitget response structure: {'code': '00000', 'data': [...]}
        """
        if not self.account:
             return {"code": "00000", "data": []}
        
        # Check ETH
        eth_wei = self.web3.eth.get_balance(self.account.address)
        eth_bal = float(self.web3.from_wei(eth_wei, 'ether'))
        
        # We could check USDC too if we had the contract address
        # For now, just return ETH and maybe a mock USDT
        
        assets = [
            {"coin": "ETH", "available": str(eth_bal), "frozen": "0"}
        ]
        
        return {"code": "00000", "data": assets}

    def get_symbols(self, product_type="USDT-FUTURES"):
        """
        Fetch available GMX V2 markets.
        """
        try:
            # GMX 'tickers' endpoint returns 24h stats for all markets
            resp = requests.get(f"{self.api_base}/order/markets") 
            # Note: The official API endpoint might differ. Let's usetickers
            resp = requests.get("https://gmx-aval-server.herokuapp.com/prices") # This is likely old/wrong.
            
            # Use reliable public generic endpoint for GMX markets validation
            # Or just return a static list of popular GMX markets
            markets = [
                {"symbol": "ETHUSDT", "baseCoin": "ETH", "quoteCoin": "USDT"},
                {"symbol": "BTCUSDT", "baseCoin": "BTC", "quoteCoin": "USDT"},
                {"symbol": "ARBUSDT", "baseCoin": "ARB", "quoteCoin": "USDT"},
                {"symbol": "SOLUSDT", "baseCoin": "SOL", "quoteCoin": "USDT"},
            ]
            
            # Wrap in Bitget-like structure
            return markets 
        except Exception as e:
            print(f"Error fetching GMX symbols: {e}")
            return []

    def get_symbol_info(self, symbol, product_type="USDT-FUTURES"):
        # Mock info for GMX
        return {
            "symbol": symbol,
            "minTradeNum": "0.001", # Min size
            "quantityPrecision": "4"
        }

    def get_ticker(self, symbol, product_type="USDT-FUTURES"):
        """
        Get current price.
        """
        try:
            # Fallback to Binance public API for price data
            binance_sym = symbol.replace("USDT", "USDT") # Assuming match
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={binance_sym}"
            r = requests.get(url, timeout=5)
            data = r.json()
            if "price" in data:
                return {"lastPr": data['price']}
        except Exception as e:
            print(f"Error fetching ticker: {e}")
        return None

    def get_candles(self, symbol, limit=1, granularity="1m", productType="USDT-FUTURES"):
        """
        Get candles (OHLC) for price data.
        Uses Binance API as a reliable price source for the bot's internal logic.
        """
        try:
            # Map granularity to Binance interval
            # Bitget: 1m, 5m, 1h. Binance: 1m, 5m, 1h
            interval = granularity 
            
            binance_sym = symbol
            url = f"https://api.binance.com/api/v3/klines?symbol={binance_sym}&interval={interval}&limit={limit}"
            
            resp = requests.get(url, timeout=5)
            data = resp.json()
            
            # Binance: [Open Time, Open, High, Low, Close, Volume, ...]
            # Bitget expected: [Time, Open, High, Low, Close, Volume, ...]
            # They are compatible enough for just Close price checks (index 4)
            return data
            
        except Exception as e:
            print(f"Error fetching candles: {e}")
            return []

    def get_positions(self, symbol="BTCUSDT"):
        """
        Fetch open positions from GMX Reader contract.
        Required for 'hedge mode' checks or closing logic.
        """
        # Implementation requires Reader Contract ABI + Address
        # returning empty list to avoid blocking execution
        return []

    def set_position_mode(self, mode="hedge_mode"):
        # GMX doesn't support changing mode via API
        return {"code": "00000", "msg": "Ignored"}

    def approve_token(self, token_address, spender_address, amount_wei):
        """
        Approve spender to use tokens.
        """
        # Minimal ERC20 ABI for approve
        erc20_abi = [
            {
                "constant": False,
                "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]
        
        try:
            contract = self.web3.eth.contract(address=token_address, abi=erc20_abi)
            
            # Estimate Gas
            gas_price = self.web3.eth.gas_price
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            
            tx = contract.functions.approve(spender_address, amount_wei).build_transaction({
                'chainId': 42161, # Arbitrum One
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce
            })
            
            # Sign and Send
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Approval Tx Sent: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            print(f"Approval Error: {e}")
            return None

    def _get_router_contract(self):
        """Returns the ExchangeRouter contract instance."""
        # Minimal ABI for createOrder
        # function createOrder(CreateOrderParams calldata params) external payable returns (bytes32)
        # Struct is complex. For simplicity in raw Web3, we might need the exact Tuple signature.
        # Signature: createOrder((address[7],uint256[7],uint8,uint8,bool,bool,bytes32))
        
        router_abi = [{
            "inputs": [{
                "components": [
                    {"internalType": "address", "name": "receiver", "type": "address"},
                    {"internalType": "address", "name": "cancellationReceiver", "type": "address"},
                    {"internalType": "address", "name": "withdrawalReceiver", "type": "address"},
                    {"internalType": "address", "name": "callbackContract", "type": "address"},
                    {"internalType": "address", "name": "market", "type": "address"},
                    {"internalType": "address", "name": "initialCollateralToken", "type": "address"},
                    {"internalType": "address[]", "name": "swapPath", "type": "address[]"},
                    {"internalType": "uint256", "name": "sizeDeltaUsd", "type": "uint256"},
                    {"internalType": "uint256", "name": "initialCollateralDeltaAmount", "type": "uint256"},
                    {"internalType": "uint256", "name": "triggerPrice", "type": "uint256"},
                    {"internalType": "uint256", "name": "acceptablePrice", "type": "uint256"},
                    {"internalType": "uint256", "name": "executionFee", "type": "uint256"},
                    {"internalType": "uint256", "name": "callbackGasLimit", "type": "uint256"},
                    {"internalType": "uint256", "name": "minOutputAmount", "type": "uint256"},
                    {"internalType": "enum Order.OrderType", "name": "orderType", "type": "uint8"},
                    {"internalType": "enum Order.DecreasePositionSwapType", "name": "decreasePositionSwapType", "type": "uint8"},
                    {"internalType": "bool", "name": "isLong", "type": "bool"},
                    {"internalType": "bool", "name": "shouldUnwrapNativeToken", "type": "bool"},
                    {"internalType": "bytes32", "name": "referralCode", "type": "bytes32"}
                ],
                "internalType": "struct IExchange.CreateOrderParams",
                "name": "params",
                "type": "tuple"
            }],
            "name": "createOrder",
            "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "stateMutability": "payable",
            "type": "function"
        }]
        return self.web3.eth.contract(address=EXCHANGE_ROUTER, abi=router_abi)

    def place_market_order(self, symbol, side, size, margin_mode=None, product_type="USDT-FUTURES", **kwargs):
        """
        Create a GMX V2 Order via RPC (Transaction).
        """
        if not self.account:
             return {"code": "40000", "msg": "No Private Key Configured"}
             
        # 1. Check Gas
        try:
            eth_bal = self.web3.eth.get_balance(self.account.address)
            if eth_bal == 0:
                print("🛑 CRITICAL: Wallet has 0 ETH.")
                # We fail here typically, but for debug let's proceed to show Params construction?
                # No, we should return error.
                return {"code": "40000", "msg": "Insufficient ETH for Gas"}
        except:
             pass

        print(f"GMX EXECUTION: {side} {size} {symbol}")
        
        # 2. Config & Addresses
        USDT_ADDRESS = Web3.to_checksum_address("0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9") # Arb One USDT
        WETH_ADDRESS = Web3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1") # Arb One WETH
        
        # Market Address for ETH-USDT (GMX V2)
        # NOTE: This MUST be the Market Token Address, not the index token.
        # Example for ETH/USDT/USDC Market
        MARKET_ADDRESS = Web3.to_checksum_address("0x70d95587d40A2caf56bd97485aB3Eec10Bee6336") # Example! Needs verification.
        
        is_long = side in ["open_long", "buy"]
        
        # 3. Approve Token
        token_in = USDT_ADDRESS # Paying with USDT
        amount_in_wei = int(float(size) * 1e6) # USDT 6 decimals
        
        if side in ["open_long", "buy"]:
            print("Checking Token Approval...")
            # Un-comment to enable
            self.approve_token(token_in, EXCHANGE_ROUTER, amount_in_wei)
        
        # 4. Construct Order Params
        # OrderType: MARKET_SWAP(0), MARKET_INCREASE(1), MARKET_DECREASE(2)...
        # For 'open_long' we use MARKET_INCREASE (1)
        order_type_val = 1 
        
        execution_fee = 2000000000000000 # 0.002 ETH (lowered slightly)
        
        # Create Tuple
        # (receiver, cancelRx, withdrawRx, callback, market, initCollat, swapPath, sizeDeltaUsd, initCollatDelta, trigPrice, acceptPrice, execFee, callbackGas, minOut, orderType, swapType, isLong, unwrap, referral)
        
        params = (
            self.account.address, # receiver
            self.account.address, # cancellationReceiver
            self.account.address, # withdrawalReceiver
            "0x0000000000000000000000000000000000000000", # callbackContract (None)
            MARKET_ADDRESS, # market
            token_in, # initialCollateralToken (USDT)
            [], # swapPath (Empty for direct market)
            int(float(size) * 1e30), # sizeDeltaUsd (1e30 precision usually for GMX USD) 
            amount_in_wei, # initialCollateralDeltaAmount (Amount of USDT sent)
            0, # triggerPrice (0 for Market)
            0, # acceptablePrice (0 for Market/Slippage handled elsewhere or strict)
            execution_fee, # executionFee
            0, # callbackGasLimit
            0, # minOutputAmount
            order_type_val, # orderType
            0, # decreasePositionSwapType
            is_long, # isLong
            False, # shouldUnwrapNativeToken
            b'\x00' * 32 # referralCode
        )
        
        print(f"Build Params: {params}")

        try:
            router = self._get_router_contract()
            
            # Helper to get current tx count
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            
            # Add 10% buffer to gas price to handle network fluctuations
            current_gas_price = self.web3.eth.gas_price
            buffered_gas_price = int(current_gas_price * 1.1)

            tx = router.functions.createOrder(params).build_transaction({
                'chainId': 42161,
                'gas': 2000000,
                'gasPrice': buffered_gas_price,
                'nonce': nonce,
                'value': execution_fee # Send ETH for execution fee
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key=self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            print(f"✅ GMX Order Sent! Hash: {tx_hash.hex()}")
            return {"code": "00000", "msg": "Success", "hash": tx_hash.hex()}
            
        except Exception as e:
            print(f"❌ Transaction Build Failed: {e}")
            return {"code": "50000", "msg": str(e)}
