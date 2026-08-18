
import time, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
from stock_signals.indicators import fetch_kline
from stock_signals.hot_fetcher import fetch_a_hot_stocks

codes = fetch_a_hot_stocks(5)
print(f'Testing {len(codes)} codes')
for c in codes:
    t = time.time()
    df = fetch_kline(c, '1d', 100)
    print(f'  {c}: {len(df)} rows, {time.time()-t:.1f}s')
print(f'Total: {time.time()-t:.1f}s')
