
import sys; sys.path.insert(0, '.')
from stock_signals.screener import sync_hot_stocks, _get_market_codes
n = sync_hot_stocks('A', 300)
print(f'Synced {n} stocks')
codes = _get_market_codes('A')
print(f'Market codes: {len(codes)}, first 5: {codes[:5]}')
