
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

# Sina 美股行情
print('Test1: Sina 美股行情')
url = 'http://hq.sinajs.cn/list=usAAPL,usGOOGL,usMSFT'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode('gbk')
    lines = [l for l in data.split('\n') if l.strip() and 'hq_str_us' in l]
    print(f'  OK: {len(lines)} stocks')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

# Sina 美股K线
print('Test2: Sina 美股K线')
for sym in ['usAAPL', 'usGOOGL']:
    url2 = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen=20'
    try:
        resp2 = urllib.request.urlopen(urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10)
        data2 = json.loads(resp2.read().decode())
        print(f'  {sym}: {len(data2) if data2 else 0} rows')
    except Exception as e:
        print(f'  {sym}: ERR {str(e)[:80]}')

# akshare 美股排行
print('Test3: akshare 美股排行')
try:
    import akshare as ak
    t = time.time()
    df = ak.stock_us_rank()
    print(f'  OK: {len(df)} rows in {time.time()-t:.1f}s')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')
