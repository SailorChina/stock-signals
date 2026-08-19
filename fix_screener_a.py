
path = r'D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\screener_a.py'
with open(path, 'r', encoding='utf-8') as f:
    txt = f.read()
# Also fix: _analyze_one_a returns AScanResult object, but we convert to dict.
# Make sure 'reasons' is always a list in the dict
old = '"reasons": p.reasons, "holding_period": p.holding_period, "last_close": p.last_close} for p in final_picks]'
new = '"reasons": list(p.reasons) if p.reasons else [], "holding_period": p.holding_period, "last_close": p.last_close} for p in final_picks]'
txt = txt.replace(old, new)
with open(path, 'w', encoding='utf-8') as f:
    f.write(txt)
print('screener_a.py verified')
