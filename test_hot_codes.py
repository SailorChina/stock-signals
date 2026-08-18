import akshare as ak, time

# Get unique codes from detail
t = time.time()
df = ak.stock_hot_rank_detail_em()
codes = df['证券代码'].unique().tolist()
print(f"detail_em unique codes: {len(codes)}")
print("Sample:", codes[:15])

# Get xueqiu hot stocks
t = time.time()
df2 = ak.stock_hot_follow_xq()
print(f"\nfollow_xq: {time.time()-t:.2f}s, rows={len(df2)}")
# Convert columns
col_map = {}
for c in df2.columns:
    for k, v in {'股票名称': 'name', '股票代码': 'code', '热度': 'heat', '最新价': 'price'}.items():
        if k in c:
            col_map[c] = v
print("Cols mapped:", col_map)
if col_map:
    df2 = df2.rename(columns=col_map)
    print(df2.head(3).to_string())
