
import urllib.request
import json

print("=== 测试 Sina K线对港股和美股的支持 ===")

# 测试Sina港股K线
print("\n=== Sina 港股K线 ===")
symbols = ["hk00700", "hk00001", "hk0939"]
for sym in symbols:
    try:
        url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/HK_StockData.getKLineData?symbol={sym}&type=daily&num=5"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        print(f"  {sym}: {len(data)} rows")
        if data:
            print(f"    最新: {data[-1]}")
    except Exception as e:
        print(f"  {sym}: ERROR - {e}")

# 测试Sina美股K线
print("\n=== Sina 美股K线 ===")
symbols = ["usAAPL", "usGOOGL", "usMSFT"]
for sym in symbols:
    try:
        url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/US_StockData.getKLineData?symbol={sym}&type=daily&num=5"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        print(f"  {sym}: {len(data)} rows")
        if data:
            print(f"    最新: {data[-1]}")
    except Exception as e:
        print(f"  {sym}: ERROR - {e}")

# 测试Sina实时行情解析
print("\n=== Sina 实时行情解析 ===")
# 港股
url = "http://hq.sinajs.cn/list=hk00700,hk00001"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
resp = urllib.request.urlopen(req, timeout=10)
data = resp.read().decode('gbk')
print(f"港股实时: {data[:200]}")

# 美股
url = "http://hq.sinajs.cn/list=usAAPL,usGOOGL"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
resp = urllib.request.urlopen(req, timeout=10)
data = resp.read().decode('gbk')
print(f"美股实时: {data[:200]}")
