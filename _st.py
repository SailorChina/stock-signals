
import urllib.request, json, time, sys, http.client
sys.stdout.reconfigure(line_buffering=True)
print("=== Sina Tests ===", flush=True)
for name, node in [('A股','hs_a'),('美股','all'),('港股','hsHKStocks')]:
    t0=time.time()
    try:
        conn=http.client.HTTPConnection('vip.stock.finance.sina.com.cn',timeout=10)
        conn.request('GET',f'/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=10&sort=changepercent&asc=0&node={node}&symbol=&_s_r_a=page',
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
print("DONE")
