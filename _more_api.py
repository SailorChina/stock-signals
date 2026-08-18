
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

print('Test1: Sina 港股代码列表')
url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=500&sort=symbol&asc=1&node=hk_h'
try:
    resp = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
    data = json.loads(resp.read().decode())
    print(f'  OK: {len(data) if data else 0} stocks')
    if data:
        print(f'  Sample: {data[0]}')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

print('Test2: Sina 美股代码列表')
url2 = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=500&sort=symbol&asc=1&node=us_a'
try:
    resp2 = urllib.request.urlopen(urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
    data2 = json.loads(resp2.read().decode())
    print(f'  OK: {len(data2) if data2 else 0} stocks')
    if data2:
        print(f'  Sample: {data2[0]}')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

print('Test3: akshare 港股函数列表')
try:
    import akshare as ak
    hk_funcs = [f for f in dir(ak) if 'hk' in f.lower()]
    print(f'  HK funcs: {hk_funcs[:20]}')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')
