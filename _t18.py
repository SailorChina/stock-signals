
import os, time, json, urllib.request
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'

def q(url):
    r = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    return urllib.request.urlopen(r, timeout=15).read()

# Test Tencent HK batch with known codes
print('=== Tencent HK batch 20 ===')
hk_codes = ['hk00700', 'hk09988', 'hk00001', 'hk02382', 'hk03690', 'hk09888', 'hk02015', 'hk02359', 'hk00686', 'hk00291',
            'hk00322', 'hk01071', 'hk09922', 'hk09866', 'hk09961', 'hk00012', 'hk00003', 'hk00006', 'hk00009', 'hk00883']
t0 = time.time()
codes_str = ','.join(hk_codes)
data = q('https://qt.gtimg.cn/q=' + codes_str).decode('gbk')
lines = [l for l in data.strip().split(chr(10)) if l.strip() and 'none_match' not in l]
print('HK 20 codes:', len(lines), 'stocks,', round(time.time()-t0,2), 's')
for line in lines[:5]:
    vals = line.split('=')[-1].strip('"').split('~')
    if len(vals) > 3:
        print('  ', vals[2], vals[1], vals[3])

# Test Sina HK stock list
print()
print('=== Sina HK stock list ===')
all_hk = []
for p in range(1, 6):
    try:
        url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=' + str(p) + '&num=100&sort=symbol&asc=1&node=hs_h'
        data = q(url)
        items = json.loads(data.decode())
        all_hk.extend(items)
        print('  page', p, ':', len(items), 'stocks')
        if len(items) < 100:
            break
    except Exception as e:
        print('  page', p, ': ERROR', str(e)[:60])
        break
print('Total HK:', len(all_hk))

# Test Sina US stock list
print()
print('=== Sina US stock list ===')
all_us = []
for p in range(1, 6):
    try:
        url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=' + str(p) + '&num=100&sort=symbol&asc=1&node=us_mid'
        data = q(url)
        items = json.loads(data.decode())
        all_us.extend(items)
        print('  page', p, ':', len(items), 'stocks')
        if len(items) < 100:
            break
    except Exception as e:
        print('  page', p, ': ERROR', str(e)[:60])
        break
print('Total US:', len(all_us))

# Test Tencent US with specific codes
print()
print('=== Tencent US specific codes ===')
us_syms = ['aapl', 'msft', 'googl', 'tsla', 'amzn', 'nvda', 'meta', 'nflx', 'amd', 'intc']
t0 = time.time()
codes_str = ','.join(['us_' + c for c in us_syms])
data = q('https://qt.gtimg.cn/q=' + codes_str).decode('gbk')
lines = [l for l in data.strip().split(chr(10)) if l.strip() and 'none_match' not in l]
print('US', len(us_syms), 'codes:', len(lines), 'stocks,', round(time.time()-t0,2), 's')
