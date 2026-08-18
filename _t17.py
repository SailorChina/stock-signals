
import os, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'

import akshare as ak

# Test A daily (should use different endpoint than hist)
print('=== akshare A daily ===')
for i in range(3):
    try:
        t0 = time.time()
        df = ak.stock_zh_a_daily(symbol='sh600519', adjust='qfq')
        print('  attempt', i+1, ':', len(df), 'rows,', round(time.time()-t0,2), 's')
    except Exception as e:
        print('  attempt', i+1, ': ERROR', str(e)[:80])

print()
print('=== akshare HK daily (retry) ===')
for i in range(3):
    try:
        t0 = time.time()
        df = ak.stock_hk_daily(symbol='00700', adjust='qfq')
        print('  attempt', i+1, ':', len(df), 'rows,', round(time.time()-t0,2), 's')
    except Exception as e:
        print('  attempt', i+1, ': ERROR', str(e)[:80])

print()
print('=== akshare US daily (retry) ===')
for i in range(3):
    try:
        t0 = time.time()
        df = ak.stock_us_daily(symbol='AAPL', adjust='qfq')
        print('  attempt', i+1, ':', len(df), 'rows,', round(time.time()-t0,2), 's')
    except Exception as e:
        print('  attempt', i+1, ': ERROR', str(e)[:80])
