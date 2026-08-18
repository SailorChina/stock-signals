import akshare as ak, time

# Test US spot
t = time.time()
try:
    df = ak.stock_us_spot_em()
    print(f"us_spot_em: {time.time()-t:.2f}s, rows={len(df)}")
    print(list(df.columns))
except Exception as e:
    print(f"us_spot_em ERROR: {e}")

# Test US famous
t = time.time()
try:
    df2 = ak.stock_us_famous_spot_em()
    print(f"us_famous: {time.time()-t:.2f}s, rows={len(df2)}")
    print(list(df2.columns))
except Exception as e:
    print(f"us_famous ERROR: {e}")
