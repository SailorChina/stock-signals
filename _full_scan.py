
import sys, os, time
sys.path.insert(0, 'D:/Backup/Documents/ChatGPT/AI/stock-signals')
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'

from stock_signals.indicators import fetch_kline, compute_indicators, signal_summary
from stock_signals.scoring import compute_rating, RATINGS
from stock_signals.screener import STOCK_POOLS
from stock_signals.hot_fetcher import fetch_hot_stocks
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('stock-signals')

print('=== Full 3-Market Scan Test ===')
print()

# Test K-line fetching
print('--- K-line Speed ---')
for code in ['SH.600519', 'SZ.000001', 'HK.00700', 'HK.09988', 'US.AAPL', 'US.MSFT']:
    t0 = time.time()
    df = fetch_kline(code)
    dt = time.time() - t0
    status = 'OK' if len(df) > 0 else 'EMPTY'
    print(f'  {code}: {len(df)} rows, {dt:.2f}s [{status}]')

print()
print('--- Indicator Computation ---')
for code in ['SH.600519', 'HK.00700', 'US.AAPL']:
    t0 = time.time()
    df = fetch_kline(code)
    if len(df) > 0:
        ind = compute_indicators(df, code)
        sig = signal_summary(ind)
        rat = compute_rating(ind)
        dt = time.time() - t0
        print(f'  {code}: {len(df)} rows, {dt:.2f}s, signals={sig["signal_count"]}, rating={rat}')
    else:
        print(f'  {code}: NO DATA')

print()
print('--- Hot Stocks ---')
for mkt in ['A', 'HK', 'US']:
    t0 = time.time()
    stocks = fetch_hot_stocks(mkt, 300)
    dt = time.time() - t0
    print(f'  {mkt}: {len(stocks)} stocks, {dt:.2f}s')
    if stocks:
        print(f'    sample: {stocks[:5]}')

print()
print('--- Pool Scan (5 stocks per market) ---')
t_total = time.time()
all_codes = []
for mkt, keys in [('A', ['SH','SZ']), ('HK', ['HK']), ('US', ['US'])]:
    for k in keys:
        for code in STOCK_POOLS.get(k, [])[:5]:
            all_codes.append((mkt, code))

print(f'  Total codes to scan: {len(all_codes)}')

from concurrent.futures import ThreadPoolExecutor, as_completed
results = []
with ThreadPoolExecutor(max_workers=6) as exe:
    futures = {}
    for mkt, code in all_codes:
        f = exe.submit(lambda mc: (_scan_stock(mc[0], mc[1])), (mkt, code))
        futures[f] = (mkt, code)
    for f in as_completed(futures):
        mkt, code = futures[f]
        try:
            result = f.result()
            results.append((mkt, code, result))
        except Exception as e:
            results.append((mkt, code, {'error': str(e)}))

print(f'  Completed {len(results)} stocks in {time.time()-t_total:.1f}s')
for mkt, code, result in sorted(results):
    if 'error' in result:
        print(f'  [{mkt}] {code}: ERROR {result["error"]}')
    else:
        print(f'  [{mkt}] {code}: rating={result.get("rating","?")}, signals={result.get("signal_count",0)}')

print()
print('=== Done ===')
