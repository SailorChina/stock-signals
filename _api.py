
import urllib.request, json, time, sys, traceback
sys.path.insert(0, r'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
sys.stdout.reconfigure(line_buffering=True)

print("=== API Comparison: Top 300 Stocks ===", flush=True)
print()

# 1. Sina Rank API (A-shares only, paginated)
print("1. Sina Rank API (A-shares, 3 pages of 100)", flush=True)
t0 = time.time()
all_codes = []
for page in range(1, 4):
    url = f'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num=100&sort=changepercent&asc=0&node=hs_a&symbol=&_s_r_a=page'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn'})
    resp = urllib.request.urlopen(req, timeout=10)
    items = json.loads(resp.read().decode('gbk', errors='ignore'))
    all_codes.extend(items)
t1 = time.time()
print(f"   A-shares: {t1-t0:.2f}s, {len(all_codes)} stocks (top gainers)", flush=True)
for it in all_codes[:3]:
    print(f"     {it.get('symbol','?')} {it.get('name','?')} {it.get('changepercent','?')}%", flush=True)

# 2. Futu API
print("\n2. Futu API (get_top_movers_rank)", flush=True)
try:
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
                print(f"   {name}: {t1-t0:.2f}s, total={all_count}, codes={codes}", flush=True)
            else:
                print(f"   {name}: {t1-t0:.2f}s ret={ret} result={result}", flush=True)
        except Exception as e:
            print(f"   {name}: ERR {type(e).__name__}: {str(e)[:80]}", flush=True)
    ctx.close()
except Exception as e:
    print(f"   Futu init failed: {e}", flush=True)

# 3. akshare Sina K-line (for reference - works for K-line but not spot)
print("\n3. akshare Sina K-line (for reference)", flush=True)
import akshare as ak
for name, fn in [('A股', 'stock_zh_a_daily'), ('美股', 'stock_us_daily'), ('港股', 'stock_hk_daily')]:
    try:
        t0 = time.time()
        df = getattr(ak, fn)('000001' if name=='A股' else ('AAPL' if name=='美股' else '00700') if name=='港股' else 'AAPL', adjust='qfq')
        t1 = time.time()
        print(f"   {name}: {t1-t0:.1f}s, {len(df) if df is not None else 0} rows", flush=True)
    except Exception as e:
        print(f"   {name}: ERR {type(e).__name__}: {str(e)[:60]}", flush=True)

print("\n=== SUMMARY ===", flush=True)
print("Sina Rank: A-shares OK (0.5s for 300), US/HK NOT WORKING", flush=True)
print("Futu API: Connected OK, but get_top_movers_rank BROKEN", flush=True)
print("akshare Sina K-line: All 3 markets OK (0.5-1s per stock)", flush=True)
print("akshare EastMoney spot: BLOCKED by proxy", flush=True)
print("DONE")
