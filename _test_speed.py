
import sys
import time
import urllib.request
import json

print("=" * 60)
print("API 速度测试")
print("=" * 60)

# 测试腾讯港股列表
print("\n[1] 腾讯港股列表")
t0 = time.time()
url = "https://qt.gtimg.cn/q=hk_all"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
resp = urllib.request.urlopen(req, timeout=10)
data = resp.read().decode('gbk')
dt = time.time() - t0
lines = data.strip().split('\n')
valid = sum(1 for l in lines if '~' in l)
print(f"  耗时: {dt:.2f}s, 股票数: {valid}")

# 测试腾讯美股列表
print("\n[2] 腾讯美股列表")
t0 = time.time()
url = "https://qt.gtimg.cn/q=us_all"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
resp = urllib.request.urlopen(req, timeout=10)
data = resp.read().decode('gbk')
dt = time.time() - t0
lines = data.strip().split('\n')
valid = sum(1 for l in lines if '~' in l)
print(f"  耗时: {dt:.2f}s, 股票数: {valid}")

# 测试Sina A股热门
print("\n[3] Sina A股热门")
t0 = time.time()
url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=100&sort=changepercent&asc=0&node=hs_a"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "http://finance.sina.com.cn/"})
resp = urllib.request.urlopen(req, timeout=5)
data = resp.read().decode()
items = json.loads(data)
dt = time.time() - t0
print(f"  耗时: {dt:.2f}s, 股票数: {len(items)}")

# 测试A股K线
print("\n[4] Sina A股K线")
t0 = time.time()
url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=100"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
resp = urllib.request.urlopen(req, timeout=10)
data = resp.read().decode()
items = json.loads(data)
dt = time.time() - t0
print(f"  耗时: {dt:.2f}s, K线数: {len(items)}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
