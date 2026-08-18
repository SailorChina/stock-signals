import urllib.request, time
try:
    url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=30&sort=changepercent&asc=0&node=hs_a"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=5)
    data = resp.read().decode()
    print(f"sina hs_a: time={time.time():.2f}, len={len(data)}")
    print(data[:300])
except Exception as e:
    print(f"ERROR: {e}")
