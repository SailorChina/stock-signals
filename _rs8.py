
import sys, json, logging
logging.basicConfig(level=logging.INFO)
sys.path.insert(0, r'D:/Backup/Documents/ChatGPT/AI/stock-signals')
from stock_signals.screener import scan, ScanConfig
cfg = ScanConfig(min_score=55, max_per_market=5)
result = scan(markets=['US'], config=cfg)
with open(r'D:/Backup/Documents/ChatGPT/AI/stock-signals/scan_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f'分析股票数: {result["summary"]["total_analyzed"]}')
print(f'推荐股票数: {result["summary"]["total_picks"]}')
print('推荐列表:')
for s in result.get('picks', {}).get('US', []):
    print(f'  {s.code}: 评分{s.score}, 评级{s.rating}')
