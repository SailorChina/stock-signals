
import time, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
from stock_signals.screener import _get_market_codes, scan_parallel, ScanConfig

codes = _get_market_codes('A')
print(f"A codes: {len(codes)}, first 3: {codes[:3]}")

# Manual test of one stock
from stock_signals.indicators import fetch_kline, compute_indicators
from stock_signals.scoring import compute_rating
from stock_signals._resonance import compute_timeframe_resonance

t = time.time()
df = fetch_kline(codes[0], '1d', 100)
print(f"Daily kline: {len(df)} rows, {time.time()-t:.1f}s")

t = time.time()
dfw = fetch_kline(codes[0], '1w', 50)
print(f"Weekly kline: {len(dfw)} rows, {time.time()-t:.1f}s")

t = time.time()
dfm = fetch_kline(codes[0], '1M', 30)
print(f"Monthly kline: {len(dfm)} rows, {time.time()-t:.1f}s")

ind = compute_indicators(df, codes[0], '1d')
rating = compute_rating(ind)
print(f"Rating: {rating['rating']} score={rating['score']}")
print(f"Total for 1 stock: ~{3 * (time.time()-t):.1f}s estimated")
