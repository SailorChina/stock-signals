
import time, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
from stock_signals.indicators import fetch_kline

code = 'SH.600519'
t = time.time()
df = fetch_kline(code, '1d', 100)
print(f'daily: {len(df)} rows, {time.time()-t:.1f}s')
t = time.time()
dfw = fetch_kline(code, '1w', 50)
print(f'weekly: {len(dfw)} rows, {time.time()-t:.1f}s')
t = time.time()
dfm = fetch_kline(code, '1M', 30)
print(f'monthly: {len(dfm)} rows, {time.time()-t:.1f}s')
print(f'total per stock: ~{(time.time()-t)*3:.1f}s estimated')
