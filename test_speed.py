import sys, logging, time
logging.basicConfig(level=logging.INFO, format='%(message)s')
sys.path.insert(0, r'D:\Backup\Documents\ChatGPT\AI\stock-signals')
from stock_signals.screener import _analyze_one
from stock_signals.indicators import fetch_kline
# Test K-line fetch only
t = time.time()
df = fetch_kline('SH.600519', '1d', num=100)
print(f'K-line fetch: {time.time()-t:.1f}s, rows={len(df) if df is not None else 0}')
# Test full analysis
t = time.time()
r = _analyze_one('SH.600519', delay=0.3)
print(f'Full analyze: {time.time()-t:.1f}s, result={r is not None}')
