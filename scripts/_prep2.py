path = r'C:\Users\sailor\.codex\skills\stock-signals\scripts\indicators.py'
lines = open(path, encoding='utf-8').readlines()
# Remove last line if it's a stray @dataclass
if lines and lines[-1].strip().startswith('@dataclass'):
    lines = lines[:-1]
open(path, 'w', encoding='utf-8').writelines(lines)
print(f'Fixed, now {len(lines)} lines')
