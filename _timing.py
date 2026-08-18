
import time, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
from stock_signals.screener import _get_market_codes, scan_parallel, ScanConfig
from stock_signals.indicators import fetch_kline

# Time market codes
t = time.time()
codes = _get_market_codes('A')
print(f"Market codes A: {len(codes)} in {time.time()-t:.1f}s")

# Time single kline fetch
t = time.time()
df = fetch_kline(codes[0], '1d', 100)
print(f"K-line fetch: {len(df)} rows in {time.time()-t:.1f}s")

# Time weekly kline
t = time.time()
dfw = fetch_kline(codes[0], '1w', 50)
print(f"Weekly kline: {len(dfw)} rows in {time.time()-t:.1f}s")

# Time monthly kline
t = time.time()
dfm = fetch_kline(codes[0], '1M', 30)
print(f"Monthly kline: {len(dfm)} rows in {time.time()-t:.1f}s")

print(f"Total per stock (3 kline fetches): ~{time.time()-t:.1f}s (estimated)")
