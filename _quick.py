
import time
from stock_signals.screener import scan_parallel, ScanConfig
config = ScanConfig()
config.max_per_market = 2
t0 = time.time()
result = scan_parallel(['A'], config=config)
elapsed = time.time() - t0
print(f"Scan time: {elapsed:.1f}s")
print(f"Picks: {len(result['picks'].get('A', []))}")
