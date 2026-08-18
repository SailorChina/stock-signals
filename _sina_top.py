
import urllib.request, json, time
apis = [
    ('A股涨幅榜', 'http://vip.stock.finance.sina.com.cn/q/go_kind/search_a.php?sort=changepercent&asc=0&node=hs_a&p=1'),
    ('美股涨幅榜', 'http://vip.stock.finance.sina.com.cn/q/go_kind/search_us.php?sort=changepercent&asc=0&node=all&p=1'),
]
for name, url in apis:
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('gbk', errors='ignore')
        t1 = time.time()
        items = json.loads(data)
        print(f'{name}: {t1-t0:.2f}s, {len(items)} stocks')
        for it in items[:5]: print(f'  {it.get("symbol","?")} {it.get("name","?")} {it.get("changepercent","?")}%')
    except Exception as e:
        print(f'{name}: ERR {type(e).__name__}: {str(e)[:100]}')
print('DONE')
