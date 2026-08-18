
import sys, time
sys.path.insert(0, r'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
sys.stdout.reconfigure(line_buffering=True)

print("=== API Test for Top 300 Stocks ===", flush=True)

# 1. Futu API test
print("\n=== 1. Futu API ===", flush=True)
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
                print(f"  {name}: {t1-t0:.2f}s total={all_count} codes={codes}", flush=True)
            else:
                print(f"  {name}: {t1-t0:.2f}s ret={ret} result={result}", flush=True)
        except Exception as e:
            print(f"  {name}: ERROR {type(e).__name__}: {str(e)[:80]}", flush=True)
    ctx.close()
except Exception as e:
    print(f"  Futu init failed: {e}", flush=True)

# 2. akshare Sina spot
print("\n=== 2. akshare Sina spot ===", flush=True)
try:
    import akshare as ak
    for name, fn in [('A股', 'stock_zh_a_spot'), ('美股', 'stock_us_spot')]:
        try:
            t0 = time.time()
            df = getattr(ak, fn)()
            t1 = time.time()
            cols = list(df.columns)[:6]
            top3 = df.nlargest(3, '涨跌幅')[['代码','名称','涨跌幅']].head(3).to_string() if '涨跌幅' in df.columns else 'no pct col'
            print(f"  {name}: {t1-t0:.1f}s, {len(df)} stocks, cols={cols}", flush=True)
            print(f"    Top 3: {top3}", flush=True)
        except Exception as e:
            print(f"  {name}: ERR {type(e).__name__}: {str(e)[:60]}", flush=True)
except Exception as e:
    print(f"  akshare failed: {e}", flush=True)

print("\nDONE")
