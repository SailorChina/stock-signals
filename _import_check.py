
import sys, os
sys.path.insert(0, 'D:/Backup/Documents/ChatGPT/AI/stock-signals')

# Clear proxy
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'

print('=== Import Check ===')
try:
    from stock_signals.indicators import fetch_kline, compute_indicators, signal_summary
    print('indicators: OK')
except Exception as e:
    print(f'indicators: ERROR {e}')

try:
    from stock_signals.hot_fetcher import fetch_hot_stocks
    print('hot_fetcher: OK')
except Exception as e:
    print(f'hot_fetcher: ERROR {e}')

try:
    from stock_signals.scoring import compute_rating
    print('scoring: OK')
except Exception as e:
    print(f'scoring: ERROR {e}')

try:
    from stock_signals.screener import STOCK_POOLS
    print('screener: OK, pools:', {k: len(v) for k,v in STOCK_POOLS.items()})
except Exception as e:
    print(f'screener: ERROR {e}')

print()
print('=== K-line Test ===')
import time
# Test A-share K-line
t0 = time.time()
df = fetch_kline('SH.600519')
print(f'A-share SH.600519: {len(df)} rows, {time.time()-t0:.2f}s')

# Test HK K-line
t0 = time.time()
df = fetch_kline('HK.00700')
print(f'HK HK.00700: {len(df)} rows, {time.time()-t0:.2f}s')

# Test US K-line
t0 = time.time()
df = fetch_kline('US.AAPL')
print(f'US US.AAPL: {len(df)} rows, {time.time()-t0:.2f}s')

print()
print('=== Hot Stocks Test ===')
t0 = time.time()
a_hot = fetch_hot_stocks('A', 10)
print(f'A hot: {len(a_hot)} stocks, {time.time()-t0:.2f}s, sample: {a_hot[:3]}')

t0 = time.time()
hk_hot = fetch_hot_stocks('HK', 10)
print(f'HK hot: {len(hk_hot)} stocks, {time.time()-t0:.2f}s, sample: {hk_hot[:3]}')

t0 = time.time()
us_hot = fetch_hot_stocks('US', 10)
print(f'US hot: {len(us_hot)} stocks, {time.time()-t0:.2f}s, sample: {us_hot[:3]}')
