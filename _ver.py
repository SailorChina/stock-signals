# Update version to 2.4.0
import os

# __init__.py
path = r"D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\__init__.py"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("v2.3.3", "v2.4.0").replace('"2.3.3"', '"2.4.0"')
with open(path, "w", encoding="utf-8") as f:
    f.write(c)
print("__init__.py:", c.split("\n")[1])

# pyproject.toml
path = r"D:\Backup\Documents\ChatGPT\AI\stock-signals\pyproject.toml"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace('version = "2.3.3"', 'version = "2.4.0"')
with open(path, "w", encoding="utf-8") as f:
    f.write(c)
print("pyproject.toml fixed")

# cli.py
path = r"D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\cli.py"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("v2.3.3", "v2.4.0")
with open(path, "w", encoding="utf-8") as f:
    f.write(c)
print("cli.py fixed")
