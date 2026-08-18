
import sys, time
sys.path.insert(0, r'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
from common import create_quote_context
from futu import ScrMarket
import inspect
ctx = create_quote_context()
print("=== get_hot_list ===", flush=True)
for mkt, name in [(ScrMarket.US,'US'),(ScrMarket.CN,'A'),(ScrMarket.HK,'HK')]:
    t0=time.time()
    try:
        ret, result = ctx.get_hot_list(mkt)
        t1=time.time()
        print(f"  {name}: {t1-t0:.2f}s ret={ret}", flush=True)
        if ret==0: print(f"    {str(result)[:200]}", flush=True)
    except Exception as e:
        print(f"  {name}: ERR {type(e).__name__}: {str(e)[:80]}", flush=True)
print("\n=== get_period_change_rank ===", flush=True)
for mkt, name in [(ScrMarket.US,'US'),(ScrMarket.CN,'A'),(ScrMarket.HK,'HK')]:
    t0=time.time()
    try:
        ret, result = ctx.get_period_change_rank(mkt)
        t1=time.time()
        print(f"  {name}: {t1-t0:.2f}s ret={ret}", flush=True)
        if ret==0 and hasattr(result,'shape'): print(f"    shape={result.shape} cols={list(result.columns)[:6]}", flush=True)
    except Exception as e:
        print(f"  {name}: ERR {type(e).__name__}: {str(e)[:80]}", flush=True)
ctx.close()
print("\nDONE")
