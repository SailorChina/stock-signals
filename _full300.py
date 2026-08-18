
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
    if len(df) < 30:
        return code, 0, None
    ind = compute_indicators(df, code)
    rat = compute_rating(ind)
    return code, len(df), rat

print('=== A-share Hot (300) Sequential + Rate Limit ===')
a_hot = fetch_hot_stocks('A', 300)
print(f'Count: {len(a_hot)}')
t0 = time.time()
ok = 0
errors = 0
for i, code in enumerate(a_hot):
    try:
        if i > 0 and i % 10 == 0:
            time.sleep(0.5)  # Rate limit protection
        code2, rows, rat = scan_one(code)
        if rows > 0: ok += 1
        else: errors += 1
        if (i+1) % 50 == 0:
            print(f'  [{i+1}/{len(a_hot)}] ok={ok} err={errors} time={time.time()-t0:.1f}s')
    except Exception as e:
        errors += 1
        if errors <= 5: print(f'  ERR {code}: {e}')
print(f'  Final: {ok}/{len(a_hot)}, errors={errors}, total={time.time()-t0:.1f}s')

print()
print('=== HK Hot Sequential ===')
hk_hot = fetch_hot_stocks('HK', 300)
print(f'Count: {len(hk_hot)}')
t0 = time.time()
ok = 0
errors = 0
for i, code in enumerate(hk_hot):
    try:
        if i > 0 and i % 5 == 0:
            time.sleep(0.3)
        code2, rows, rat = scan_one(code)
        if rows > 0: ok += 1
        else: errors += 1
        if (i+1) % 5 == 0:
            print(f'  [{i+1}/{len(hk_hot)}] ok={ok} err={errors} time={time.time()-t0:.1f}s')
    except Exception as e:
        errors += 1
print(f'  Final: {ok}/{len(hk_hot)}, errors={errors}, total={time.time()-t0:.1f}s')

print()
print('=== US Hot Sequential ===')
us_hot = fetch_hot_stocks('US', 300)
print(f'Count: {len(us_hot)}')
t0 = time.time()
ok = 0
errors = 0
for i, code in enumerate(us_hot):
    try:
        if i > 0 and i % 5 == 0:
            time.sleep(0.3)
        code2, rows, rat = scan_one(code)
        if rows > 0: ok += 1
        else: errors += 1
        if (i+1) % 5 == 0:
            print(f'  [{i+1}/{len(us_hot)}] ok={ok} err={errors} time={time.time()-t0:.1f}s')
    except Exception as e:
        errors += 1
print(f'  Final: {ok}/{len(us_hot)}, errors={errors}, total={time.time()-t0:.1f}s')
print('ALL DONE')
