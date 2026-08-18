
import sys; sys.path.insert(0, '.')
from stock_signals.screener import scan_parallel, ScanConfig
config = ScanConfig()
config.max_per_market = 1
result = scan_parallel(['A'], config=config)
for p in result['picks'].get('A', []):
    print(f"{p.code}: score={p.score} rating={p.rating}")
