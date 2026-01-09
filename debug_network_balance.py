
import os
import sys
from web3 import Web3
from dotenv import load_dotenv

def check_networks():
    load_dotenv()
    pk = os.getenv("GMX_PRIVATE_KEY")
    if not pk:
        print("No Private Key found.")
        return

    # derived address
    tmp_w3 = Web3()
    account = tmp_w3.eth.account.from_key(pk)
    address = account.address
    print(f"🔍 Inspecting Funds for: {address}")
    
    # 1. ARBITRUM ONE
    arb_rpc = "https://arb1.arbitrum.io/rpc"
    try:
        w3 = Web3(Web3.HTTPProvider(arb_rpc))
        if w3.is_connected():
            eth = w3.from_wei(w3.eth.get_balance(address), 'ether')
            blk = w3.eth.block_number
            print(f"\n[ARBITRUM] Connected (Block {blk})")
            print(f"   ETH Balance: {eth}")
            
            # USDT arb
            usdt = w3.eth.contract(address="0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", abi=[{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}])
            bal = usdt.functions.balanceOf(address).call()
            print(f"   USDT Balance: {bal / 1e6}")
            
            # USDC.e (Arb)
            usdc = w3.eth.contract(address="0xFF970A61a04b1cA14834A43f5dE4533eBDDB5CC8", abi=[{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}])
            bal_c = usdc.functions.balanceOf(address).call()
            print(f"   USDC.e Balance: {bal_c / 1e6}")
            
        else:
            print("\n[ARBITRUM] Connection Failed")
    except Exception as e:
        print(f"[ARBITRUM] Error: {e}")

    # 2. AVALANCHE C-CHAIN
    avax_rpc = "https://api.avax.network/ext/bc/C/rpc"
    try:
        w3 = Web3(Web3.HTTPProvider(avax_rpc))
        if w3.is_connected():
            # Avax
            avax = w3.from_wei(w3.eth.get_balance(address), 'ether')
            print(f"\n[AVALANCHE] Connected")
            print(f"   AVAX Balance: {avax}")
            
            # USDt (Avax)
            usdt_avax = w3.eth.contract(address="0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7", abi=[{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}])
            bal = usdt_avax.functions.balanceOf(address).call()
            print(f"   USDt Balance: {bal / 1e6}")
            
        else:
            print("\n[AVALANCHE] Connection Failed")
    except Exception as e:
        print(f"[AVALANCHE] Error: {e}")

    # 3. ETHEREUM MAINNET
    eth_rpc = "https://rpc.ankr.com/eth"
    try:
        w3 = Web3(Web3.HTTPProvider(eth_rpc))
        if w3.is_connected():
            eth = w3.from_wei(w3.eth.get_balance(address), 'ether')
            print(f"\n[ETHEREUM MAINNET] Connected")
            print(f"   ETH Balance: {eth}")
    except:
        pass

    # 4. OPTIMISM
    opt_rpc = "https://mainnet.optimism.io"
    try:
        w3 = Web3(Web3.HTTPProvider(opt_rpc))
        if w3.is_connected():
            eth = w3.from_wei(w3.eth.get_balance(address), 'ether')
            if eth > 0:
                print(f"\n[OPTIMISM] Connected")
                print(f"   ETH Balance: {eth}")
    except:
        pass

    # 5. BASE
    base_rpc = "https://mainnet.base.org"
    try:
        w3 = Web3(Web3.HTTPProvider(base_rpc))
        if w3.is_connected():
            eth = w3.from_wei(w3.eth.get_balance(address), 'ether')
            if eth > 0:
                print(f"\n[BASE] Connected")
                print(f"   ETH Balance: {eth}")
    except:
        pass
        
    # 6. POLYGON
    poly_rpc = "https://polygon-rpc.com"
    try:
        w3 = Web3(Web3.HTTPProvider(poly_rpc))
        if w3.is_connected():
            matic = w3.from_wei(w3.eth.get_balance(address), 'ether')
            if matic > 0:
                print(f"\n[POLYGON] Connected")
                print(f"   MATIC Balance: {matic}")
    except:
        pass

    # 7. BSC
    bsc_rpc = "https://bsc-dataseed.binance.org"
    try:
        w3 = Web3(Web3.HTTPProvider(bsc_rpc))
        if w3.is_connected():
            bnb = w3.from_wei(w3.eth.get_balance(address), 'ether')
            if bnb > 0:
                print(f"\n[BSC] Connected")
                print(f"   BNB Balance: {bnb}")
    except:
        pass

if __name__ == "__main__":
    check_networks()
