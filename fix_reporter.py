
path = r'D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\reporter.py'
with open(path, 'r', encoding='utf-8') as f:
    txt = f.read()
helper = '''
def _to_obj(d):
    if hasattr(d, 'code'): return d
    class _O: pass
    o = _O()
    for k, v in d.items(): setattr(o, k, v)
    return o

'''
marker = 'RATING_CN = {'
idx = txt.index(marker)
txt = txt[:idx] + helper + txt[idx:]
txt = txt.replace(
    'def _print_stock(r, index: int, watch: bool = False):',
    'def _print_stock(r, index: int, watch: bool = False):\n    r = _to_obj(r)'
)
with open(path, 'w', encoding='utf-8') as f:
    f.write(txt)
print('Fixed reporter.py')
