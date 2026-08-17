
import sys, json, logging
logging.basicConfig(level=logging.INFO)
sys.path.insert(0, r'D:/Backup/Documents/ChatGPT/AI/stock-signals')
from stock_signals.screener import scan
result = scan(markets=['US'], output_json=False)
print(json.dumps(result, ensure_ascii=False, indent=2))
