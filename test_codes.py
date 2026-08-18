import sys, time
sys.path.insert(0, r'D:\Backup\Documents\ChatGPT\AI\stock-signals')
from stock_signals.screener import _get_market_codes
for m in ['A', 'HK', 'US']:
    t = time.time()
    c = _get_market_codes(m)
    print(f'{m}: {len(c)} codes in {time.time()-t:.1f}s, first={c[:3]}')
