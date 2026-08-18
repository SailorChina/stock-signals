
import os, urllib.request
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'
def q(url):
    r = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    return urllib.request.urlopen(r, timeout=15).read()
print('Tencent HK r_hk00700:', repr(q('https://qt.gtimg.cn/q=r_hk00700').decode('gbk')[:200]))
print('Tencent HK hk00700:', repr(q('https://qt.gtimg.cn/q=hk00700').decode('gbk')[:200]))
print('Sina HK hq00700:', repr(q('https://hq.sinajs.cn/list=hk00700').decode('gbk')[:300]))
print('Sina US us_aapl:', repr(q('https://hq.sinajs.cn/list=us_aapl').decode('utf-8',errors='replace')[:300]))
print('Sina US AAPL:', repr(q('https://hq.sinajs.cn/list=AAPL').decode('utf-8',errors='replace')[:300]))
