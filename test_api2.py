import akshare as ak, time

# Test A-share hot rank with more rows
t = time.time()
df = ak.stock_hot_rank_em()
print(f"hot_rank_em: {time.time()-t:.2f}s, rows={len(df)}")
print(df.head(5).to_string())

# Test HK hot rank with more rows
t = time.time()
df2 = ak.stock_hk_hot_rank_em()
print(f"\nhk_hot_rank_em: {time.time()-t:.2f}s, rows={len(df2)}")
print(df2.head(5).to_string())

# Test detail
t = time.time()
df3 = ak.stock_hot_rank_detail_em()
print(f"\nhot_detail_em: {time.time()-t:.2f}s, rows={len(df3)}")
print(df3.head(3).to_string())

# Check US-related functions more carefully
import akshare as ak2
us_funcs2 = [f for f in dir(ak2) if 'stock_us' in f.lower() or 'us_stock' in f.lower()]
print(f"\nUS stock funcs: {us_funcs2}")
