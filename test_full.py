import sys, logging, time
logging.basicConfig(level=logging.INFO, format='%(message)s')
sys.path.insert(0, r'D:\Backup\Documents\ChatGPT\AI\stock-signals')
from stock_signals.screener import scan_parallel, ScanConfig
config = ScanConfig(max_per_market=2, min_score=70)
t = time.time()
result = scan_parallel(markets=['A', 'HK', 'US'], config=config)
elapsed = time.time()-t
print(f'Time: {elapsed:.1f}s')
for m in ['A', 'HK', 'US']:
    print(f'{m}: {len(result["picks"][m])} picks, {len(result["watchlist"][m])} watch')
    for p in result['picks'][m][:2]:
        print(f'  {p.code}: {p.rating} score={p.score:.1f}')
