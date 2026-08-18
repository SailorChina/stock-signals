
import sys, time, inspect
sys.stdout.reconfigure(line_buffering=True)
import akshare as ak

# List relevant functions
funcs = [f for f in dir(ak) if 'spot' in f.lower() or 'sina' in f.lower()]
print("Relevant functions:", funcs[:30])

# Check sina direct URL
sys.path.insert(0, 'D:/Backup/Documents/ChatGPT/AI/stock-signals')
from stock_signals.akshare_data import _fetch_sina_direct
src = inspect.getsource(_fetch_sina_direct)
print("\n=== _fetch_sina_direct source ===")
print(src[:1000])
