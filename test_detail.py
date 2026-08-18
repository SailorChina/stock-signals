import akshare as ak, time
t = time.time()
df = ak.stock_hot_rank_detail_em()
print(f"detail_em: {time.time()-t:.2f}s, rows={len(df)}")
print("cols:", list(df.columns))
print(df.head(5).to_string())
