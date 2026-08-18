import akshare as ak, time

# Extract A-share codes from xueqiu hot follow
t = time.time()
df = ak.stock_hot_follow_xq()
# Clean column names
df.columns = ['code', 'name', 'heat', 'price']
# Filter to A-shares only (SH/SZ prefix)
a_codes = [c for c in df['code'] if c.startswith('SH') or c.startswith('SZ')]
print(f"Xueqiu A-share codes: {len(a_codes)} in {time.time()-t:.2f}s")
print("Sample:", a_codes[:10])

# Format as SH.600519
formatted = [f"{c[:2]}.{c[2:]}" for c in a_codes]
print("Formatted:", formatted[:10])
