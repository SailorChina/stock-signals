import akshare as ak, time

# Test HK spot
t = time.time()
try:
    df = ak.stock_hk_spot_em()
    print(f"hk_spot_em: {time.time()-t:.2f}s, rows={len(df)}")
    print(list(df.columns)[:10])
except Exception as e:
    print(f"hk_spot_em ERROR: {str(e)[:100]}")

# Test HK famous
t = time.time()
try:
    df = ak.stock_hk_famous_spot_em()
    print(f"hk_famous: {time.time()-t:.2f}s, rows={len(df)}")
    print(list(df.columns)[:10])
except Exception as e:
    print(f"hk_famous ERROR: {str(e)[:100]}")

# Test HK main board
t = time.time()
try:
    df = ak.stock_hk_main_board_spot_em()
    print(f"hk_main: {time.time()-t:.2f}s, rows={len(df)}")
    print(list(df.columns)[:10])
except Exception as e:
    print(f"hk_main ERROR: {str(e)[:100]}")
