
import os, sys
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k)
sys.path.insert(0, '.')

# Test 1: akshare hist
print('Test1: akshare hist')
try:
    import akshare as ak
    df = ak.stock_zh_a_hist(symbol='600519', period='daily', adjust='qfq', timeout=10)
    print(f'  OK: {len(df)} rows')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

# Test 2: Sina with different headers
print('Test2: Sina kline')
import urllib.request, json
url = 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=5'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': 'http://finance.sina.com.cn/'})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode())
    print(f'  OK: {len(data)} rows')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

# Test 3: baostock
print('Test3: baostock')
try:
    import baostock as bs
    lg = bs.login()
    rs = bs.query_history_kline_plus('sz.600519', 'date,open,high,low,close,volume', start_date='2025-01-01', end_date='2025-08-18', frequency='d')
    rows = []
    while (rs.error_code == '0') & rs.next():
        rows.append(rs.get_row_data())
    print(f'  OK: {len(rows)} rows')
    bs.logout()
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')
