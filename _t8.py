
import os, json, urllib.request, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
def q(url, timeout=15):
    r = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    return urllib.request.urlopen(r, timeout=timeout).read()

# Test Sina HK K-line with different endpoints
print('=== Sina HK K-line variants ===')
for url in [
    'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=hk00700&scale=240&ma=no&datalen=50',
    'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=HK00700&scale=240&ma=no&datalen=50',
    'http://quotes.sina.cn/cn/api/json_v2.php/IPSeeker.query?city=%E9%A6%99%E6%B8%AF',
]:
    try:
        t0 = time.time()
        data = q(url)
        print(url[-40:], ':', data.decode()[:100], round(time.time()-t0,2), 's')
    except Exception as e:
        print(url[-40:], ': ERROR', str(e)[:60])

# Test Sina for HK individual stock quote
print()
print('=== Sina HK quote ===')
for sym in ['hk00700', 'HK00700', '00700']:
    try:
        t0 = time.time()
        url = 'https://hq.sinajs.cn/list=' + sym
        data = q(url).decode('gbk')
        print(sym, ':', repr(data[:150]), round(time.time()-t0,2), 's')
    except Exception as e:
        print(sym, ': ERROR', str(e)[:60])

# Test Sina for US individual stock quote
print()
print('=== Sina US quote ===')
for sym in ['us_aapl', 'AAPL', 'us.AAPL', 'AAPL']:
    try:
        t0 = time.time()
        url = 'https://hq.sinajs.cn/list=' + sym
        data = q(url).decode('utf-8', errors='replace')
        print(sym, ':', repr(data[:150]), round(time.time()-t0,2), 's')
    except Exception as e:
        print(sym, ': ERROR', str(e)[:60])

# Try Sina US K-line
print()
print('=== Sina US K-line ===')
for sym in ['us_aapl', 'AAPL']:
    try:
        t0 = time.time()
        url = 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=' + sym + '&scale=240&ma=no&datalen=50'
        data = q(url)
        d = json.loads(data.decode())
        print(sym, ':', len(d) if isinstance(d, list) else 'error', round(time.time()-t0,2), 's')
    except Exception as e:
        print(sym, ': ERROR', str(e)[:60])

# Try Futu API alternative - check if there's a lighter weight option
print()
print('=== Check Python packages ===')
try:
    import akshare
    print('akshare:', akshare.__version__)
except:
    print('akshare: not installed')
try:
    import baostock
    print('baostock: installed')
except:
    print('baostock: not installed')
try:
    import tushare
    print('tushare:', tushare.__version__)
except:
    print('tushare: not installed')
try:
    import yfinance
    print('yfinance:', yfinance.__version__)
except:
    print('yfinance: not installed')

# Test baostock if available
print()
print('=== baostock test ===')
try:
    import baostock as bs
    t0 = time.time()
    lg = bs.login()
    print('baostock login:', lg.error_code, lg.error_msg)
    rs = bs.query_history_k_data_plus("sh.600519", "date,open,high,low,close,volume",
        start_date='2025-01-01', end_date='2025-06-01', frequency="d", adjustflag="3")
    print('baostock query:', rs.error_code, rs.error_msg)
    rows = rs.get_rows()
    print('baostock rows:', len(rows) if rows else 0, round(time.time()-t0,2), 's')
    bs.logout()
except Exception as e:
    print('baostock error:', str(e)[:100])
