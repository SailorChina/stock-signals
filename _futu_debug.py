
import sys, time, json
sys.path.insert(0, r'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
from common import create_quote_context, check_ret
from futu import ScrMarket

print("=== Futu get_top_movers_rank Debug ===", flush=True)

ctx = create_quote_context()

# Test different parameter combinations
tests = [
    ("default", {}),
    ("count=10", {"count": 10}),
    ("count=10,sort_dir=1", {"count": 10, "sort_dir": 1}),
    ("count=int(300)", {"count": int(300)}),
    ("count=300,sort_dir=1", {"count": 300, "sort_dir": 1}),
]

for mkt, mkt_name in [(ScrMarket.US, "US"), (ScrMarket.CN, "A"), (ScrMarket.HK, "HK")]:
    print(f"\n=== {mkt_name} ===", flush=True)
    for name, kwargs in tests:
        t0 = time.time()
        try:
            ret, result = ctx.get_top_movers_rank(mkt, **kwargs)
            t1 = time.time()
            if ret == 0 and result:
                all_count, data = result
                codes = data["security"].tolist()[:5] if "security" in data.columns else []
                print(f"  {name}: {t1-t0:.2f}s total={all_count} codes={codes}", flush=True)
            else:
                print(f"  {name}: {t1-t0:.2f}s ret={ret} result={result}", flush=True)
        except Exception as e:
            t1 = time.time()
            print(f"  {name}: {t1-t0:.2f}s ERR {type(e).__name__}: {str(e)[:80]}", flush=True)

# Also check the method signature
import inspect
sig = inspect.signature(ctx.get_top_movers_rank)
print(f"\nSignature: get_top_movers_rank{sig}", flush=True)

ctx.close()
print("\nDONE")
