import sys, logging, time
logging.basicConfig(level=logging.INFO, format='%(message)s')
sys.path.insert(0, r'D:\Backup\Documents\ChatGPT\AI\stock-signals')
from stock_signals.screener import scan_parallel, ScanConfig
config = ScanConfig(max_per_market=2)
t = time.time()
result = scan_parallel(markets=['A'], config=config)
elapsed = time.time()-t
print(f'Time: {elapsed:.1f}s')
print(f'Picks: {len(result["picks"]["A"])}')
for p in result['picks']['A'][:2]:
    print(f'  {p.code}: {p.rating} score={p.score:.1f}')
