
import os, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'

import akshare as ak

# Check available akshare functions for HK and US
print('=== akshare HK functions ===')
hk_funcs = [f for f in dir(ak) if 'hk' in f.lower() and 'hist' in f.lower()]
print('HK hist funcs:', hk_funcs[:20])

print()
print('=== akshare US functions ===')
us_funcs = [f for f in dir(ak) if 'us' in f.lower() and 'hist' in f.lower()]
print('US hist funcs:', us_funcs[:20])

# Try akshare HK with different parameter formats
print()
print('=== akshare HK hist variants ===')
for func_name in ['stock_hk_hist', 'stock_hk_zh_hist', 'stock_hk_daily']:
    try:
        fn = getattr(ak, func_name, None)
        if fn is None:
            print(func_name, ': not found')
            continue
        t0 = time.time()
        df = fn(symbol='00700', adjust='qfq')
        print(func_name, ':', len(df), 'rows,', round(time.time()-t0,2), 's')
    except Exception as e:
        print(func_name, ': ERROR', str(e)[:100])

print()
print('=== akshare US hist variants ===')
for func_name in ['stock_us_hist', 'stock_us_daily']:
    try:
        fn = getattr(ak, func_name, None)
        if fn is None:
            print(func_name, ': not found')
            continue
        t0 = time.time()
        df = fn(symbol='AAPL', adjust='qfq')
        print(func_name, ':', len(df), 'rows,', round(time.time()-t0,2), 's')
    except Exception as e:
        print(func_name, ': ERROR', str(e)[:100])

# Try with explicit proxy bypass
print()
print('=== akshare with explicit bypass ===')
import urllib.request
old_open = urllib.request.urlopen
def no_proxy_open(url, *args, **kwargs):
    if isinstance(url, str):
        pass
    return old_open(url, *args, **kwargs)
urllib.request.urlopen = no_proxy_open

for k in list(os.environ.keys()):
    if 'proxy' in k.lower() or 'PROXY' in k:
        os.environ.pop(k, None)
os.environ['all_proxy'] = ''
os.environ['ALL_PROXY'] = ''
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'

import importlib
importlib.reload(ak)

try:
    t0 = time.time()
    df = ak.stock_hk_hist(symbol='00700', adjust='qfq')
    print('HK hist (no proxy):', len(df), 'rows,', round(time.time()-t0,2), 's')
except Exception as e:
    print('HK hist error:', str(e)[:150])

try:
    t0 = time.time()
    df = ak.stock_us_hist(symbol='AAPL', adjust='qfq')
    print('US hist (no proxy):', len(df), 'rows,', round(time.time()-t0,2), 's')
except Exception as e:
    print('US hist error:', str(e)[:150])
