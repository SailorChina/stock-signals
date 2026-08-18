
import os, time
for k in list(os.environ.keys()):
    if 'proxy' in k.lower(): os.environ.pop(k, None)
os.environ['no_proxy'] = '*'

import yfinance as yf

print('=== yfinance A-share ===')
try:
    t0 = time.time()
    tickers = ['600519.SS', '000001.SZ', '600036.SH']
    for sym in tickers:
        t1 = time.time()
        try:
            stock = yf.Ticker(sym)
            hist = stock.history(period='5d')
            print(sym, ':', len(hist), 'rows,', round(time.time()-t1,2), 's, last_close:', hist['Close'].iloc[-1] if len(hist) > 0 else 'N/A')
        except Exception as e:
            print(sym, ': ERROR', str(e)[:80])
    print('Total:', round(time.time()-t0,2), 's')
except Exception as e:
    print('Error:', e)

print()
print('=== yfinance HK ===')
try:
    t0 = time.time()
    tickers = ['0700.HK', '9988.HK', '0001.HK', '2382.HK', '3690.HK']
    for sym in tickers:
        t1 = time.time()
        try:
            stock = yf.Ticker(sym)
            hist = stock.history(period='5d')
            print(sym, ':', len(hist), 'rows,', round(time.time()-t1,2), 's, last_close:', hist['Close'].iloc[-1] if len(hist) > 0 else 'N/A')
        except Exception as e:
            print(sym, ': ERROR', str(e)[:80])
    print('Total:', round(time.time()-t0,2), 's')
except Exception as e:
    print('Error:', e)

print()
print('=== yfinance US ===')
try:
    t0 = time.time()
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
    for sym in tickers:
        t1 = time.time()
        try:
            stock = yf.Ticker(sym)
            hist = stock.history(period='5d')
            print(sym, ':', len(hist), 'rows,', round(time.time()-t1,2), 's, last_close:', hist['Close'].iloc[-1] if len(hist) > 0 else 'N/A')
        except Exception as e:
            print(sym, ': ERROR', str(e)[:80])
    print('Total:', round(time.time()-t0,2), 's')
except Exception as e:
    print('Error:', e)
