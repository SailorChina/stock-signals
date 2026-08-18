
import os
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k)
import sys; sys.path.insert(0, '.')
import akshare as ak

print('hot_follow_xq:', end=' ')
try: print(len(ak.stock_hot_follow_xq()), 'rows')
except Exception as e: print(f'ERR {str(e)[:80]}')

print('stock_zh_a_hist:', end=' ')
try:
    df = ak.stock_zh_a_hist(symbol='600519', period='daily', adjust='qfq', timeout=10)
    print(f'{len(df)} rows')
except Exception as e: print(f'ERR {str(e)[:80]}')

print('stock_hk_hist:', end=' ')
try:
    df = ak.stock_hk_hist(symbol='00700', period='daily', adjust='qfq')
    print(f'{len(df)} rows')
except Exception as e: print(f'ERR {str(e)[:80]}')

print('stock_us_hist:', end=' ')
try:
    df = ak.stock_us_hist(symbol='105.MSFT', period='daily', adjust='qfq')
    print(f'{len(df)} rows')
except Exception as e: print(f'ERR {str(e)[:80]}')

print()
from stock_signals.indicators import fetch_kline
for n, c in [('A','SH.600519'),('HK','HK.00700'),('US','US.AAPL')]:
    df = fetch_kline(c, '1d', 10)
    print(f'fetch_kline {n}: {len(df)} rows')
