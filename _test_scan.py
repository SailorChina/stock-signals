
import sys
sys.path.insert(0, 'D:\\Backup\\Documents\\ChatGPT\\AI\\stock-signals')

from stock_signals.screener import scan_parallel, ScanConfig

print("扫描测试:")
config = ScanConfig(max_per_market=3)
result = scan_parallel(["A"], config=config)
print(f"\nA股扫描结果: {len(result['picks'])} 只")
for pick in result['picks'][:3]:
    print(f"  {pick}")
print("\n完成!")
