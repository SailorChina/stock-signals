import os
# First, remove duplicate class in indicators.py (lines 348+)
path = r'C:\\Users\\sailor\\.codex\\skills\\stock-signals\\scripts\\indicators.py'
lines = open(path, encoding='utf-8').readlines()
# Find the second 'class Indicators' and remove everything from there
cut_at = None
for i, l in enumerate(lines):
    if i > 100 and l.strip().startswith('class Indicators:'):
        cut_at = i
        break
if cut_at:
    lines = lines[:cut_at]
    open(path, 'w', encoding='utf-8').writelines(lines)
    print(f'Removed duplicate at line {cut_at+1}, now {len(lines)} lines')
else:
    print('No duplicate found, total lines:', len(lines))
