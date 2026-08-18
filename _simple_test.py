
import os
import sys

# 清除代理
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        os.environ.pop(k)

sys.path.insert(0, 'D:\\Backup\\Documents\\ChatGPT\\AI\\stock-signals')

print("测试导入...")
try:
    from stock_signals.indicators import fetch_realtime, fetch_kline
    print("  OK: indicators 导入成功")
except Exception as e:
    print(f"  ERROR: indicators 导入失败: {e}")

try:
    from stock_signals.hot_fetcher import fetch_hot_stocks
    print("  OK: hot_fetcher 导入成功")
except Exception as e:
    print(f"  ERROR: hot_fetcher 导入失败: {e}")

print("\n测试完成!")
