
import os, json, urllib.request, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
def q(url, timeout=15):
    r = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    return urllib.request.urlopen(r, timeout=timeout).read()

# Test EastMoney batch K-line for HK
print('=== EastMoney HK batch K-line ===')
hk_codes = ['116.00700', '116.09988', '116.00001', '116.02382', '116.03690']
t0 = time.time()
for secid in hk_codes:
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=' + secid + '&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500000&lmt=100'
    try:
        data = q(url)
        d = json.loads(data.decode())
        kl = d.get('data',{}).get('klines',[])
        print(secid, ':', len(kl), 'rows')
    except Exception as e:
        print(secid, ': ERROR', str(e)[:60])
print('Total time:', round(time.time()-t0,2), 's for', len(hk_codes), 'stocks')

# Test EastMoney batch K-line for US
print()
print('=== EastMoney US batch K-line ===')
us_codes = ['105.AAPL', '105.MSFT', '105.GOOG', '105.TSLA', '105.AMZN']
t0 = time.time()
for secid in us_codes:
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=' + secid + '&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500000&lmt=100'
    try:
        data = q(url)
        d = json.loads(data.decode())
        kl = d.get('data',{}).get('klines',[])
        print(secid, ':', len(kl), 'rows')
    except Exception as e:
        print(secid, ': ERROR', str(e)[:60])
print('Total time:', round(time.time()-t0,2), 's for', len(us_codes), 'stocks')

# Test EastMoney A-share batch K-line
print()
print('=== EastMoney A-share batch K-line ===')
a_codes = ['1.600519', '1.600036', '0.000001']
t0 = time.time()
for secid in a_codes:
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=' + secid + '&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500000&lmt=100'
    try:
        data = q(url)
        d = json.loads(data.decode())
        kl = d.get('data',{}).get('klines',[])
        print(secid, ':', len(kl), 'rows')
    except Exception as e:
        print(secid, ': ERROR', str(e)[:60])
print('Total time:', round(time.time()-t0,2), 's for', len(a_codes), 'stocks')

# Test Tencent HK realtime for batch of 300
print()
print('=== Tencent HK batch realtime 300 ===')
# First, get HK stock list
try:
    t0 = time.time()
    # Sina HK stock list
    all_hk = []
    for p in range(1, 5):
        url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=' + str(p) + '&num=100&sort=changepercent&asc=0&node=hs_h'
        data = q(url)
        items = json.loads(data.decode())
        all_hk.extend(items)
        print('  HK page', p, ':', len(items))
        if len(items) < 100: break
    print('Total HK stocks from Sina:', len(all_hk), round(time.time()-t0,2), 's')
except Exception as e:
    print('Error:', e)

# Test Tencent HK with specific codes
print()
print('=== Tencent HK specific codes ===')
try:
    t0 = time.time()
    codes = ','.join(['hk' + str(i).zfill(5) for i in [700, 9988, 1, 2382, 3690, 9888, 2015, 2359, 686, 291]])
    url = 'https://qt.gtimg.cn/q=' + codes
    data = q(url).decode('gbk')
    lines = [l for l in data.strip().split(chr(10)) if l.strip() and 'none_match' not in l]
    print('HK batch 10:', len(lines), 'stocks,', round(time.time()-t0,2), 's')
except Exception as e:
    print('Error:', e)
