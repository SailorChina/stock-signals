# -*- coding: utf-8 -*-
"""导出交易记录为JSON备份"""
import os, sqlite3, json
from datetime import datetime

DB_PATH = os.path.expanduser("~/.tech-signal-FUTU-skill/journal.db")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("SELECT * FROM recommendations ORDER BY scan_date DESC, id")
cols = [d[0] for d in cur.description]
rows = [dict(zip(cols, r)) for r in cur.fetchall()]
conn.close()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = os.path.join(OUTPUT_DIR, f"journal_backup_{timestamp}.json")

with open(backup_file, "w", encoding="utf-8") as f:
    json.dump({"exported_at": datetime.now().isoformat(), "records": rows}, f, ensure_ascii=False, indent=2)

print(f"备份完成: {len(rows)} 条记录 -> {backup_file}")

