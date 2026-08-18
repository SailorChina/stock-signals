
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

print('Test 1: Sina kline')
url = 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=5'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': 'http://finance.sina.com.cn/'})
t = time.time()
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode())
    print(f'  OK: {len(data)} rows in {time.time()-t:.1f}s')
except Exception as e:
    print(f'  ERR: {str(e)[:150]} in {time.time()-t:.1f}s')

print('Test 2: akshare hist')
try:
    import akshare as ak
    t = time.time()
    df = ak.stock_zh_a_hist(symbol='600519', period='daily', adjust='qfq', timeout=10)
    print(f'  OK: {len(df)} rows in {time.time()-t:.1f}s')
except Exception as e:
    print(f'  ERR: {str(e)[:150]}')
