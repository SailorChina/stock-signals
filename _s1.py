
import time, sys
sys.path.insert(0, '.')
from stock_signals.screener import _analyze_one
t = time.time()
r = _analyze_one('SH.600519')
print(f'score={r.score if r else None} time={time.time()-t:.1f}s')
