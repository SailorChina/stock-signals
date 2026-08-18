
import time, sys
sys.path.insert(0, '.')
from stock_signals.indicators import fetch_kline
from stock_signals.screener import scan_parallel, ScanConfig

print("Test 1: Single kline fetch")
t = time.time()
df = fetch_kline("SH.600519", "1d", 30)
print(f"  rows={len(df)} time={time.time()-t:.1f}s")

print("Test 2: Scan 3 A-stock")
config = ScanConfig()
config.max_per_market = 1
t = time.time()
result = scan_parallel(["A"], config=config)
elapsed = time.time() - t
print(f"  Scan time: {elapsed:.1f}s")
print(f"  Picks: {len(result['picks'].get('A', []))}")
if result['picks'].get('A'):
    for p in result['picks']['A'][:2]:
        print(f"    {p.code}: score={p.score} rating={p.rating}")
print("DONE")
