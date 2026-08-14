with open(r"C:\Users\sailor\.codex\skills\stock-signals\scripts\analyze_signals.py", "r", encoding="utf-8") as f:
    content = f.read()

lines = content.split("\n")
# Find line numbers for key markers
for i, l in enumerate(lines):
    if "compute_timeframe_resonance" in l and "result[" not in l:
        print(f"Line {i+1}: resonance call")
    if "result = {" in l:
        print(f"Line {i+1}: result dict start")
    if "result[" in l and "resonance" in l:
        print(f"Line {i+1}: {l.strip()[:60]}")
