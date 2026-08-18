
import sys; sys.path.insert(0, '.')
from stock_signals.indicators import fetch_kline
for n, c in [('A','SH.600519'),('HK','HK.00700'),('US','US.AAPL')]:
    df = fetch_kline(c, '1d', 10)
    print(f'{n}: {len(df)} rows')
