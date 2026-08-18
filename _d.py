
import sys; sys.path.insert(0, '.')
import urllib.request, json
code = 'SH.600519'
clean = code.split('.')[-1]
sina = f'sh{clean.lower()}'
url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina}&scale=240&ma=no&datalen=10'
print(f'url={url}')
try:
    resp = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10)
    data = json.loads(resp.read().decode())
    print(f'direct: {len(data)} rows')
except Exception as e:
    print(f'direct ERR: {e}')
from stock_signals.indicators import fetch_kline
try:
    df = fetch_kline(code, '1d', 10)
    print(f'fetch_kline: {len(df)} rows')
except Exception as e:
    print(f'fetch_kline ERR: {e}')
    import traceback; traceback.print_exc()
