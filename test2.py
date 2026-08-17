
import sys, logging
logging.basicConfig(level=logging.INFO)
sys.path.insert(0, r'D:/Backup/Documents/ChatGPT/AI/stock-signals')
from stock_signals.screener import _fetch_hot_stocks
result = _fetch_hot_stocks('US')
print(f'热门股数量: {len(result)}')
if result:
    print(f'前10只: {result[:10]}')
