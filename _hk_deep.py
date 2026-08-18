
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

print('=== 港股 API 深入测试 ===')

# 1. Sina 港股实时行情
print('Test1: Sina 港股行情')
hk_codes = ['hk00700', 'hk00001', 'hk9988', 'hk3690', 'hk01299', 'hk09618', 'hk09961', 'hk02015', 'hk02382', 'hk00941']
symbols_str = ','.join(hk_codes)
url = f'http://hq.sinajs.cn/list={symbols_str}'
try:
    resp = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
    data = resp.read().decode('gbk')
    lines = [l for l in data.split('\n') if l.strip() and 'hq_str_hk' in l]
    print(f'  OK: {len(lines)} stocks')
    for line in lines[:3]:
        parts = line.split('="')
        if len(parts) > 1:
            vals = parts[1].strip('";').split(',')
            print(f'    {vals[0] if vals else "?"}: {vals[3] if len(vals)>3 else "?"}')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

# 2. Sina 港股排行
print('Test2: Sina 港股排行')
for page in range(1, 4):
    url2 = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num=100&sort=changepercent&asc=0&node=hk_h'
    try:
        resp2 = urllib.request.urlopen(urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
        data2 = json.loads(resp2.read().decode())
        print(f'  Page {page}: {len(data2) if data2 else 0} stocks')
        if data2:
            print(f'    First: {data2[0].get("code", "?")}')
    except Exception as e:
        print(f'  Page {page}: ERR {str(e)[:100]}')
        break

# 3. akshare 港股
print('Test3: akshare 港股')
try:
    import akshare as ak
    t = time.time()
    df = ak.stock_hk_hist(symbol='00700', period='daily', adjust='qfq', timeout=15)
    print(f'  00700: {len(df)} rows in {time.time()-t:.1f}s')
except Exception as e:
    err = str(e)
    if 'PROXY' in err.upper():
        print(f'  代理问题')
    else:
        print(f'  ERR: {err[:200]}')
