
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

print('=== Sina 美股排行 ===')
nodes = ['us_a', 'us_hk', 'us_n']
for node in nodes:
    for page in range(1, 3):
        url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num=100&sort=changepercent&asc=0&node={node}'
        try:
            resp = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
            data = json.loads(resp.read().decode())
            if data:
                print(f'{node} page{page}: {len(data)} stocks, first={data[0].get("code", "?")}')
                break
        except Exception as e:
            if page == 1:
                print(f'{node}: ERR {str(e)[:100]}')
