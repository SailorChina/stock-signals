
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

# Sina 美股行情
print('Test1: Sina 美股行情')
url = 'http://hq.sinajs.cn/list=usAAPL,usGOOGL,usMSFT,usTSLA,usAMZN,usNVDA'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode('gbk')
    lines = [l for l in data.split('\n') if l.strip() and 'hq_str_us' in l]
    print(f'  OK: {len(lines)} stocks')
    if lines:
        parts = lines[0].split('=')
        if len(parts) > 1:
            vals = parts[1].strip('"').split(',')
            print(f'  Sample: name={vals[0] if vals else "?"} price={vals[1] if len(vals)>1 else "?"}')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

# Sina 美股K线
print('Test2: Sina 美股K线')
for sym in ['usAAPL', 'usGOOGL', 'usMSFT']:
    url2 = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen=20'
    try:
        resp2 = urllib.request.urlopen(urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
        data2 = json.loads(resp2.read().decode())
        print(f'  {sym}: {len(data2) if data2 else 0} rows')
    except Exception as e:
        print(f'  {sym}: ERR {str(e)[:80]}')

# akshare 美股
print('Test3: akshare 美股')
try:
    import akshare as ak
    t = time.time()
    df = ak.stock_us_hist(symbol='105.AAPL', period='daily', adjust='qfq')
    print(f'  AAPL: {len(df)} rows in {time.time()-t:.1f}s')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

# yfinance
print('Test4: yfinance')
try:
    import yfinance as yf
    t = time.time()
    hist = yf.Ticker('AAPL').history(period='5d')
    print(f'  AAPL: {len(hist)} rows in {time.time()-t:.1f}s')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')
