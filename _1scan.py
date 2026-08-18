
import time, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
from stock_signals.screener import scan_parallel, ScanConfig
config = ScanConfig()
config.max_per_market = 1
t0 = time.time()
result = scan_parallel(['A'], config=config)
elapsed = time.time() - t0
print(f'Time: {elapsed:.1f}s for A-market (30 stocks, max_per_market=1)')
print(f'Picks: {len(result["picks"].get("A", []))}')
for p in result['picks'].get('A', [])[:3]:
    print(f'  {p.code}: score={p.score} rating={p.rating}')
