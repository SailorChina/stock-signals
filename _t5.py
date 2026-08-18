
import os, json, urllib.request, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
def q(url, timeout=15):
    r = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    return urllib.request.urlopen(r, timeout=timeout).read()

print('=== Tencent US formats ===')
for prefix in ['us_', 'US_', '']:
    try:
        t0 = time.time()
        url = 'https://qt.gtimg.cn/q=' + prefix + 'aapl'
        data = q(url).decode('gbk')
        lines = [l for l in data.strip().split(chr(10)) if l.strip() and 'none_match' not in l]
        print(prefix + 'aapl:', len(lines), 'stocks,', round(time.time()-t0,2), 's')
    except Exception as e:
        print(prefix + 'aapl: ERROR', str(e)[:60])

print()
print('=== EastMoney HK K-line ===')
try:
    t0 = time.time()
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=116.00700&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500000&lmt=50'
    data = q(url)
    d = json.loads(data.decode())
    kl = d.get('data',{}).get('klines',[])
    print('HK 00700:', len(kl), 'rows,', round(time.time()-t0,2), 's')
    if kl: print('  First:', kl[0])
except Exception as e:
    print('Error:', str(e)[:100])

print()
print('=== EastMoney US K-line ===')
for secid in ['105.AAPL', '105.aapl']:
    try:
        t0 = time.time()
        url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=' + secid + '&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500000&lmt=50'
        data = q(url)
        d = json.loads(data.decode())
        kl = d.get('data',{}).get('klines',[])
        print(secid, ':', len(kl), 'rows,', round(time.time()-t0,2), 's')
        if kl: print('  First:', kl[0])
        break
    except Exception as e:
        print(secid, ': ERROR', str(e)[:80])

print()
print('=== Sina A K-line ===')
for sym in ['sh600519', 'sz000001']:
    try:
        t0 = time.time()
        url = 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=' + sym + '&scale=240&ma=no&datalen=100'
        data = q(url)
        d = json.loads(data.decode())
        print(sym, ':', len(d), 'rows,', round(time.time()-t0,2), 's')
    except Exception as e:
        print(sym, ': ERROR', str(e)[:80])

print()
print('=== Sina A hot ===')
try:
    t0 = time.time()
    all_items = []
    for p in range(1, 4):
        url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=' + str(p) + '&num=100&sort=changepercent&asc=0&node=hs_a'
        data = q(url)
        items = json.loads(data.decode())
        all_items.extend(items)
        print('  page', p, ':', len(items))
        if len(items) < 100: break
    print('Total:', len(all_items), round(time.time()-t0,2), 's')
except Exception as e:
    print('Error:', e)
