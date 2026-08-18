import urllib.request, time, json

nodes = [
    ('A-share', 'hs_a'),
    ('HK', 'hsHKStocks'),
    ('US', 'us'),
    ('All', 'all'),
]

for name, node in nodes:
    t = time.time()
    try:
        url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=30&sort=changepercent&asc=0&node={node}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode()
        items = json.loads(data)
        print(f"sina {name} ({node}): {time.time()-t:.2f}s, items={len(items)}")
        if items:
            print(f"  first: {items[0].get('symbol')}, {items[0].get('name')}, change={items[0].get('changepercent')}%")
    except Exception as e:
        print(f"sina {name} ({node}): ERROR {str(e)[:100]}")
