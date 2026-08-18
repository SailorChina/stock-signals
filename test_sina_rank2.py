import urllib.request, time, json

# Test Sina ranking with different page sizes
print("=== SINA RANK PAGESIZES ===")
for num in [30, 50, 100, 200]:
    t = time.time()
    try:
        url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num={num}&sort=changepercent&asc=0&node=hs_a'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        items = json.loads(resp.read().decode())
        print(f"num={num}: {time.time()-t:.2f}s, got={len(items)} items")
    except Exception as e:
        print(f"num={num}: ERROR {str(e)[:80]}")

# Test how many pages of A-share data we can get
print("")
print("=== SINA A-RANK PAGES ===")
all_items = []
t = time.time()
for p in range(1, 11):
    url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={p}&num=100&sort=changepercent&asc=0&node=hs_a'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        items = json.loads(resp.read().decode())
        all_items.extend(items)
        print(f"page {p}: got {len(items)} items, total={len(all_items)}")
        if len(items) < 100:
            break
    except Exception as e:
        print(f"page {p}: ERROR {str(e)[:80]}")
        break
print(f"Total: {len(all_items)} items in {time.time()-t:.2f}s")
if all_items:
    print("First 3 symbols:", [i.get('symbol') for i in all_items[:3]])
