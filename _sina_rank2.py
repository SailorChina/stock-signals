
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

print('=== Sina 排行测试 ===')
for market, node in [('港股', 'hk_h'), ('美股', 'us_a')]:
    print(f'{market}:')
    for page in range(1, 4):
        url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num=100&sort=changepercent&asc=0&node={node}'
        try:
            resp = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
            data = json.loads(resp.read().decode())
            print(f'  page{page}: {len(data) if data else 0} stocks')
            if data:
                print(f'    First: {data[0].get("code", "?")}')
                break
        except Exception as e:
            if page == 1:
                print(f'  ERR: {str(e)[:100]}')
            break
