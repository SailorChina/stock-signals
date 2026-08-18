import urllib.request, time
markets = [("us", "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=30&sort=changepercent&asc=0&node=us"), ("hk", "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=30&sort=changepercent&asc=0&node=hsHKStocks")]
for name, url in markets:
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode()
        print(f"sina {name}: time={time.time()-t0:.2f}s, len={len(data)}")
    except Exception as e:
        print(f"sina {name} ERROR: {e}")
