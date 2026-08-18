
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

print('Test1: Sina 美股排行')
for node in ['us_a', 'us_hk', 'us_n']:
    url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=100&sort=changepercent&asc=0&node={node}'
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
        data = json.loads(resp.read().decode())
        print(f'  {node}: {len(data) if data else 0} stocks')
    except Exception as e:
        print(f'  {node}: ERR {str(e)[:100]}')

print('Test2: Sina 美股行情')
url2 = 'http://hq.sinajs.cn/list=usAAPL,usGOOGL,usMSFT,usTSLA,usAMZN'
try:
    resp2 = urllib.request.urlopen(urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
    data2 = resp2.read().decode('gbk')
    lines = [l for l in data2.split('\n') if l.strip() and 'hq_str_us' in l]
    print(f'  OK: {len(lines)} stocks')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')
