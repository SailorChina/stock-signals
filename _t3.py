
import os, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
import akshare as ak
tests = [
    ('A-hot', lambda: ak.stock_hot_follow_xq()),
    ('A-kline', lambda: ak.stock_zh_a_hist(symbol='600519', adjust='qfq')),
    ('HK-kline', lambda: ak.stock_hk_hist(symbol='00700', adjust='qfq')),
    ('US-kline', lambda: ak.stock_us_hist(symbol='AAPL', adjust='qfq')),
]
for name, fn in tests:
    t = time.time()
    try:
        df = fn()
        print(name, len(df), 'rows,', round(time.time()-t,2), 's')
    except Exception as e:
        print(name, 'ERROR', str(e)[:100])
