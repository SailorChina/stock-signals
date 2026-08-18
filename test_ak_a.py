import akshare as ak, time
t = time.time()
try:
    df = ak.stock_zh_a_spot()
    print(f"akshare A-spot: rows={len(df)}, time={time.time()-t:.2f}s")
    print("columns:", df.columns.tolist())
except Exception as e:
    print(f"akshare A-spot ERROR: {e}")
