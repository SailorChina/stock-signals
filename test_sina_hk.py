import urllib.request, time, json
nodes = ['hsHKStocks', 'hk_stock', 'hk', 'hsHK']
for node in nodes:
    t = time.time()
    try:
        url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=30&sort=changepercent&asc=0&node={node}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode()
        items = json.loads(data)
        print(f"{node}: {time.time()-t:.2f}s, items={len(items)}")
        if items:
            print(f"  first: {items[0].get('symbol')}, {items[0].get('name')}")
    except Exception as e:
        print(f"{node}: ERROR {str(e)[:80]}")
