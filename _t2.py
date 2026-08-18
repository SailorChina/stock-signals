
import os, json, urllib.request
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
def q(url):
    r = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    return urllib.request.urlopen(r, timeout=15).read()
for code, url in [('AAPL','https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=5d'),('0700.HK','https://query1.finance.yahoo.com/v8/finance/chart/0700.HK?interval=1d&range=5d'),('600519.SS','https://query1.finance.yahoo.com/v8/finance/chart/600519.SS?interval=1d&range=5d')]:
    try:
        d = json.loads(q(url).decode())
        r = d.get('chart',{}).get('result',[{}])[0]
        ts = r.get('timestamp',[])
        close = r.get('indicators',{}).get('quote',[{}])[0].get('close',[])
        last = close[-1] if close and close[-1] else 'N/A'
        print(code, len(ts), 'bars, last_close=' + str(last))
    except Exception as e:
        print(code, 'ERROR', str(e)[:100])
