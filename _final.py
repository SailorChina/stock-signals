
import sys, time, json, http.client, urllib.request
sys.stdout.reconfigure(line_buffering=True)
sys.path.insert(0, r'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
from common import create_quote_context
from futu import ScrMarket

print("=== Futu Alternative Methods ===", flush=True)
ctx = create_quote_context()
for method in ['get_hot_list', 'get_period_change_rank', 'get_dividend_rank']:
    print(f"\n--- {method} ---", flush=True)
    for mkt, name in [(ScrMarket.US,'US'),(ScrMarket.CN,'A'),(ScrMarket.HK,'HK')]:
        t0=time.time()
        try:
            m = getattr(ctx, method)
            ret, result = m(mkt)
            t1=time.time()
            print(f"  {name}: {t1-t0:.2f}s ret={ret}", flush=True)
            if ret==0 and result is not None:
                if hasattr(result,'shape'): print(f"    shape={result.shape} cols={list(result.columns)[:6]}", flush=True)
                else: print(f"    {str(result)[:200]}", flush=True)
        except Exception as e:
            print(f"  {name}: ERR {type(e).__name__}: {str(e)[:80]}", flush=True)
ctx.close()

print("\n=== Sina HTTP Tests ===", flush=True)
for name, node in [('A股','hs_a'),('美股','all'),('港股','hsHKStocks')]:
    t0=time.time()
    try:
        conn=http.client.HTTPConnection('vip.stock.finance.sina.com.cn',timeout=10)
        conn.request('GET',f'/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=5&sort=changepercent&asc=0&node={node}&symbol=&_s_r_a=page',
            headers={'User-Agent':'Mozilla/5.0','Referer':'http://finance.sina.com.cn/stock/'})
        resp=conn.getresponse()
        data=resp.read().decode('gbk',errors='ignore')
        t1=time.time()
        print(f"{name}: {t1-t0:.2f}s status={resp.status} len={len(data)}", flush=True)
        if resp.status==200:
            items=json.loads(data)
            print(f"  {len(items)} stocks", flush=True)
            for it in items[:3]: print(f"  {it.get('symbol','?')} {it.get('name','?')} {it.get('changepercent','?')}%", flush=True)
        else: print(f"  Body: {data[:200]}", flush=True)
    except Exception as e:
        t1=time.time()
        print(f"{name}: {t1-t0:.2f}s ERR {type(e).__name__}: {str(e)[:80]}", flush=True)
print("\nDONE")
