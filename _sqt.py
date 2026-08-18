
import urllib.request, json, time, sys
sys.stdout.reconfigure(line_buffering=True)
print("=== Sina Rank API ===", flush=True)
apis = [
    ('A股涨幅榜', 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=300&sort=changepercent&asc=0&node=hs_a&symbol=&_s_r_a=page'),
    ('美股涨幅榜', 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=300&sort=changepercent&asc=0&node=all&symbol=&_s_r_a=page'),
    ('港股涨幅榜', 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=300&sort=changepercent&asc=0&node=hsHKStocks&symbol=&_s_r_a=page'),
]
for name, url in apis:
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('gbk', errors='ignore')
        t1 = time.time()
        items = json.loads(data)
        print(f'{name}: {t1-t0:.2f}s, {len(items)} stocks', flush=True)
        for it in items[:3]: print(f"  {it.get('symbol','?')} {it.get('name','?')} {it.get('changepercent','?')}%", flush=True)
    except Exception as e:
        print(f'{name}: ERR {type(e).__name__}: {str(e)[:100]}', flush=True)
print('DONE')
