
import os
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
import akshare as ak
for name, fn, args in [('HK', lambda: ak.stock_hk_daily(symbol='00700', adjust='qfq'), None),
                        ('US', lambda: ak.stock_us_daily(symbol='AAPL', adjust='qfq'), None),
                        ('A', lambda: ak.stock_zh_a_daily(symbol='sh600519', adjust='qfq'), None)]:
    r = fn()
    print(name, 'type:', type(r).__name__)
    if isinstance(r, tuple):
        print('  tuple len:', len(r), 'elt0:', type(r[0]).__name__, 'elt1:', type(r[1]).__name__)
        if hasattr(r[1], 'empty'): print('  df empty:', r[1].empty, 'len:', len(r[1]))
    elif hasattr(r, 'empty'):
        print('  df empty:', r.empty, 'len:', len(r))
