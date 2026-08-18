
import urllib.request, json
for sym in ['hk00700', '00700', 'usAAPL', 'AAPL']:
    url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen=5'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode())
        print(f'{sym}: {len(data) if data else 0}')
    except Exception as e:
        print(f'{sym}: ERR {str(e)[:100]}')
