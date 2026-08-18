import akshare as ak, time

tests = [
    ('stock_hot_rank_em', lambda: ak.stock_hot_rank_em()),
    ('stock_hk_hot_rank_em', lambda: ak.stock_hk_hot_rank_em()),
    ('stock_hk_hot_rank_latest_em', lambda: ak.stock_hk_hot_rank_latest_em()),
    ('stock_hot_rank_detail_em', lambda: ak.stock_hot_rank_detail_em()),
    ('stock_hot_up_em', lambda: ak.stock_hot_up_em()),
    ('stock_hot_follow_xq', lambda: ak.stock_hot_follow_xq()),
]

for name, fn in tests:
    t = time.time()
    try:
        df = fn()
        print(f"{name}: time={time.time()-t:.2f}s, rows={len(df)}, cols={list(df.columns)}")
    except Exception as e:
        print(f"{name}: ERROR {e}")
