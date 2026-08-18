
import os
import sys
import time
import urllib.request

print("=" * 60)
print("代理问题诊断")
print("=" * 60)

# 检查当前代理设置
print("\n[1] 当前代理设置")
proxy_vars = {k: v for k, v in os.environ.items() if 'proxy' in k.lower()}
if proxy_vars:
    print(f"  发现代理变量: {proxy_vars}")
else:
    print("  未发现代理变量")

# 清除代理后测试
print("\n[2] 清除代理后测试 akshare")
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        print(f"  清除: {k}={os.environ.pop(k)}")

try:
    import akshare as ak
    print("\n  [尝试] 港股历史数据")
    t0 = time.time()
    df = ak.stock_hk_hist(symbol="00700", period="daily", adjust="qfq")
    dt = time.time() - t0
    print(f"  结果: {len(df)} rows, {dt:.2f}s")
    if not df.empty:
        print(f"  最新数据: {df.iloc[-1].to_dict()}")
except Exception as e:
    print(f"  失败: {e}")

try:
    print("\n  [尝试] 美股历史数据")
    t0 = time.time()
    df = ak.stock_us_hist(symbol="105.AAPL", period="daily", adjust="qfq")
    dt = time.time() - t0
    print(f"  结果: {len(df)} rows, {dt:.2f}s")
    if not df.empty:
        print(f"  最新数据: {df.iloc[-1].to_dict()}")
except Exception as e:
    print(f"  失败: {e}")

try:
    print("\n  [尝试] 港股实时行情")
    t0 = time.time()
    df = ak.stock_hk_spot_em()
    dt = time.time() - t0
    print(f"  结果: {len(df)} rows, {dt:.2f}s")
except Exception as e:
    print(f"  失败: {e}")

try:
    print("\n  [尝试] 美股实时行情")
    t0 = time.time()
    df = ak.stock_us_spot_em()
    dt = time.time() - t0
    print(f"  结果: {len(df)} rows, {dt:.2f}s")
except Exception as e:
    print(f"  失败: {e}")

# 测试直接URL访问
print("\n[3] 直接测试 URL 连通性")
urls = [
    ("东方财富港股", "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=116.00700&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=5"),
    ("腾讯港股", "https://qt.gtimg.cn/q=hk00700"),
    ("Sina港股", "http://hq.sinajs.cn/list=hk00700"),
]

for name, url in urls:
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        dt = time.time() - t0
        data = resp.read()
        print(f"  {name}: OK, {dt:.2f}s, {len(data)} bytes")
    except Exception as e:
        print(f"  {name}: FAIL, {str(e)[:50]}")
