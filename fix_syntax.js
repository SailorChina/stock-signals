
import re

# Fix scoring.py
with open('D:/Backup/Documents/ChatGPT/AI/stock-signals/stock_signals/scoring.py', 'r', encoding='utf-8') as f:
    sc = f.read()

# Fix the corrupted top-level try/except
old = """try:
    if not _FUTU_AVAILABLE:
        return {}
except ImportError:
    _FUTU_AVAILABLE = False
    create_quote_context = None
    check_ret = None
    safe_close = None"""
new = """try:
    from common import create_quote_context, check_ret, safe_close
    _FUTU_AVAILABLE = True
except ImportError:
    _FUTU_AVAILABLE = False
    create_quote_context = None
    check_ret = None
    safe_close = None"""
sc = sc.replace(old, new)

# Fix internal imports in get_capital_data and get_short_data
sc = sc.replace(
    '        from common import create_quote_context, check_ret, safe_close\n        ctx = None',
    '        if not _FUTU_AVAILABLE:\n            return {}\n        ctx = None'
)
sc = sc.replace(
    '        from common import create_quote_context, check_ret, safe_close\n        ctx = None',
    '        if not _FUTU_AVAILABLE:\n            return None\n        ctx = None'
)

with open('D:/Backup/Documents/ChatGPT/AI/stock-signals/stock_signals/scoring.py', 'w', encoding='utf-8') as f:
    f.write(sc)
print('scoring.py fixed')

# Fix indicators.py double "not"
with open('D:/Backup/Documents/ChatGPT/AI/stock-signals/stock_signals/indicators.py', 'r', encoding='utf-8') as f:
    ind = f.read()
ind = ind.replace('if df is not not None', 'if df is not None')
with open('D:/Backup/Documents/ChatGPT/AI/stock-signals/stock_signals/indicators.py', 'w', encoding='utf-8') as f:
    f.write(ind)
print('indicators.py fixed')

# Verify syntax
import py_compile
for f in ['stock_signals/indicators.py', 'stock_signals/scoring.py', 'stock_signals/screener.py']:
    try:
        py_compile.compile(f, doraise=True)
        print(f'{f}: syntax OK')
    except py_compile.PyCompileError as e:
        print(f'{f}: SYNTAX ERROR - {e}')
