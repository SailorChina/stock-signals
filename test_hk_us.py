import akshare as ak
funcs = [f for f in dir(ak) if 'hk' in f.lower() and ('hot' in f.lower() or 'rank' in f.lower() or 'spot' in f.lower() or 'list' in f.lower())]
print("HK funcs:", funcs)
