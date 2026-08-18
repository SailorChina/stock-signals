
import sys, os, time
sys.path.insert(0, 'D:/Backup/Documents/ChatGPT/AI/stock-signals')
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
from stock_signals.indicators import fetch_kline
from stock_signals.scoring import compute_rating
from stock_signals.hot_fetcher import fetch_hot_stocks
def scan_one(code):
    df = fetch_kline(code)
    if len(df) < 30: return code, 0, None
    ind = compute_indicators(df, code)
    rat = compute_rating(ind)
    return code, len(df), rat
print('A-share 30 stocks:')
a_hot = fetch_hot_stocks('A', 30)
print(f'  Got {len(a_hot)}')
t0 = time.time()
ok = sum(1 for c in a_hot if scan_one(c)[1] > 0)
print(f'  OK: {ok}/30 in {time.time()-t0:.1f}s')
print('HK 10 stocks:')
hk_hot = fetch_hot_stocks('HK', 10)
t0 = time.time()
ok = sum(1 for c in hk_hot if scan_one(c)[1] > 0)
print(f'  OK: {ok}/{len(hk_hot)} in {time.time()-t0:.1f}s')
print('US 10 stocks:')
us_hot = fetch_hot_stocks('US', 10)
t0 = time.time()
ok = sum(1 for c in us_hot if scan_one(c)[1] > 0)
print(f'  OK: {ok}/{len(us_hot)} in {time.time()-t0:.1f}s')
