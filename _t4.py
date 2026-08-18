
import os, json, urllib.request, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
def q(url, timeout=15):
    r = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    return urllib.request.urlopen(r, timeout=timeout).read()

print('=== Tencent HK batch ===')
try:
    t0 = time.time()
    codes = 'hk00700,hk09988,hk00001,hk02382,hk03690,hk09888,hk02015'
    data = q('https://qt.gtimg.cn/q=' + codes).decode('gbk')
    lines = [l for l in data.strip().split(chr(10)) if l.strip() and 'none_match' not in l]
    print('HK batch:', len(lines), 'stocks,', round(time.time()-t0,2), 's')
    for line in lines[:5]:
        parts = line.split('=')
        if len(parts) >= 2:
            vals = parts[-1].strip('"').split('~')
            name = vals[1] if len(vals) > 1 else '?'
            code = vals[2] if len(vals) > 2 else '?'
            price = vals[3] if len(vals) > 3 else '?'
            chg = vals[31] if len(vals) > 31 else '?'
            print(' ', code, name, price, chg+'%')
except Exception as e:
    print('Error:', e)

print()
print('=== Tencent US batch ===')
try:
    t0 = time.time()
    codes = 'us_aapl,us_msft,us_googl,us_tsla,us_amzn,us_nvda,us_meta'
    data = q('https://qt.gtimg.cn/q=' + codes).decode('gbk')
    lines = [l for l in data.strip().split(chr(10)) if l.strip() and 'none_match' not in l]
    print('US batch:', len(lines), 'stocks,', round(time.time()-t0,2), 's')
    for line in lines[:5]:
        parts = line.split('=')
        if len(parts) >= 2:
            vals = parts[-1].strip('"').split('~')
            name = vals[1] if len(vals) > 1 else '?'
            sym = vals[2] if len(vals) > 2 else '?'
            price = vals[3] if len(vals) > 3 else '?'
            chg = vals[31] if len(vals) > 31 else '?'
            print(' ', sym, name, price, chg+'%')
except Exception as e:
    print('Error:', e)

print()
print('=== Sina HK K-line ===')
for sym in ['hk00700', 'HK00700']:
    try:
        t0 = time.time()
        url = 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=' + sym + '&scale=240&ma=no&datalen=100'
        data = q(url)
        d = json.loads(data.decode())
        print(sym, ':', len(d) if isinstance(d, list) else 'error', round(time.time()-t0,2), 's')
    except Exception as e:
        print(sym, ': ERROR', str(e)[:80])

print()
print('=== Sina US K-line ===')
for sym in ['us_aapl', 'AAPL']:
    try:
        t0 = time.time()
        url = 'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=' + sym + '&scale=240&ma=no&datalen=100'
        data = q(url)
        d = json.loads(data.decode())
        print(sym, ':', len(d) if isinstance(d, list) else 'error', round(time.time()-t0,2), 's')
    except Exception as e:
        print(sym, ': ERROR', str(e)[:80])

print()
print('=== Sina HK stock list pages ===')
try:
    for p in range(1, 4):
        t0 = time.time()
        url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=' + str(p) + '&num=100&sort=changepercent&asc=0&node=hs_h'
        data = q(url)
        d = json.loads(data.decode())
        print('  page', p, ':', len(d), 'stocks,', round(time.time()-t0,2), 's')
        if len(d) < 100:
            break
except Exception as e:
    print('Error:', e)

print()
print('=== Sina US stock list pages ===')
try:
    for p in range(1, 4):
        t0 = time.time()
        url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=' + str(p) + '&num=100&sort=changepercent&asc=0&node=us_mid'
        data = q(url)
        d = json.loads(data.decode())
        print('  page', p, ':', len(d), 'stocks,', round(time.time()-t0,2), 's')
        if len(d) < 100:
            break
except Exception as e:
    print('Error:', e)
