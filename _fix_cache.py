
import re
path = 'D:/Backup/Documents/ChatGPT/AI/stock-signals/stock_signals/indicators.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find fetch_kline and add cache_key
old = 'def fetch_kline(code, ktype="1d", num=300):\n    parts = code.split'
new = 'def fetch_kline(code, ktype="1d", num=300):\n    cache_key = f"{code}_{num}"\n    if cache_key in _kline_cache:\n        return _kline_cache[cache_key]\n    parts = code.split'
if old in content:
    content = content.replace(old, new)
    print('Fixed with old pattern')
else:
    # Try line by line
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip() == 'def fetch_kline(code, ktype="1d", num=300):':
            lines.insert(i+1, '    cache_key = f"{code}_{num}"')
            lines.insert(i+2, '    if cache_key in _kline_cache:')
            lines.insert(i+3, '        return _kline_cache[cache_key]')
            content = '\n'.join(lines)
            print(f'Fixed at line {i+1}')
            break
    else:
        print('NOT FOUND')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
