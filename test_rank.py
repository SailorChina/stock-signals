import akshare as ak, time, json, urllib.request

print("=== AKSHARE HOT RANK ===")
t = time.time()
df = ak.stock_hot_rank_em()
print(f"hot_rank_em: {time.time()-t:.2f}s, rows={len(df)}")
print("cols:", list(df.columns))
print(df.head(3).to_string())

t = time.time()
df2 = ak.stock_hk_hot_rank_em()
print(f"hk_hot_rank: {time.time()-t:.2f}s, rows={len(df2)}")
print("cols:", list(df2.columns))
print(df2.head(3).to_string())

print("")
print("=== SINA RANK PAGINATED ===")
t = time.time()
all_items = []
for p in range(1, 5):
    url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={p}&num=100&sort=changepercent&asc=0&node=hs_a'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=5)
    items = json.loads(resp.read().decode())
    all_items.extend(items)
    if len(items) < 100:
        break
print(f"sina A-rank: {time.time()-t:.2f}s, total={len(all_items)}")
if all_items:
    print("first 3:", [(i.get('symbol'), i.get('name'), i.get('changepercent')) for i in all_items[:3]])
