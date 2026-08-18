import urllib.request, time, json

# Retry Sina ranking with different approaches
urls = [
    ('normal', 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=30&sort=changepercent&asc=0&node=hs_a'),
    ('ssl', 'https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=30&sort=changepercent&asc=0&node=hs_a'),
]

for name, url in urls:
    t = time.time()
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://finance.sina.com.cn/',
            'Accept': 'application/json',
        })
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode()
        items = json.loads(data)
        print(f"{name}: {time.time()-t:.2f}s, items={len(items)}")
        if items:
            print(f"  first: {items[0].get('symbol')}, {items[0].get('name')}")
    except Exception as e:
        print(f"{name}: ERROR {str(e)[:100]}")

# Also try akshare hot rank
print("")
print("=== AKSHARE RETRY ===")
import akshare as ak
for fn_name in ['stock_hot_rank_em', 'stock_hot_rank_detail_em']:
    t = time.time()
    try:
        fn = getattr(ak, fn_name)
        df = fn()
        print(f"{fn_name}: {time.time()-t:.2f}s, rows={len(df)}")
    except Exception as e:
        print(f"{fn_name}: ERROR {str(e)[:80]}")
