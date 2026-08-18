import urllib.request, time, json

print("=== SINA RANK BY MARKET ===")
markets = [
    ('A-share', 'hs_a'),
    ('HK', 'hsHKStocks'),
    ('US', 'us'),
    ('All', 'all'),
    ('BSE', 'bj'),
]
for name, node in markets:
    t = time.time()
    try:
        url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=30&sort=changepercent&asc=0&node={node}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        items = json.loads(resp.read().decode())
        print(f"{name} ({node}): {time.time()-t:.2f}s, items={len(items)}")
        if items:
            print(f"  first: {items[0].get('symbol')}, {items[0].get('name')}, chg={items[0].get('changepercent')}%")
    except Exception as e:
        print(f"{name} ({node}): ERROR {str(e)[:80]}")

print("")
print("=== AKSHARE RETEST ===")
import akshare as ak
for fn_name in ['stock_hot_rank_em', 'stock_hk_hot_rank_em']:
    t = time.time()
    try:
        fn = getattr(ak, fn_name)
        df = fn()
        print(f"{fn_name}: {time.time()-t:.2f}s, rows={len(df)}")
    except Exception as e:
        print(f"{fn_name}: ERROR {str(e)[:100]}")
