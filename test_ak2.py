import akshare as ak, time

tests = [
    ('stock_hot_up_em', lambda: ak.stock_hot_up_em()),
    ('stock_hot_follow_xq', lambda: ak.stock_hot_follow_xq()),
    ('stock_hot_rank_detail_em', lambda: ak.stock_hot_rank_detail_em()),
    ('stock_hot_keyword_em', lambda: ak.stock_hot_keyword_em()),
]
for name, fn in tests:
    t = time.time()
    try:
        df = fn()
        print(f"{name}: {time.time()-t:.2f}s, rows={len(df)}")
        print(f"  cols: {list(df.columns)[:5]}")
        if len(df) > 0:
            print(f"  first: {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"{name}: ERROR {str(e)[:100]}")
