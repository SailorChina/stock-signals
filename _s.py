
import time, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
from stock_signals.screener import scan_parallel, ScanConfig
config = ScanConfig()
config.max_per_market = 1
t0 = time.time()
result = scan_parallel(['A'], config=config)
print(f"Time: {time.time()-t0:.1f}s")
print(f"Picks: {len(result['picks'].get('A', []))}")
