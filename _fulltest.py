
import sys, time, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')

print('=== Step 1: Test fetch_kline ===')
from stock_signals.indicators import fetch_kline
for n, c in [('A','SH.600519'),('HK','HK.00700'),('US','US.AAPL')]:
    df = fetch_kline(c, '1d', 10)
    print(f'  {n}: {len(df)} rows')

print('\n=== Step 2: Test scan 3-market ===')
from stock_signals.screener import scan_parallel, ScanConfig
config = ScanConfig()
config.max_per_market = 1
t0 = time.time()
result = scan_parallel(['A', 'HK', 'US'], config=config)
elapsed = time.time() - t0
print(f'  Time: {elapsed:.1f}s')
for m in ['A', 'HK', 'US']:
    picks = result['picks'].get(m, [])
    print(f'  {m}: picks={len(picks)}')
    for p in picks[:2]:
        print(f'    {p.code}: score={p.score} rating={p.rating}')
print('\nDONE')
