
import os
import time
import urllib.request
import json

# 清除代理
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        os.environ.pop(k)

print("=" * 60)
print("港股/美股 API 全面测试")
print("=" * 60)

results = {}

# 1. 测试 akshare 港股
print("\n[1] akshare 港股 hist")
try:
    import akshare as ak
    t0 = time.time()
    df = ak.stock_hk_hist(symbol="00700", period="daily", adjust="qfq")
    dt = time.time() - t0
    results['akshare_hk_hist'] = len(df) > 0
    print(f"  {'OK' if results['akshare_hk_hist'] else 'FAIL'}: {len(df)} rows, {dt:.2f}s")
except Exception as e:
    results['akshare_hk_hist'] = False
    print(f"  FAIL: {e}")

# 2. 测试 akshare 港股排行
print("\n[2] akshare 港股 spot")
try:
    import akshare as ak
    t0 = time.time()
    df = ak.stock_hk_spot_em()
    dt = time.time() - t0
    results['akshare_hk_spot'] = len(df) > 0
    print(f"  {'OK' if results['akshare_hk_spot'] else 'FAIL'}: {len(df)} rows, {dt:.2f}s")
except Exception as e:
    results['akshare_hk_spot'] = False
    print(f"  FAIL: {e}")

# 3. 测试 akshare 美股
print("\n[3] akshare 美股 hist")
try:
    import akshare as ak
    t0 = time.time()
    df = ak.stock_us_hist(symbol="105.AAPL", period="daily", adjust="qfq")
    dt = time.time() - t0
    results['akshare_us_hist'] = len(df) > 0
    print(f"  {'OK' if results['akshare_us_hist'] else 'FAIL'}: {len(df)} rows, {dt:.2f}s")
except Exception as e:
    results['akshare_us_hist'] = False
    print(f"  FAIL: {e}")

# 4. 测试 akshare 美股排行
print("\n[4] akshare 美股 spot")
try:
    import akshare as ak
    t0 = time.time()
    df = ak.stock_us_spot_em()
    dt = time.time() - t0
    results['akshare_us_spot'] = len(df) > 0
    print(f"  {'OK' if results['akshare_us_spot'] else 'FAIL'}: {len(df)} rows, {dt:.2f}s")
except Exception as e:
    results['akshare_us_spot'] = False
    print(f"  FAIL: {e}")

# 5. 测试 Sina 港股实时
print("\n[5] Sina 港股实时")
try:
    t0 = time.time()
    url = "http://hq.sinajs.cn/list=hk00700,hk00001,hk0939"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode('gbk')
    results['sina_hk_realtime'] = len(data) > 100
    print(f"  {'OK' if results['sina_hk_realtime'] else 'FAIL'}: {dt:.2f}s, {len(data)} chars")
except Exception as e:
    results['sina_hk_realtime'] = False
    print(f"  FAIL: {e}")

# 6. 测试 Sina 美股实时
print("\n[6] Sina 美股实时")
try:
    t0 = time.time()
    url = "http://hq.sinajs.cn/list=usAAPL,usGOOGL,usMSFT"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode('gbk')
    results['sina_us_realtime'] = len(data) > 100
    print(f"  {'OK' if results['sina_us_realtime'] else 'FAIL'}: {dt:.2f}s, {len(data)} chars")
except Exception as e:
    results['sina_us_realtime'] = False
    print(f"  FAIL: {e}")

# 7. 测试 东方财富 港股排行
print("\n[7] 东方财富 港股排行")
try:
    t0 = time.time()
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=50&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:HK.HK+m:HK.MB&fields=f2,f3,f4,f12,f14"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = json.loads(resp.read().decode())
    results['eastmoney_hk_rank'] = bool(data.get('data', {}).get('diff'))
    if results['eastmoney_hk_rank']:
        items = data['data']['diff']
        print(f"  OK: {len(items)} stocks, {dt:.2f}s")
    else:
        print(f"  FAIL: no data")
except Exception as e:
    results['eastmoney_hk_rank'] = False
    print(f"  FAIL: {e}")

# 8. 测试 东方财富 美股排行
print("\n[8] 东方财富 美股排行")
try:
    t0 = time.time()
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=50&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:US.NASDAQ&fields=f2,f3,f4,f12,f14"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = json.loads(resp.read().decode())
    results['eastmoney_us_rank'] = bool(data.get('data', {}).get('diff'))
    if results['eastmoney_us_rank']:
        items = data['data']['diff']
        print(f"  OK: {len(items)} stocks, {dt:.2f}s")
    else:
        print(f"  FAIL: no data")
except Exception as e:
    results['eastmoney_us_rank'] = False
    print(f"  FAIL: {e}")

# 9. 测试 东方财富 港股K线
print("\n[9] 东方财富 港股K线")
try:
    t0 = time.time()
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=116.00700&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=20"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = json.loads(resp.read().decode())
    results['eastmoney_hk_kline'] = bool(data.get('data', {}).get('klines'))
    if results['eastmoney_hk_kline']:
        klines = data['data']['klines']
        print(f"  OK: {len(klines)} klines, {dt:.2f}s")
    else:
        print(f"  FAIL: no data")
except Exception as e:
    results['eastmoney_hk_kline'] = False
    print(f"  FAIL: {e}")

# 10. 测试 东方财富 美股K线
print("\n[10] 东方财富 美股K线")
try:
    t0 = time.time()
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AAPL&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=20"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = json.loads(resp.read().decode())
    results['eastmoney_us_kline'] = bool(data.get('data', {}).get('klines'))
    if results['eastmoney_us_kline']:
        klines = data['data']['klines']
        print(f"  OK: {len(klines)} klines, {dt:.2f}s")
    else:
        print(f"  FAIL: no data")
except Exception as e:
    results['eastmoney_us_kline'] = False
    print(f"  FAIL: {e}")

# 11. 测试 腾讯 港股
print("\n[11] 腾讯 港股")
try:
    t0 = time.time()
    url = "https://qt.gtimg.cn/q=hk00700,hk00001,hk0939"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode('gbk')
    results['tencent_hk'] = len(data) > 100
    print(f"  {'OK' if results['tencent_hk'] else 'FAIL'}: {dt:.2f}s, {len(data)} chars")
except Exception as e:
    results['tencent_hk'] = False
    print(f"  FAIL: {e}")

# 12. 测试 腾讯 美股
print("\n[12] 腾讯 美股")
try:
    t0 = time.time()
    url = "https://qt.gtimg.cn/q=usAAPL,usGOOGL,usMSFT"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode('gbk')
    results['tencent_us'] = len(data) > 100
    print(f"  {'OK' if results['tencent_us'] else 'FAIL'}: {dt:.2f}s, {len(data)} chars")
except Exception as e:
    results['tencent_us'] = False
    print(f"  FAIL: {e}")

# 汇总
print("\n" + "=" * 60)
print("测试结果汇总")
print("=" * 60)
for k, v in results.items():
    print(f"  {k}: {'OK' if v else 'FAIL'}")

# 推荐
print("\n" + "=" * 60)
print("推荐方案")
print("=" * 60)

hk_ok = [k for k, v in results.items() if v and 'hk' in k.lower()]
us_ok = [k for k, v in results.items() if v and 'us' in k.lower()]

print(f"\n港股可用: {', '.join(hk_ok) if hk_ok else '无'}")
print(f"美股可用: {', '.join(us_ok) if us_ok else '无'}")
