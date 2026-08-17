
import sys
sys.path.insert(0, r'D:/Backup/Documents/ChatGPT/AI/stock-signals')
from stock_signals.screener import _get_market_codes
codes = _get_market_codes('US')
print(f'候选池数量: {len(codes)}')
print(f'前20只: {codes[:20]}')
