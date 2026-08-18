# -*- coding: utf-8 -*-
path = r'D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\screener.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the broken _write_pool_to_file function
start = -1
end = -1
for i, line in enumerate(lines):
    if line.startswith('def _write_pool_to_file'):
        start = i
    if start != -1 and end == -1 and line.startswith('def ') and i > start:
        end = i
        break

if start == -1:
    print('ERROR: function not found')
    exit(1)

print(f'Found _write_pool_to_file at lines {start+1}-{end}')

# Replace with fixed version
new_func = [
    'def _write_pool_to_file(var_name: str, codes: List[str]):\n',
    '    """Write hot stock pool back to screener.py."""\n',
    '    import re as _re\n',
    '    pool_str = ", ".join(f'"{c}"' for c in codes)\n',
    "    pat = _re.escape(var_name) + r'\\s*=\\s*\\[([^\\]]*?)\\n\\s*\\]'\n",
    "    repl = var_name + ' = [\n' + '    ' + pool_str + ',\n]'\n",
    "    with open(path, 'r', encoding='utf-8') as f:\n",
    '        cnt = f.read()\n',
    '    cnt = _re.sub(pat, repl, cnt, count=1)\n',
    "    with open(path, 'w', encoding='utf-8') as f:\n",
    '        f.write(cnt)\n',
    '\n',
    '\n',
]

result = lines[:start] + new_func + lines[end:]
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(result)
print('Fixed')
