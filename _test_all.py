
import time, sys
sys.path.insert(0, '.')
from stock_signals.screener import _get_market_codes, scan_parallel, ScanConfig
from stock_signals.hot_fetcher import fetch_a_hot_stocks
from stock_signals.indicators import fetch_kline

print('=== Test 1: Hot stock fetch ===')
t0 = time.time()
codes = fetch_a_hot_stocks(5)
print(f'Got {len(codes)} codes in {time.time()-t0:.1f}s: {codes}')

print()
print('=== Test 2: Market codes ===')
t0 = time.time()
a = _get_market_codes('A')
hk = _get_market_codes('HK')
us = _get_market_codes('US')
print(f'A:{len(a)} HK:{len(hk)} US:{len(us)} in {time.time()-t0:.1f}s')
print(f'A sample: {a[:3]}')

print()
print('=== Test 3: K-line fetch ===')
t0 = time.time()
df = fetch_kline(codes[0], '1d', 100)
print(f'{codes[0]}: {len(df)} rows in {time.time()-t0:.1f}s')

print()
print('=== Test 4: Quick A-market scan (5 stocks) ===')
t0 = time.time()
config = ScanConfig()
config.max_per_market = 3
result = scan_parallel(['A'], config=config)
elapsed = time.time() - t0
print(f'Scan time: {elapsed:.1f}s')
print(f'Picks: {len(result["picks"].get("A", []))}')
print('DONE')
