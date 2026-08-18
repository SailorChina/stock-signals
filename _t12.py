
import os, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'

import urllib.request, json

def q(url):
    r = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn/',
    })
    return urllib.request.urlopen(r, timeout=15).read()

# Try AkShare with different proxy settings
print('=== akshare with session ===')
try:
    import akshare as ak
    import requests
    
    # Try with session that has no proxy
    session = requests.Session()
    session.trust_env = False
    session.proxies = {}
    
    # Test A-share K-line
    t0 = time.time()
    df = ak.stock_zh_a_hist(symbol='600519', adjust='qfq', session=session)
    print('A kline with session:', len(df), 'rows,', round(time.time()-t0,2), 's')
except Exception as e:
    print('A kline error:', str(e)[:150])

try:
    import akshare as ak
    import requests
    session = requests.Session()
    session.trust_env = False
    session.proxies = {}
    
    t0 = time.time()
    df = ak.stock_hk_hist(symbol='00700', adjust='qfq', session=session)
    print('HK kline with session:', len(df), 'rows,', round(time.time()-t0,2), 's')
except Exception as e:
    print('HK kline error:', str(e)[:150])

try:
    import akshare as ak
    import requests
    session = requests.Session()
    session.trust_env = False
    session.proxies = {}
    
    t0 = time.time()
    df = ak.stock_us_hist(symbol='AAPL', adjust='qfq', session=session)
    print('US kline with session:', len(df), 'rows,', round(time.time()-t0,2), 's')
except Exception as e:
    print('US kline error:', str(e)[:150])

# Try xueqiu for HK/US
print()
print('=== Xueqiu HK/US ===')
try:
    import akshare as ak
    t0 = time.time()
    df = ak.stock_zh_history(symbol='sh600519')
    print('xueqiu A:', len(df), 'rows,', round(time.time()-t0,2), 's')
except Exception as e:
    print('xueqiu A error:', str(e)[:100])

# Try Sina for HK/US K-line with correct symbol format
print()
print('=== Sina K-line symbol formats ===')
test_cases = [
    ('A-share', 'sh600519', 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=10'),
    ('HK special', 'SH00700', 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=SH00700&scale=240&ma=no&datalen=10'),
    ('US special', 'US_AAPL', 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=US_AAPL&scale=240&ma=no&datalen=10'),
]
for name, sym, url in test_cases:
    try:
        t0 = time.time()
        data = q(url)
        d = json.loads(data.decode())
        print(name, sym, ':', 'null' if d is None else len(d), 'rows,', round(time.time()-t0,2), 's')
    except Exception as e:
        print(name, sym, ': ERROR', str(e)[:60])
