import sys, logging, time
logging.basicConfig(level=logging.INFO, format='%(message)s')
sys.path.insert(0, r'D:\Backup\Documents\ChatGPT\AI\stock-signals')
from stock_signals.screener import _analyze_one
t = time.time()
r = _analyze_one('SH.600519', delay=0.3)
print(f'Time: {time.time()-t:.1f}s')
if r:
    print(f'score={r.score:.1f} rating={r.rating} phase={r.trend_phase}')
    print(f'entry={r.entry} stop={r.stop_loss} rr={r.risk_reward}')
else:
    print('No result')
