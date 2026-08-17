
import sys, json, logging
logging.basicConfig(level=logging.INFO)
sys.path.insert(0, r'D:/Backup/Documents/ChatGPT/AI/stock-signals')
from stock_signals.screener import scan
result = scan(markets=['US'], output_json=True)
print(f'分析股票数: {result["summary"]["total_analyzed"]}')
print(f'推荐股票数: {result["summary"]["total_picks"]}')
print(f'推荐列表: {[(s.code, s.score) for s in result["picks"]["US"]]}')
