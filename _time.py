
import time, sys
sys.path.insert(0, '.')
from stock_signals.indicators import fetch_kline
for i in range(3):
    t = time.time()
    df = fetch_kline('SH.600519', '1d', 10)
    print(f'Call {i+1}: {len(df)} rows in {time.time()-t:.1f}s')
