
import sys, time, urllib.request, json
sys.stdout.reconfigure(line_buffering=True)

print("=== API Speed Test for Top 300 Stocks ===\n", flush=True)

# 1. Futu API
print("=== 1. Futu API ===", flush=True)
try:
    sys.path.insert(0, r'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
    from common import create_quote_context
    from futu import ScrMarket
    ctx = create_quote_context()
    for mkt, name in [(ScrMarket.US, 'US'), (ScrMarket.CN, 'A'), (ScrMarket.HK, 'HK')]:
        t0 = time.time()
        try:
            ret, result = ctx.get_top_movers_rank(mkt)
            t1 = time.time()
            if ret == 0 and result:
                all_count, data = result
                codes = data['security'].tolist()[:5] if 'security' in data.columns else []
                print(f"  {name}: {t1-t0:.2f}s total={all_count} codes={codes}", flush=True)
            else:
                print(f"  {name}: {t1-t0:.2f}s ret={ret} result={result}", flush=True)
        except Exception as e:
            print(f"  {name}: ERROR {type(e).__name__}: {str(e)[:80]}", flush=True)
    ctx.close()
except Exception as e:
    print(f"  Futu init failed: {e}", flush=True)

# 2. Sina rank API (direct HTTP)
print("\n=== 2. Sina Rank API ===", flush=True)
for name, url in [
    ('A股涨幅榜', 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=300&sort=changepercent&asc=0&node=hs_a&symbol=&_s_r_a=page'),
    ('美股涨幅榜', 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=300&sort=changepercent&asc=0&node=all&symbol=&_s_r_a=page'),
    ('港股涨幅榜', 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=300&sort=changepercent&asc=0&node=hsHKStocks&symbol=&_s_r_a=page'),
]:
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('gbk', errors='ignore')
        t1 = time.time()
        items = json.loads(data)
        print(f"  {name}: {t1-t0:.2f}s, {len(items)} stocks", flush=True)
        for it in items[:3]:
            print(f"    {it.get('symbol','?')} {it.get('name','?')} {it.get('changepercent','?')}%", flush=True)
    except Exception as e:
        print(f"  {name}: ERR {type(e).__name__}: {str(e)[:80]}", flush=True)

# 3. Sina stock quote API (for real-time quotes)
print("\n=== 3. Sina Quote API ===", flush=True)
# Get A-share top gainers via sina real-time quote
try:
    # Sina real-time quote for top A-shares
    url = 'http://hq.sinajs.cn/list=' + ','.join([f'sh{str(i).zfill(6)}' for i in range(100, 110)])
    t0 = time.time()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode('gbk', errors='ignore')
    t1 = time.time()
    print(f"  Sina quote test: {t1-t0:.2f}s, data={len(data)} bytes", flush=True)
    print(f"  Preview: {data[:200]}", flush=True)
except Exception as e:
    print(f"  Sina quote: ERR {type(e).__name__}: {str(e)[:80]}", flush=True)

print("\nDONE")
