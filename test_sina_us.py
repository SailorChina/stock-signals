import urllib.request, time
formats = ['usNVDA', 'usAAPL', 'ibm', 'aapl', 'nvda', '^GSPC', '^IXIC', '^DJI']
for code in formats:
    t = time.time()
    try:
        url = f'http://hq.sinajs.cn/list={code}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn'})
        resp = urllib.request.urlopen(req, timeout=3)
        data = resp.read().decode('gbk')
        has_data = len(data.strip()) > 50
        print(f"{code}: {time.time()-t:.2f}s, len={len(data)}, has_data={has_data}, first={data[:80]}")
    except Exception as e:
        print(f"{code}: ERROR {str(e)[:60]}")
