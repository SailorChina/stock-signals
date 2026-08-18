
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

print('='*50)
print('三市场扫描速度测试 (每只延迟0.2s)')
print('='*50)

print()
print('[A股市场]')
a_hot = fetch_hot_stocks('A', 300)
print(f'热门股: {len(a_hot)} 只')
t0 = time.time()
a_ok = 0
for i, code in enumerate(a_hot):
    time.sleep(0.2)
    c, rows, rat = scan_one(code)
    if rows > 0: a_ok += 1
    if (i+1) % 50 == 0:
        print(f'  [{i+1}/300] 成功:{a_ok} 时间:{time.time()-t0:.1f}s')
a_total = time.time() - t0
print(f'结果: {a_ok}/300 成功, {a_total:.1f}s')

print()
print('[港股市场]')
hk_hot = fetch_hot_stocks('HK', 300)
print(f'热门股: {len(hk_hot)} 只')
t0 = time.time()
hk_ok = 0
for i, code in enumerate(hk_hot):
    time.sleep(0.2)
    c, rows, rat = scan_one(code)
    if rows > 0: hk_ok += 1
    if (i+1) % 50 == 0:
        print(f'  [{i+1}/{len(hk_hot)}] 成功:{hk_ok} 时间:{time.time()-t0:.1f}s')
hk_total = time.time() - t0
print(f'结果: {hk_ok}/{len(hk_hot)} 成功, {hk_total:.1f}s')

print()
print('[美股市场]')
us_hot = fetch_hot_stocks('US', 300)
print(f'热门股: {len(us_hot)} 只')
t0 = time.time()
us_ok = 0
for i, code in enumerate(us_hot):
    time.sleep(0.2)
    c, rows, rat = scan_one(code)
    if rows > 0: us_ok += 1
    if (i+1) % 50 == 0:
        print(f'  [{i+1}/{len(us_hot)}] 成功:{us_ok} 时间:{time.time()-t0:.1f}s')
us_total = time.time() - t0
print(f'结果: {us_ok}/{len(us_hot)} 成功, {us_total:.1f}s')

print()
print('='*50)
print('汇总')
print('='*50)
print(f'A股: {a_ok}/300, {a_total:.1f}s')
print(f'港股: {hk_ok}/{len(hk_hot)}, {hk_total:.1f}s')
print(f'美股: {us_ok}/{len(us_hot)}, {us_total:.1f}s')
print(f'总计: {a_ok+hk_ok+us_ok}只成功, {a_total+hk_total+us_total:.1f}s')
