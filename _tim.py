
import time, sys
sys.path.insert(0, '.')
from stock_signals.indicators import fetch_kline
t = time.time()
df = fetch_kline('SH.600519', '1d', 10)
print(f'fetch_kline A: {len(df)} rows in {time.time()-t:.1f}s')
t = time.time()
df2 = fetch_kline('SH.600519', '1w', 20)
print(f'fetch_kline A weekly: {len(df2)} rows in {time.time()-t:.1f}s')
t = time.time()
df3 = fetch_kline('SH.600519', '1M', 12)
print(f'fetch_kline A monthly: {len(df3)} rows in {time.time()-t:.1f}s')
