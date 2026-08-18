import requests, time, json
headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn'}
for node in ['hs_a', 'hsHKStocks', 'us']:
    t = time.time()
    try:
        url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=10&sort=changepercent&asc=0&node={node}'
        resp = requests.get(url, headers=headers, timeout=5)
        items = resp.json()
        print(f'{node}: {time.time()-t:.2f}s, items={len(items)}')
        if items:
            print(f'  first: {items[0].get("symbol")}')
    except Exception as e:
        print(f'{node}: ERROR {str(e)[:80]}')
