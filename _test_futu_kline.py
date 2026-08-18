
import sys
sys.path.insert(0, 'D:\\Backup\\Documents\\ChatGPT\\AI\\stock-signals')

from stock_signals.indicators import fetch_kline
import time

print("测试 Futu K线...")
print("=" * 50)

# A股
print("")
print("[A股 K线]")
t0 = time.time()
df = fetch_kline("SH.600519", ktype="1d", num=100)
dt = time.time() - t0
print("  结果: " + str(len(df)) + " 行, " + str(round(dt, 2)) + "s")
if not df.empty:
    print("  最新: " + str(df.iloc[-1].to_dict()))

# 港股
print("")
print("[港股 K线]")
t0 = time.time()
df = fetch_kline("HK.00700", ktype="1d", num=100)
dt = time.time() - t0
print("  结果: " + str(len(df)) + " 行, " + str(round(dt, 2)) + "s")
if not df.empty:
    print("  最新: " + str(df.iloc[-1].to_dict()))

# 美股
print("")
print("[美股 K线]")
t0 = time.time()
df = fetch_kline("US.AAPL", ktype="1d", num=100)
dt = time.time() - t0
print("  结果: " + str(len(df)) + " 行, " + str(round(dt, 2)) + "s")
if not df.empty:
    print("  最新: " + str(df.iloc[-1].to_dict()))

print("")
print("=" * 50)
print("测试完成!")
