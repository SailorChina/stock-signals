
import sys; sys.path.insert(0, '.')
from stock_signals.indicators import fetch_kline
print(len(fetch_kline('SH.600519', '1d', 10)))
