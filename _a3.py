import time
from stock_signals.screener import scan_parallel
print("START")
t0=time.time()
r=scan_parallel(markets=["A"],output_json=True)
t1=time.time()
print("A:" + str(round(t1-t0,1)) + "s")
print("analyzed:" + str(r["summary"]["total_analyzed"]) + " picks:" + str(len(r["picks"]["A"])))
