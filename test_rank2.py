import akshare as ak, time, sys

print("TEST 1: stock_hot_rank_em", flush=True)
t = time.time()
try:
    df = ak.stock_hot_rank_em()
    print(f"OK: {time.time()-t:.2f}s, rows={len(df)}", flush=True)
    print(list(df.columns), flush=True)
    print(df.head(3).to_string(), flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback; traceback.print_exc()

print("TEST 2: stock_hk_hot_rank_em", flush=True)
t = time.time()
try:
    df2 = ak.stock_hk_hot_rank_em()
    print(f"OK: {time.time()-t:.2f}s, rows={len(df2)}", flush=True)
    print(list(df2.columns), flush=True)
    print(df2.head(3).to_string(), flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback; traceback.print_exc()
