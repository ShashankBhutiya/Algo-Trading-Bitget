from core.bitget_client import BitgetClient
from core.strategy import ema_strategy

client = BitgetClient()
candles = client.get_candles()

signal = ema_strategy(candles)
print("Strategy signal:", signal)
