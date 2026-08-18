
import os, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'

import akshare as ak

# Test akshare HK hist (the one that worked before)
print('=== akshare HK hist (retry) ===')
for i in range(3):
    try:
        t0 = time.time()
        df = ak.stock_hk_hist(symbol='00700', adjust='qfq')
        print('  attempt', i+1, ':', len(df), 'rows,', round(time.time()-t0,2), 's')
    except Exception as e:
        print('  attempt', i+1, ': ERROR', str(e)[:80])

print()
print('=== akshare US hist (retry) ===')
for i in range(3):
    try:
        t0 = time.time()
        df = ak.stock_us_hist(symbol='AAPL', adjust='qfq')
        print('  attempt', i+1, ':', len(df), 'rows,', round(time.time()-t0,2), 's')
    except Exception as e:
        print('  attempt', i+1, ': ERROR', str(e)[:80])

# Test akshare A hist
print()
print('=== akshare A hist (retry) ===')
for i in range(3):
    try:
        t0 = time.time()
        df = ak.stock_zh_a_hist(symbol='600519', adjust='qfq')
        print('  attempt', i+1, ':', len(df), 'rows,', round(time.time()-t0,2), 's')
    except Exception as e:
        print('  attempt', i+1, ': ERROR', str(e)[:80])

# Test Sina A-share K-line speed (bulk)
print()
print('=== Sina A K-line speed test ===')
import urllib.request, json
def q(url):
    r = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    return urllib.request.urlopen(r, timeout=10).read()

codes = ['sh600519', 'sz000001', 'sh600036', 'sz000002', 'sh601318', 'sh600519', 'sz000001']
t0 = time.time()
for sym in codes:
    url = 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=' + sym + '&scale=240&ma=no&datalen=100'
    data = q(url)
    d = json.loads(data.decode())
    print(sym, ':', len(d), 'rows')
print('Sina A total:', round(time.time()-t0,2), 's for', len(codes), 'stocks')

# Test Sina A hot
print()
print('=== Sina A hot speed test ===')
t0 = time.time()
all_items = []
for p in range(1, 4):
    url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=' + str(p) + '&num=100&sort=changepercent&asc=0&node=hs_a'
    data = q(url)
    items = json.loads(data.decode())
    all_items.extend(items)
    if len(items) < 100:
        break
print('Sina A hot:', len(all_items), 'stocks,', round(time.time()-t0,2), 's')
