
import os
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k)
import sys; sys.path.insert(0, '.')
import akshare as ak
print('HK:', end=' ')
try:
    df = ak.stock_hk_hist(symbol='00700', period='daily', adjust='qfq', timeout=10)
    print(f'{len(df)} rows')
except Exception as e: print(f'ERR {str(e)[:100]}')
print('US:', end=' ')
try:
    df = ak.stock_us_hist(symbol='105.MSFT', period='daily', adjust='qfq', timeout=10)
    print(f'{len(df)} rows')
except Exception as e: print(f'ERR {str(e)[:100]}')
