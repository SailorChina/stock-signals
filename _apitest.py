
import sys, time, json
sys.path.insert(0, r'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')

print("=== API Speed Test for Top 300 Stocks ===", flush=True)

# 1. Futu API
print("\n=== 1. Futu API (get_top_movers_rank) ===", flush=True)
try:
    from common import create_quote_context
    from futu import ScrMarket
    ctx = create_quote_context()
    for mkt, name in [(ScrMarket.US, 'US'), (ScrMarket.CN, 'A'), (ScrMarket.HK, 'HK')]:
        t0 = time.time()
        try:
            ret, result = ctx.get_top_movers_rank(mkt, count=int(300))
            t1 = time.time()
            if ret == 0 and result:
                all_count, data = result
                codes = data['security'].tolist()[:5] if 'security' in data.columns else []
                print(f"  {name}: {t1-t0:.2f}s, total={all_count}, codes={codes}", flush=True)
            else:
                print(f"  {name}: {t1-t0:.2f}s, error={result}", flush=True)
        except Exception as e:
            print(f"  {name}: ERROR {type(e).__name__}: {str(e)[:80]}", flush=True)
    ctx.close()
except Exception as e:
    print(f"  Futu init failed: {e}", flush=True)

# 2. akshare Sina spot
print("\n=== 2. akshare Sina spot ===", flush=True)
try:
    import akshare as ak
    for name, fn in [('A股', 'stock_zh_a_spot'), ('美股', 'stock_us_spot'), ('港股', 'stock_hk_spot')]:
        try:
            t0 = time.time()
            df = getattr(ak, fn)()
            t1 = time.time()
            print(f"  {name}: {t1-t0:.1f}s, {len(df)} stocks", flush=True)
        except Exception as e:
            print(f"  {name}: ERR {type(e).__name__}: {str(e)[:60]}", flush=True)
except Exception as e:
    print(f"  akshare failed: {e}", flush=True)

print("\nDONE")
