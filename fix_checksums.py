
from web3 import Web3

addresses = {
    "EXCHANGE_ROUTER": "0x7a583163152ef38b8045e41255551270cE6A34F5",
    "ORDER_VAULT": "0x31eF83a530F6d1eA12480ABdfd7bdFda622114d5",
    "USDT_ADDRESS": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
    "WETH_ADDRESS": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    "MARKET_ADDRESS": "0x70d95587d40A2caf56bd97485aB3Eec10Bee6336"
}

print("Correct Checksum Addresses:")
for name, addr in addresses.items():
    try:
        checksummed = Web3.to_checksum_address(addr)
        print(f"{name} = \"{checksummed}\"")
    except Exception as e:
        print(f"Error converting {name}: {e}")
