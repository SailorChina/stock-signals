
import os, sys
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k)
sys.path.insert(0, '.')
import akshare as ak
print('HK:', end=' ')
try:
    print(len(ak.stock_hk_hist(symbol='00700', period='daily', adjust='qfq')), 'rows')
except Exception as e: print(f'ERR {str(e)[:100]}')
print('US:', end=' ')
try:
    print(len(ak.stock_us_hist(symbol='105.MSFT', period='daily', adjust='qfq')), 'rows')
except Exception as e: print(f'ERR {str(e)[:100]}')
