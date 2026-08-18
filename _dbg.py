
import sys; sys.path.insert(0, '.')
import urllib.request, json

code = 'SH.600519'
clean = code.split('.')[-1]
sina_code = f'sh{clean.lower()}'
print(f'code={code} clean={clean} sina={sina_code}')

url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale=240&ma=no&datalen=10'
print(f'url={url}')

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode())
    print(f'data: {type(data)} len={len(data) if data else 0}')
    if data: print(f'  first={data[0]}')
except Exception as e:
    print(f'ERR: {e}')

from stock_signals.indicators import fetch_kline
df = fetch_kline(code, '1d', 10)
print(f'fetch_kline: {len(df)} rows')
