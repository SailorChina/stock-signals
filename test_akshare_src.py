import akshare as ak, time

# Test akshare functions that might use Sina source (not EastMoney)
tests = [
    ('stock_zh_a_spot', lambda: ak.stock_zh_a_spot()),
    ('stock_zh_a_spot_em', lambda: ak.stock_zh_a_spot_em()),
    ('stock_hk_spot', lambda: ak.stock_hk_spot()),
    ('stock_hk_spot_em', lambda: ak.stock_hk_spot_em()),
    ('stock_us_spot', lambda: ak.stock_us_spot()),
    ('stock_us_spot_em', lambda: ak.stock_us_spot_em()),
]
for name, fn in tests:
    t = time.time()
    try:
        df = fn()
        print(f"{name}: {time.time()-t:.2f}s, rows={len(df)}")
    except Exception as e:
        print(f"{name}: ERROR {str(e)[:80]}")
