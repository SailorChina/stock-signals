
import sys, os, time, logging
sys.path.insert(0, 'D:/Backup/Documents/ChatGPT/AI/stock-signals')
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
logging.basicConfig(level=logging.WARNING)

from stock_signals.indicators import fetch_kline
from stock_signals.scoring import compute_rating
from stock_signals.hot_fetcher import fetch_hot_stocks

print('=== Test individual codes ===')
for code in ['SH.600519', 'SH.688826', 'SZ.000001', 'HK.00700', 'US.AAPL']:
    t0 = time.time()
    df = fetch_kline(code)
    dt = time.time() - t0
    print(f'  {code}: {len(df)} rows, {dt:.2f}s')

print()
print('=== A-share hot scan (30 stocks) ===')
a_hot = fetch_hot_stocks('A', 30)
print(f'Count: {len(a_hot)}')
t0 = time.time()
ok = 0
for i, code in enumerate(a_hot):
    df = fetch_kline(code)
    if len(df) >= 30:
        ind = compute_rating(compute_indicators(df, code))
        ok += 1
    if (i+1) % 10 == 0:
        print(f'  [{i+1}/{len(a_hot)}] ok={ok} time={time.time()-t0:.1f}s')
    time.sleep(0.3)
print(f'  Done: {ok}/{len(a_hot)}, time={time.time()-t0:.1f}s')
