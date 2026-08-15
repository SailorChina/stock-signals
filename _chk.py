import sys, codecs
sys.stdout.reconfigure(encoding="utf-8")
path = r"D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\cli.py"
with codecs.open(path, "r", "utf-8") as f:
    content = f.read()
lines = content.split(chr(10))
for i in range(136, 142):
    print(f"L{i+1}: {repr(lines[i])}")
