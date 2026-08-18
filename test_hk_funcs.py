import akshare as ak, time

hk_funcs = [
    'stock_hk_hot_rank_em', 'stock_hk_hot_rank_latest_em',
    'stock_hk_hot_rank_detail_em', 'stock_hk_hot_rank_detail_realtime_em',
    'stock_hk_index_spot_em', 'stock_hk_index_spot_sina',
    'stock_hk_main_board_spot_em', 'stock_hk_spot', 'stock_hk_spot_em',
    'stock_hk_famous_spot_em',
]
for fn_name in hk_funcs:
    t = time.time()
    try:
        fn = getattr(ak, fn_name)
        df = fn()
        print(f"{fn_name}: {time.time()-t:.2f}s, rows={len(df)}")
    except Exception as e:
        print(f"{fn_name}: ERR {str(e)[:60]}")
