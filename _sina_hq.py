
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

print('港股实时行情:')
url = 'http://hq.sinajs.cn/list=hk00700,hk00001,hk9988,hk3690,hk01299,hk09618,hk09961,hk02015,hk02382,hk00941'
try:
    resp = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
    data = resp.read().decode('gbk')
    lines = [l for l in data.split('\n') if l.strip() and 'hq_str_hk' in l]
    print(f'  OK: {len(lines)} stocks')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')

print('美股实时行情:')
url2 = 'http://hq.sinajs.cn/list=usAAPL,usGOOGL,usMSFT,usTSLA,usAMZN,usNVDA,usMETA,usNFLX,usAMD,usINTC'
try:
    resp2 = urllib.request.urlopen(urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
    data2 = resp2.read().decode('gbk')
    lines2 = [l for l in data2.split('\n') if l.strip() and 'hq_str_us' in l]
    print(f'  OK: {len(lines2)} stocks')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')
