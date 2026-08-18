
import os
import urllib.request
import json
import time

print("=== 东方财富 API 测试（清除代理后） ===")

# 清除代理
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        os.environ.pop(k)

# 1. 测试东方财富港股K线
print("\n[1] 东方财富 港股K线")
try:
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=116.00700&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=10"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time()
    data = resp.read().decode()
    dt = time.time() - dt
    print(f"  耗时: {dt:.2f}s")
    print(f"  返回: {data[:300]}")
    
    jdata = json.loads(data)
    if jdata.get('data') and jdata['data'].get('klines'):
        klines = jdata['data']['klines']
        print(f"  K线: {len(klines)} rows")
        for k in klines[-3:]:
            print(f"    {k}")
except Exception as e:
    print(f"  ERROR: {e}")

# 2. 测试东方财富美股K线
print("\n[2] 东方财富 美股K线")
try:
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=105.AAPL&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=10"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time()
    data = resp.read().decode()
    dt = time.time() - dt
    print(f"  耗时: {dt:.2f}s")
    print(f"  返回: {data[:300]}")
    
    jdata = json.loads(data)
    if jdata.get('data') and jdata['data'].get('klines'):
        klines = jdata['data']['klines']
        print(f"  K线: {len(klines)} rows")
except Exception as e:
    print(f"  ERROR: {e}")

# 3. 测试东方财富港股排行
print("\n[3] 东方财富 港股排行")
try:
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=50&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:HK.HK+m:HK.MB&fields=f2,f3,f4,f12,f14"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time()
    data = resp.read().decode()
    dt = time.time() - dt
    print(f"  耗时: {dt:.2f}s")
    
    jdata = json.loads(data)
    if jdata.get('data') and jdata['data'].get('diff'):
        items = jdata['data']['diff']
        print(f"  返回 {len(items)} 条股票")
        for item in items[:5]:
            print(f"    {item.get('f14')}: 代码={item.get('f12')}, 当前={item.get('f2')}")
except Exception as e:
    print(f"  ERROR: {e}")

# 4. 测试东方财富美股排行
print("\n[4] 东方财富 美股排行")
try:
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=50&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:US.NASDAQ&fields=f2,f3,f4,f12,f14"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time()
    data = resp.read().decode()
    dt = time.time() - dt
    print(f"  耗时: {dt:.2f}s")
    
    jdata = json.loads(data)
    if jdata.get('data') and jdata['data'].get('diff'):
        items = jdata['data']['diff']
        print(f"  返回 {len(items)} 条股票")
        for item in items[:5]:
            print(f"    {item.get('f14')}: 代码={item.get('f12')}, 当前={item.get('f2')}")
except Exception as e:
    print(f"  ERROR: {e}")
