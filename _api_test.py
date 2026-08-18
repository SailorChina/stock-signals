
import os, sys, json, urllib.request

for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'

def req(url):
    r = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(r, timeout=10).read()

print('=== Tencent HK ===')
try:
    t = req('https://qt.gtimg.cn/q=hk_all').decode('gbk')
    lines = [l for l in t.strip().split(chr(10)) if l.strip()]
    print(f'  Lines: {len(lines)}')
    if lines:
        print(f'  Sample: {lines[0][:100]}')
except Exception as e:
    print(f'  Error: {e}')

print('=== Tencent US ===')
try:
    t = req('https://qt.gtimg.cn/q=us_all').decode('gbk')
    lines = [l for l in t.strip().split(chr(10)) if l.strip()]
    print(f'  Lines: {len(lines)}')
    if lines:
        print(f'  Sample: {lines[0][:100]}')
except Exception as e:
    print(f'  Error: {e}')

print('=== Sina A K-line ===')
try:
    d = json.loads(req('http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=100').decode())
    print(f'  Rows: {len(d)}')
except Exception as e:
    print(f'  Error: {e}')

print('=== EastMoney A K-line ===')
try:
    d = json.loads(req('https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=1.600519&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500000&lmt=50').decode())
    kl = d.get('data',{}).get('klines',[])
    print(f'  Rows: {len(kl)}, First: {kl[0] if kl else None}')
except Exception as e:
    print(f'  Error: {e}')

print('=== EastMoney HK K-line ===')
try:
    d = json.loads(req('https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=116.00700&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500000&lmt=50').decode())
    kl = d.get('data',{}).get('klines',[])
    print(f'  Rows: {len(kl)}, First: {kl[0] if kl else None}')
except Exception as e:
    print(f'  Error: {e}')

print('=== EastMoney US K-line ===')
try:
    d = json.loads(req('https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AAPL&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500000&lmt=50').decode())
    kl = d.get('data',{}).get('klines',[])
    print(f'  Rows: {len(kl)}, First: {kl[0] if kl else None}')
except Exception as e:
    print(f'  Error: {e}')

print('=== Sina HK Node ===')
try:
    d = json.loads(req('http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=100&sort=symbol&asc=1&node=hs_h').decode())
    print(f'  Stocks: {len(d)}, First: {d[0] if d else None}')
except Exception as e:
    print(f'  Error: {e}')

print('=== Sina US Node ===')
try:
    d = json.loads(req('http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=100&sort=symbol&asc=1&node=us_mid').decode())
    print(f'  Stocks: {len(d)}, First: {d[0] if d else None}')
except Exception as e:
    print(f'  Error: {e}')
