
import sys, time
sys.path.insert(0, r'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
from common import create_quote_context
from futu import ScrMarket
ctx = create_quote_context()
for mkt, name in [(ScrMarket.US, 'US'), (ScrMarket.CN, 'A'), (ScrMarket.HK, 'HK')]:
    t0 = time.time()
    try:
        ret, result = ctx.get_top_movers_rank(mkt, count=300)
        t1 = time.time()
        if ret == 0 and result:
            all_count, data = result
            codes = data['security'].tolist()[:5] if 'security' in data.columns else []
            print(f'{name}: {t1-t0:.2f}s total={all_count} codes={codes}')
        else:
            print(f'{name}: {t1-t0:.2f}s error={result}')
    except Exception as e:
        print(f'{name}: ERROR {type(e).__name__}: {str(e)[:100]}')
ctx.close()
print('DONE')
