import sys
path = r'C:\Users\sailor\Desktop\富途牛牛量化\pyproject.toml'
with open(path, 'r') as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if 'streamlit>=1.30' in line:
        lines[i] = line.rstrip() + ',\n    \"plotly>=5.0\",\n'
        break
with open(path, 'w') as f:
    f.writelines(lines)
print('pyproject.toml updated')
