
import time, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
from stock_signals.screener import scan_parallel, ScanConfig
config = ScanConfig()
config.max_per_market = 5
t0 = time.time()
result = scan_parallel(['A', 'HK', 'US'], config=config)
elapsed = time.time() - t0
print(f"Total scan time: {elapsed:.1f}s")
for m in ['A', 'HK', 'US']:
    picks = result['picks'].get(m, [])
    watch = result['watchlist'].get(m, [])
    print(f"  {m}: picks={len(picks)} watchlist={len(watch)}")
    for p in picks[:3]:
        print(f"    {p.code}: score={p.score} rating={p.rating}")
print('DONE')
