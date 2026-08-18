
import sys
import time
sys.path.insert(0, 'D:\\Backup\\Documents\\ChatGPT\\AI\\stock-signals')

from stock_signals.indicators import fetch_realtime, fetch_kline
from stock_signals.hot_fetcher import fetch_hot_stocks
from stock_signals.data_sources import fetch_stock_list

print("=" * 70)
print("最终测试报告")
print("=" * 70)

# 测试1: 实时行情
print("\n[测试 1] 实时行情获取")
t0 = time.time()
a_result = fetch_realtime(["SH.600519", "SZ.000001"])
hk_result = fetch_realtime(["HK.00700", "HK.09988"])
us_result = fetch_realtime(["US.AAPL", "US.MSFT"])
dt = time.time() - t0
print(f"  A股: {len(a_result)} 只 (贵州茅台: {a_result.get('SH.600519', {}).get('price', 0):.2f})")
print(f"  港股: {len(hk_result)} 只 (腾讯: {hk_result.get('HK.00700', {}).get('price', 0):.2f})")
print(f"  美股: {len(us_result)} 只 (AAPL: {us_result.get('US.AAPL', {}).get('price', 0):.2f})")
print(f"  总耗时: {dt:.2f}s")

# 测试2: 热门股获取
print("\n[测试 2] 热门股获取")
t0 = time.time()
a_hot = fetch_hot_stocks("A", top_n=10)
hk_hot = fetch_hot_stocks("HK", top_n=10)
us_hot = fetch_hot_stocks("US", top_n=10)
dt = time.time() - t0
print(f"  A股热门: {len(a_hot)} 只 ({dt:.1f}s)")
print(f"  港股热门: {len(hk_hot)} 只")
print(f"  美股热门: {len(us_hot)} 只")

# 测试3: K线数据
print("\n[测试 3] K线数据获取")
t0 = time.time()
a_kline = fetch_kline("SH.600519", ktype="1d", num=100)
dt = time.time() - t0
print(f"  A股K线: {len(a_kline)} 行 ({dt:.2f}s)")
print(f"  港股K线: 0 行 (暂不支持)")
print(f"  美股K线: 0 行 (暂不支持)")

# 测试4: 股票列表
print("\n[测试 4] 股票列表获取")
t0 = time.time()
a_list = fetch_stock_list("A", top_n=100)
hk_list = fetch_stock_list("HK", top_n=50)
us_list = fetch_stock_list("US", top_n=50)
dt = time.time() - t0
print(f"  A股列表: {len(a_list)} 只 ({dt:.1f}s)")
print(f"  港股列表: {len(hk_list)} 只")
print(f"  美股列表: {len(us_list)} 只")

print("\n" + "=" * 70)
print("测试完成!")
print("=" * 70)
print("\n推荐方案:")
print("  A股: Sina API (实时行情 + K线) + akshare (热门股)")
print("  港股: 腾讯 API (实时行情) + 静态池 (K线)")
print("  美股: 腾讯 API (实时行情) + yfinance (K线备选)")
