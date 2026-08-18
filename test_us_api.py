import akshare as ak
funcs = [f for f in dir(ak) if 'us' in f.lower()]
print('US funcs:', funcs[:30])
