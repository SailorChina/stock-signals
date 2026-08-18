# -*- coding: utf-8 -*-
path = r'D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\screener.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the _write_pool_to_file function boundaries
start = -1
end = -1
for i, line in enumerate(lines):
    if line.strip().startswith('def _write_pool_to_file'):
        start = i
    if start != -1 and end == -1 and line.strip().startswith('def ') and i > start:
        end = i
        break

print(f'Function at lines {start+1}-{end}')

# Build replacement
new_lines = []
new_lines.append('def _write_pool_to_file(var_name: str, codes: List[str]):
')
new_lines.append('    """Write hot stock pool back to screener.py."""
')
new_lines.append('    import re as _re
')
new_lines.append('    pool_str = ", ".join(f\"{c}\" for c in codes)
')
new_lines.append("    pat = _re.escape(var_name) + r'\\s*=\\s*\\[([^\\]]*?)\\n\\s*\\]'
")
new_lines.append("    repl = var_name + ' = [\n' + '    ' + pool_str + ',\n]'
")
new_lines.append("    with open(path, 'r', encoding='utf-8') as f:
")
new_lines.append('        cnt = f.read()
')
new_lines.append('    cnt = _re.sub(pat, repl, cnt, count=1)
')
new_lines.append("    with open(path, 'w', encoding='utf-8') as f:
")
new_lines.append('        f.write(cnt)
')
new_lines.append('
')
new_lines.append('
')

result = lines[:start] + new_lines + lines[end:]
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(result)
print('Fixed')
