import urllib.request, time
tests = [
    ('sina hq', 'http://hq.sinajs.cn/list=sh600519'),
    ('eastmoney push2 https', 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m%3A105%2Cc%3AN20001&fields=f12,f14'),
    ('eastmoney push2 http', 'http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m%3A105%2Cc%3AN20001&fields=f12,f14'),
    ('sina top api', 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=5&sort=changepercent&asc=0&node=hs_a'),
]
for name, url in tests:
    t = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode()
        print(f"{name}: {time.time()-t:.2f}s, len={len(data)}, first={data[:100]}")
    except Exception as e:
        print(f"{name}: ERROR {str(e)[:100]}")
