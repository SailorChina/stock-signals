
import sys, os, time, logging
sys.path.insert(0, 'D:/Backup/Documents/ChatGPT/AI/stock-signals')
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
logging.basicConfig(level=logging.WARNING)

from stock_signals.indicators import fetch_kline
from stock_signals.scoring import compute_rating
from stock_signals.hot_fetcher import fetch_hot_stocks

def scan_one(code):
    df = fetch_kline(code)
    if len(df) < 30: return code, 0, None
    ind = compute_indicators(df, code)
    rat = compute_rating(ind)
    return code, len(df), rat

print('=== Sequential scan 30 A-share (with cache) ===')
a_hot = fetch_hot_stocks('A', 30)
print(f'Hot: {len(a_hot)} stocks')
t0 = time.time()
ok = 0
for i, code in enumerate(a_hot):
    try:
        c, rows, rat = scan_one(code)
        if rows > 0: ok += 1
        if (i+1) % 10 == 0:
            print(f'  [{i+1}/{len(a_hot)}] ok={ok} time={time.time()-t0:.1f}s')
    except Exception as e:
        pass
elapsed = time.time() - t0
print(f'  Done: {ok}/{len(a_hot)} in {elapsed:.1f}s, rate={ok/elapsed:.1f}/s')

print()
print('=== Sequential scan 10 HK (with cache) ===')
hk_hot = fetch_hot_stocks('HK', 10)
t0 = time.time()
ok = 0
for i, code in enumerate(hk_hot):
    try:
        c, rows, rat = scan_one(code)
        if rows > 0: ok += 1
    except: pass
elapsed = time.time() - t0
print(f'  Done: {ok}/{len(hk_hot)} in {elapsed:.1f}s, rate={ok/elapsed:.1f}/s')

print()
print('=== Sequential scan 10 US (with cache) ===')
us_hot = fetch_hot_stocks('US', 10)
t0 = time.time()
ok = 0
for i, code in enumerate(us_hot):
    try:
        c, rows, rat = scan_one(code)
        if rows > 0: ok += 1
    except: pass
elapsed = time.time() - t0
print(f'  Done: {ok}/{len(us_hot)} in {elapsed:.1f}s, rate={ok/elapsed:.1f}/s')

print()
print('=== Second run (all cached) ===')
t0 = time.time()
ok = 0
for code in a_hot + hk_hot + us_hot:
    try:
        c, rows, rat = scan_one(code)
        if rows > 0: ok += 1
    except: pass
elapsed = time.time() - t0
print(f'  Done: {ok}/{len(a_hot)+len(hk_hot)+len(us_hot)} in {elapsed:.1f}s, rate={ok/elapsed:.1f}/s')
