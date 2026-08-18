import urllib.request, time, json
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'http://finance.sina.com.cn/stock/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}
for node in ['hs_a', 'hsHKStocks', 'us']:
    t = time.time()
    try:
        url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=10&sort=changepercent&asc=0&node={node}'
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode()
        items = json.loads(data)
        print(f"{node}: {time.time()-t:.2f}s, items={len(items)}")
        if items:
            print(f"  first: {items[0].get('symbol')}, {items[0].get('name')}")
    except Exception as e:
        print(f"{node}: ERROR {str(e)[:80]}")
