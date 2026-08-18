
import py_compile
with open('stock_signals/scoring.py', 'r', encoding='utf-8') as f: sc = f.read()
old = "try:\n    if not _FUTU_AVAILABLE:\n        return {}\nexcept ImportError:\n    _FUTU_AVAILABLE = False\n    create_quote_context = None\n    check_ret = None\n    safe_close = None"
new = "try:\n    from common import create_quote_context, check_ret, safe_close\n    _FUTU_AVAILABLE = True\nexcept ImportError:\n    _FUTU_AVAILABLE = False\n    create_quote_context = None\n    check_ret = None\n    safe_close = None"
sc = sc.replace(old, new)
sc = sc.replace('        from common import create_quote_context, check_ret, safe_close\n        ctx = None\n        try:\n            ctx = _get_cap_ctx()\n            ret, data = ctx.get_capital_distribution', '        if not _FUTU_AVAILABLE:\n            return {}\n        ctx = None\n        try:\n            ctx = _get_cap_ctx()\n            ret, data = ctx.get_capital_distribution')
sc = sc.replace('        from common import create_quote_context, check_ret, safe_close\n        ctx = None\n        try:\n            ctx = _get_cap_ctx()\n            ret, data, _ = ctx.get_daily_short_volume', '        if not _FUTU_AVAILABLE:\n            return None\n        ctx = None\n        try:\n            ctx = _get_cap_ctx()\n            ret, data, _ = ctx.get_daily_short_volume')
with open('stock_signals/scoring.py', 'w', encoding='utf-8') as f: f.write(sc)
print('scoring.py fixed')
with open('stock_signals/indicators.py', 'r', encoding='utf-8') as f: ind = f.read()
ind = ind.replace('if df is not not None', 'if df is not None')
with open('stock_signals/indicators.py', 'w', encoding='utf-8') as f: f.write(ind)
print('indicators.py fixed')
for fname in ['stock_signals/indicators.py', 'stock_signals/scoring.py', 'stock_signals/screener.py']:
    try:
        py_compile.compile(fname, doraise=True)
        print(f'{fname}: OK')
    except py_compile.PyCompileError as e:
        print(f'{fname}: ERROR - {e}')
