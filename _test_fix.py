
import sys, logging
logging.basicConfig(level=logging.INFO)
sys.path.insert(0, r'D:/Backup/Documents/ChatGPT/AI/stock-signals')
from stock_signals.screener import _fetch_hot_stocks, _US_HOT_STOCKS_POOL
print(f'_US_HOT_STOCKS_POOL 数量: {len(_US_HOT_STOCKS_POOL)}')
result = _fetch_hot_stocks('US')
print(f'热门股数量: {len(result)}')
if result:
    print(f'前15只: {result[:15]}')
else:
    print('未获取到热门股')
