
import os
import time
import urllib.request
import json

# 清除代理
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        os.environ.pop(k)

print("=" * 70)
print("港股/美股 API 最终测试")
print("=" * 70)

results = {}

# 1. 腾讯港股实时
print("\n[1] 腾讯 港股实时")
try:
    url = "https://qt.gtimg.cn/q=hk00700,hk00001,hk0939"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time()
    data = resp.read().decode('gbk')
    dt = time.time() - dt
    lines = data.strip().split('\n')
    valid = sum(1 for l in lines if '~' in l and len(l.split('~')) > 40)
    results['tencent_hk_realtime'] = valid > 0
    print(f"  {'OK' if results['tencent_hk_realtime'] else 'FAIL'}: {dt:.2f}s, {valid} stocks")
except Exception as e:
    results['tencent_hk_realtime'] = False
    print(f"  FAIL: {e}")

# 2. 腾讯美股实时
print("\n[2] 腾讯 美股实时")
try:
    url = "https://qt.gtimg.cn/q=usAAPL,usGOOGL,usMSFT"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time()
    data = resp.read().decode('gbk')
    dt = time.time() - dt
    lines = data.strip().split('\n')
    valid = sum(1 for l in lines if '~' in l and len(l.split('~')) > 40)
    results['tencent_us_realtime'] = valid > 0
    print(f"  {'OK' if results['tencent_us_realtime'] else 'FAIL'}: {dt:.2f}s, {valid} stocks")
except Exception as e:
    results['tencent_us_realtime'] = False
    print(f"  FAIL: {e}")

# 3. Sina港股实时
print("\n[3] Sina 港股实时")
try;
    url = "http://hq.sinajs.cn/list=hk00700,hk00001"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time()
    data = resp.read().decode('gbk')
    dt = time.time() - dt
    lines = data.strip().split(';')
    valid = sum(1 for l in lines if '=' in l and len(l.split('=',1)[1].strip('\"')) > 50)
    results['sina_hk_realtime'] = valid > 0
    print(f"  {'OK' if results['sina_hk_realtime'] else 'FAIL'}: {dt:.2f}s, {valid} stocks")
except Exception as e:
    results['sina_hk_realtime'] = False
    print(f"  FAIL: {e}")

# 4. Sina美股实时
print("\n[4] Sina 美股实时")
try:
    url = "http://hq.sinajs.cn/list=usAAPL,usGOOGL"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time()
    data = resp.read().decode('gbk')
    dt = time.time() - dt
    has_data = len(data.strip('\";')) > 100
    results['sina_us_realtime'] = has_data
    print(f"  {'OK' if results['sina_us_realtime'] else 'FAIL'}: {dt:.2f}s, len={len(data)}")
except Exception as e:
    results['sina_us_realtime'] = False
    print(f"  FAIL: {e}")

# 5. Sina港股K线
print("\n[5] Sina 港股K线")
try:
    url = "http://stock.finance.sina.com.cn/hkstock/api/json_v2.php/HK_StockData.getKLineData?symbol=hk00700&type=daily&num=10"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time()
    data = resp.read().decode()
    dt = time.time() - dt
    if data and data.strip() and data.strip() not in ('null', '[]'):
        items = json.loads(data)
        if isinstance(items, list) and len(items) > 0:
            results['sina_hk_kline'] = True
            print(f"  OK: {dt:.2f}s, {len(items)} rows")
        else:
            results['sina_hk_kline'] = False
            print(f"  FAIL: empty list")
    else:
        results['sina_hk_kline'] = False
        print(f"  FAIL: empty data")
except Exception as e:
    results['sina_hk_kline'] = False
    print(f"  FAIL: {str(e)[:50]}")

# 6. Sina美股K线
print("\n[6] Sina 美股K线")
try:
    url = "http://stock.finance.sina.com.cn/usstock/api/json_v2.php/US_StockData.getKLineData?symbol=usAAPL&type=daily&num=10"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time()
    data = resp.read().decode()
    dt = time.time() - dt
    if data and data.strip() and data.strip() not in ('null', '[]'):
        items = json.loads(data)
        if isinstance(items, list) and len(items) > 0:
            results['sina_us_kline'] = True
            print(f"  OK: {dt:.2f}s, {len(items)} rows")
        else:
            results['sina_us_kline'] = False
            print(f"  FAIL: empty list")
    else:
        results['sina_us_kline'] = False
        print(f"  FAIL: empty data")
except Exception as e:
    results['sina_us_kline'] = False
    print(f"  FAIL: {str(e)[:50]}")

# 7. akshare港股
print("\n[7] akshare 港股")
try:
    import akshare as ak
    t0 = time.time()
    df = ak.stock_hk_hist(symbol="00700", period="daily", adjust="qfq")
    dt = time.time() - t0
    results['akshare_hk'] = len(df) > 0
    print(f"  {'OK' if results['akshare_hk'] else 'FAIL'}: {dt:.2f}s, {len(df)} rows")
except Exception as e:
    results['akshare_hk'] = False
    print(f"  FAIL: {str(e)[:50]}")

# 8. akshare美股
print("\n[8] akshare 美股")
try:
    import akshare as ak
    t0 = time.time()
    df = ak.stock_us_hist(symbol="105.AAPL", period="daily", adjust="qfq")
    dt = time.time() - t0
    results['akshare_us'] = len(df) > 0
    print(f"  {'OK' if results['akshare_us'] else 'FAIL'}: {dt:.2f}s, {len(df)} rows")
except Exception as e:
    results['akshare_us'] = False
    print(f"  FAIL: {str(e)[:50]}")

# 汇总
print("\n" + "=" * 70)
print("测试结果汇总")
print("=" * 70)
for k, v in results.items():
    print(f"  {k}: {'OK' if v else 'FAIL'}")

# 推荐方案
print("\n" + "=" * 70)
print("推荐方案")
print("=" * 70)

hk_ok = [k for k, v in results.items() if v and 'hk' in k.lower()]
us_ok = [k for k, v in results.items() if v and 'us' in k.lower()]

print(f"\n港股可用: {', '.join(hk_ok) if hk_ok else '无'}")
print(f"美股可用: {', '.join(us_ok) if us_ok else '无'}")
