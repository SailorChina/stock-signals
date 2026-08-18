
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

print('Test1: Sina 美股K线')
for sym, desc in [('usAAPL','苹果'),('usGOOGL','谷歌'),('usMSFT','微软')]:
    url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen=20'
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10)
        data = json.loads(resp.read().decode())
        print(f'  {sym}({desc}): {len(data) if data else 0} rows')
    except Exception as e:
        print(f'  {sym}: ERR {str(e)[:60]}')

print('Test2: akshare 美股历史')
try:
    import akshare as ak
    t = time.time()
    df = ak.stock_us_hist(symbol='105.AAPL', period='daily', adjust='qfq')
    print(f'  AAPL: {len(df)} rows in {time.time()-t:.1f}s')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

print('Test3: yfinance')
try:
    import yfinance as yf
    t = time.time()
    hist = yf.Ticker('AAPL').history(period='1mo')
    print(f'  AAPL: {len(hist)} rows in {time.time()-t:.1f}s')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

print('Test4: akshare 美股排行')
try:
    import akshare as ak
    t = time.time()
    df = ak.stock_us_spot_em()
    print(f'  OK: {len(df)} rows in {time.time()-t:.1f}s')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')
