import sys, time
sys.path.insert(0, r'D:\Backup\Documents\ChatGPT\AI\stock-signals')
from stock_signals.screener import sync_hot_stocks
t = time.time()
n = sync_hot_stocks('A', 300)
print(f'Synced {n} A-share hot stocks in {time.time()-t:.1f}s')
