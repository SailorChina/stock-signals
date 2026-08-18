
import sys, time, os, inspect
sys.path.insert(0, r'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
from common import create_quote_context
from futu import ScrMarket

print("=== Futu Full Debug ===", flush=True)

# Find futu path
import futu
futu_path = os.path.dirname(futu.__file__)
print(f"Futu: {futu_path}", flush=True)

# Search source
for root, dirs, files in os.walk(futu_path):
    for fname in files:
        if fname.endswith('.py'):
            fp = os.path.join(root, fname)
            try:
                content = open(fp, 'r', encoding='utf-8', errors='ignore').read()
                if 'get_top_movers_rank' in content:
                    idx = content.find('def get_top_movers_rank')
                    end = content.find('\n    def ', idx+1)
                    print(f"\nSource in {fp} L{content[:idx].count(chr(10))+1}:", flush=True)
                    print(content[idx:end if end>0 else idx+2000], flush=True)
            except: pass

# Protobuf check
print("\n=== Protobuf ===", flush=True)
try:
    import futu.proto.openquotation_pb2 as pb2
    req = pb2.TopMoversRankReq()
    req.market = 1
    req.count = 10
    print(f"Fields: {[f.name for f in req.DESCRIPTOR.fields]}", flush=True)
    print(f"Values: market={req.market} count={req.count}", flush=True)
except Exception as e:
    print(f"ERR: {e}", flush=True)

# Alternative methods
ctx = create_quote_context()
alts = [m for m in dir(ctx) if 'top' in m.lower() or 'mover' in m.lower() or 'rank' in m.lower() or 'hot' in m.lower()]
print(f"\n=== Alt methods: {alts} ===", flush=True)

# Try get_stock_basicinfo for volume ranking
print("\n=== get_stock_basicinfo ===", flush=True)
for mkt, name in [(ScrMarket.US, "US"), (ScrMarket.CN, "A"), (ScrMarket.HK, "HK")]:
    t0 = time.time()
    try:
        ret, data = ctx.request_stock_basicinfo(mkt)
        t1 = time.time()
        print(f"  {name}: {t1-t0:.2f}s ret={ret}", flush=True)
        if ret == 0 and data is not None and not data.empty:
            print(f"    shape={data.shape} cols={list(data.columns)[:8]}", flush=True)
            if 'volume' in data.columns:
                top10 = data.nlargest(10, 'volume')[['code','volume']].head()
                print(f"    Top 3 vol:\n{top10.to_string()}", flush=True)
        else:
            print(f"    data={str(data)[:100]}", flush=True)
    except Exception as e:
        print(f"  {name}: ERR {type(e).__name__}: {str(e)[:80]}", flush=True)

ctx.close()
print("\nDONE")
