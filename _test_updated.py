
import os
import sys
import time

# 清除代理
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        os.environ.pop(k)

sys.path.insert(0, 'D:\\Backup\\Documents\\ChatGPT\\AI\\stock-signals')

from stock_signals.indicators import fetch_realtime, fetch_kline
from stock_signals.hot_fetcher import fetch_hot_stocks

print("=" * 60)
print("更新后测试（清除代理）")
print("=" * 60)

# 测试实时行情
print("\n[1] 实时行情")
a_rt = fetch_realtime(["SH.600519", "HK.00700", "US.AAPL"])
print(f"  返回: {len(a_rt)} 只")
for k, v in a_rt.items():
    print(f"    {k}: price={v.get('price', 0):.2f}")

# 测试K线
print("\n[2] K线数据")
t0 = time.time()
a_kline = fetch_kline("SH.600519", ktype="1d", num=100)
dt = time.time() - t0
print(f"  A股: {len(a_kline)} 行, {dt:.2f}s")

t0 = time.time()
us_kline = fetch_kline("US.AAPL", ktype="1d", num=100)
dt = time.time() - t0
print(f"  美股: {len(us_kline)} 行, {dt:.2f}s")

t0 = time.time()
hk_kline = fetch_kline("HK.00700", ktype="1d", num=100)
dt = time.time() - t0
print(f"  港股: {len(hk_kline)} 行, {dt:.2f}s")

# 测试热门股
print("\n[3] 热门股")
t0 = time.time()
a_hot = fetch_hot_stocks("A", top_n=5)
dt = time.time() - t0
print(f"  A股: {len(a_hot)} 只, {dt:.2f}s")

print("\n测试完成!")
