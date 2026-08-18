
import os, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
import akshare as ak

print('=== akshare A hot ===')
t0 = time.time()
try:
    df = ak.stock_hot_follow_xq()
    print('A hot:', len(df), 'rows,', round(time.time()-t0,2), 's')
    print('Cols:', list(df.columns)[:5])
except Exception as e:
    print('Error:', str(e)[:150])

print()
print('=== akshare A kline ===')
t0 = time.time()
try:
    df = ak.stock_zh_a_hist(symbol='600519', adjust='qfq')
    print('A kline:', len(df), 'rows,', round(time.time()-t0,2), 's')
except Exception as e:
    print('Error:', str(e)[:150])

print()
print('=== akshare HK kline ===')
t0 = time.time()
try:
    df = ak.stock_hk_hist(symbol='00700', adjust='qfq')
    print('HK kline:', len(df), 'rows,', round(time.time()-t0,2), 's')
except Exception as e:
    print('Error:', str(e)[:150])

print()
print('=== akshare US kline ===')
t0 = time.time()
try:
    df = ak.stock_us_hist(symbol='AAPL', adjust='qfq')
    print('US kline:', len(df), 'rows,', round(time.time()-t0,2), 's')
except Exception as e:
    print('Error:', str(e)[:150])
