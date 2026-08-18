import akshare as ak, time

# Test Sina quote for US stocks with different code format
tests = [
    ('sina us nasdaq', 'http://hq.sinajs.cn/list=ibm,csco'),
    ('sina us nasdaq2', 'http://hq.sinajs.cn/list=^IXIC'),
]
for name, url in tests:
    t = time.time()
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode('gbk')
        print(f"{name}: {time.time()-t:.2f}s, len={len(data)}, data={data[:200]}")
    except Exception as e:
        print(f"{name}: ERROR {e}")

# Test akshare stock_us_hist for a single stock
t = time.time()
try:
    df = ak.stock_us_hist(symbol="03700", period="daily", start_date="20250801", end_date="20260818", adjust="")
    print(f"\nstock_us_hist HK03700: {time.time()-t:.2f}s, rows={len(df)}")
except Exception as e:
    print(f"\nstock_us_hist ERROR: {e}")
