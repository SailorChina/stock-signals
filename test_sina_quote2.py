import urllib.request, time

# Test Sina quote API for different markets
# A-shares
codes_a = 'sh600519,sz000858,sh601318'
# HK
codes_hk = 'hk00700,hk00001,hk09988'

for name, codes in [('A-share', codes_a), ('HK', codes_hk)]:
    t = time.time()
    try:
        url = f'http://hq.sinajs.cn/list={codes}'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode('gbk')
        print(f"sina quote {name}: {time.time()-t:.2f}s, len={len(data)}")
        for line in data.strip().split(';'):
            if line.strip():
                print(f"  {line[:120]}")
    except Exception as e:
        print(f"sina quote {name}: ERROR {str(e)[:100]}")
