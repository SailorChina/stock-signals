
import sys
sys.path.insert(0, r'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
from futu import ScrMarket
import inspect
from common import create_quote_context
ctx = create_quote_context()
# Check method signature
sig = inspect.signature(ctx.get_top_movers_rank)
print('get_top_movers_rank signature:', sig)
# Try with different params
import time
t0 = time.time()
try:
    ret, result = ctx.get_top_movers_rank(ScrMarket.US, count=300)
    t1 = time.time()
    print(f'US: {t1-t0:.2f}s ret={ret} result={result}')
except Exception as e:
    print(f'US ERROR: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
ctx.close()
