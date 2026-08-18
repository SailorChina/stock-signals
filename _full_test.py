
import sys, os, time
sys.path.insert(0, 'D:/Backup/Documents/ChatGPT/AI/stock-signals')
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'

print('=== Import Check ===')
try:
    from stock_signals.indicators import fetch_kline, compute_indicators, signal_summary
    print('indicators: OK')
except Exception as e:
    print(f'indicators: ERROR {e}')

try:
    from stock_signals.hot_fetcher import fetch_hot_stocks
    print('hot_fetcher: OK')
except Exception as e:
    print(f'hot_fetcher: ERROR {e}')

try:
    from stock_signals.scoring import compute_rating, RATINGS
    print('scoring: OK')
except Exception as e:
    print(f'scoring: ERROR {e}')

try:
    from stock_signals.screener import STOCK_POOLS
    print(f'screener: OK, pools: SH={len(STOCK_POOLS.get("SH",[]))}, SZ={len(STOCK_POOLS.get("SZ",[]))}, HK={len(STOCK_POOLS.get("HK",[]))}, US={len(STOCK_POOLS.get("US",[]))}')
except Exception as e:
    print(f'screener: ERROR {e}')

print()
print('=== K-line Speed Test ===')
# Test A-share K-line
for code in ['SH.600519', 'SZ.000001', 'SH.600036']:
    t0 = time.time()
    df = fetch_kline(code)
    print(f'  {code}: {len(df)} rows, {time.time()-t0:.2f}s')

# Test HK K-line
for code in ['HK.00700', 'HK.09988']:
    t0 = time.time()
    df = fetch_kline(code)
    print(f'  {code}: {len(df)} rows, {time.time()-t0:.2f}s')

# Test US K-line
for code in ['US.AAPL', 'US.MSFT']:
    t0 = time.time()
    df = fetch_kline(code)
    print(f'  {code}: {len(df)} rows, {time.time()-t0:.2f}s')

print()
print('=== Hot Stocks Test ===')
t0 = time.time()
a_hot = fetch_hot_stocks('A', 30)
print(f'  A hot: {len(a_hot)} stocks, {time.time()-t0:.2f}s')

t0 = time.time()
hk_hot = fetch_hot_stocks('HK', 30)
print(f'  HK hot: {len(hk_hot)} stocks, {time.time()-t0:.2f}s')

t0 = time.time()
us_hot = fetch_hot_stocks('US', 30)
print(f'  US hot: {len(us_hot)} stocks, {time.time()-t0:.2f}s')

print()
print('=== Full Scan (3 stocks per market) ===')
t_total = time.time()
from concurrent.futures import ThreadPoolExecutor, as_completed

all_codes = []
for mkt, pool in [('A', STOCK_POOLS.get('SH',[])[:3] + STOCK_POOLS.get('SZ',[])[:3]),
                   ('HK', STOCK_POOLS.get('HK',[])[:3]),
                   ('US', STOCK_POOLS.get('US',[])[:3])]:
    for code in pool:
        all_codes.append((mkt, code))

results = []
with ThreadPoolExecutor(max_workers=6) as exe:
    futures = {exe.submit(lambda mc: (mc[0], fetch_kline(mc[1])), c): c for c in all_codes}
    for f in as_completed(futures):
        mkt, code = futures[f]
        try:
            df = f.result()
            ind = compute_indicators(df, code)
            sig = signal_summary(ind)
            results.append((code, len(df), sig['signal_count'], sig['signals']))
        except Exception as e:
            results.append((code, 0, 0, [str(e)]))

print(f'  Scanned {len(results)} stocks, total: {time.time()-t_total:.1f}s')
for code, rows, nsignals, sigs in sorted(results, key=lambda x: -x[2]):
    print(f'    {code}: {rows} rows, {nsignals} signals: {sigs[:3]}')
