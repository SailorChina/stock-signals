
import time, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
from stock_signals.screener import scan_parallel, ScanConfig
config = ScanConfig()
config.max_per_market = 1
t0 = time.time()
result = scan_parallel(['A', 'HK', 'US'], config=config)
elapsed = time.time() - t0
print(f"Time: {elapsed:.1f}s")
for m in ['A', 'HK', 'US']:
    picks = result['picks'].get(m, [])
    print(f"  {m}: picks={len(picks)}")
print('DONE')
