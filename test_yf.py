import yfinance as yf, time
t = time.time()
try:
    tk = yf.Ticker("NVDA")
    h = tk.history(period="5d")
    print(f"yf NVDA: time={time.time()-t:.2f}s, rows={len(h)}")
except Exception as e:
    print(f"yf ERROR: {e}")
