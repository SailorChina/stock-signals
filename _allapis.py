
import os, sys
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k)
sys.path.insert(0, '.')
import urllib.request, json

tests = [
  ('Sina http', 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=5'),
  ('Sina https', 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=5'),
  ('Sina quote', 'http://hq.sinajs.cn/list=sh600519'),
]
for name, url in tests:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read()
        print(f'{name}: OK {len(data)} bytes')
    except Exception as e:
        print(f'{name}: ERR {str(e)[:100]}')

# Test baostock
print('baostock:', end=' ')
try:
    import baostock as bs
    lg = bs.login()
    rs = bs.query_history_kline_plus(start='2025-01-01', end='2025-08-18', code='sz.600519', frequency='d')
    rows = []
    while (rs.error_code == '0') & rs.next(): rows.append(rs.get_row_data())
    print(f'OK {len(rows)} rows')
    bs.logout()
except Exception as e:
    print(f'ERR {str(e)[:100]}')
