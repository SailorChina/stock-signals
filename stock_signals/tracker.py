# -*- coding: utf-8 -*-
import sqlite3, os
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.expanduser(chr(126)), '.tech-signal-FUTU-skill', 'journal.db')

def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_conn()
    c = conn.cursor()
    cols = 'id INTEGER PRIMARY KEY AUTOINCREMENT, '
    cols += 'scan_date TEXT NOT NULL, symbol TEXT NOT NULL, '
    cols += 'rating TEXT, score REAL, resonance TEXT, trend_phase TEXT, '
    cols += 'current_price REAL, entry_price REAL, entry_type TEXT, '
    cols += 'stop_loss REAL, target1 REAL, target2 REAL, '
    cols += 'rr_ratio REAL, position_pct REAL, hold_period TEXT, '
    cols += 'buy_strategy TEXT, sell_strategy TEXT, sector TEXT, note TEXT, '
    cols += 'outcome TEXT DEFAULT NULL, outcome_price REAL DEFAULT NULL, '
    cols += 'outcome_pnl_pct REAL DEFAULT NULL, '
    cols += 'created_at TEXT DEFAULT CURRENT_TIMESTAMP, '
    cols += 'updated_at TEXT DEFAULT CURRENT_TIMESTAMP'
    c.execute('CREATE TABLE IF NOT EXISTS recommendations (' + cols + ')')
    c.execute('CREATE INDEX IF NOT EXISTS idx_date ON recommendations(scan_date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON recommendations(symbol)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_outcome ON recommendations(outcome)')
    conn.commit()
    conn.close()

def save_scan(scan_date, results, category='recommended'):
    conn = _get_conn()
    c = conn.cursor()
    for r in results:
        c.execute(
            'INSERT INTO recommendations '
            '(scan_date, symbol, rating, score, resonance, trend_phase, '
            'current_price, entry_price, entry_type, stop_loss, target1, target2, '
            'rr_ratio, position_pct, hold_period, buy_strategy, sell_strategy, '
            'sector, note, outcome) '
            'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (scan_date, r.get('symbol'), r.get('rating'), r.get('score'),
             r.get('resonance'), r.get('trend_phase'),
             r.get('current_price'), r.get('entry_price'), r.get('entry_type'),
             r.get('stop_loss'), r.get('target1'), r.get('target2'),
             r.get('rr_ratio'), r.get('position_pct'), r.get('hold_period'),
             r.get('buy_strategy'), r.get('sell_strategy'),
             r.get('sector'), r.get('note'), category)
        )
    conn.commit()
    conn.close()
    return len(results)

def get_recommendations(date=None, symbol=None, outcome=None):
    conn = _get_conn()
    c = conn.cursor()
    where, params = [], []
    if date: where.append('scan_date=?'); params.append(date)
    if symbol: where.append('symbol=?'); params.append(symbol)
    if outcome: where.append('outcome=?'); params.append(outcome)
    sql = 'SELECT * FROM recommendations'
    if where: sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY scan_date DESC, score DESC'
    c.execute(sql, params)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_dates():
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT DISTINCT scan_date FROM recommendations ORDER BY scan_date DESC')
    dates = [r[0] for r in c.fetchall()]; conn.close(); return dates

def update_outcome(rec_id, outcome, outcome_price=None, outcome_pnl_pct=None):
    conn = _get_conn(); c = conn.cursor()
    c.execute(
        'UPDATE recommendations SET outcome=?,outcome_price=?,outcome_pnl_pct=?,updated_at=CURRENT_TIMESTAMP WHERE id=?',
        (outcome, outcome_price, outcome_pnl_pct, rec_id)
    )
    conn.commit(); conn.close()

def get_stats():
    conn = _get_conn(); c = conn.cursor(); stats = {}
    c.execute('SELECT COUNT(*) FROM recommendations'); stats['total'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM recommendations WHERE outcome IS NOT NULL'); stats['tracked'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM recommendations WHERE outcome=?', ('win',)); stats['wins'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM recommendations WHERE outcome=?', ('loss',)); stats['losses'] = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM recommendations WHERE outcome=?', ('hold',)); stats['holds'] = c.fetchone()[0]
    if stats['tracked'] > 0:
        c.execute('SELECT AVG(outcome_pnl_pct) FROM recommendations WHERE outcome_pnl_pct IS NOT NULL')
        avg = c.fetchone()[0]
        stats['avg_pnl_pct'] = round(avg, 2) if avg else None
        stats['win_rate'] = round(stats['wins'] / stats['tracked'] * 100, 1)
    else:
        stats['avg_pnl_pct'] = None; stats['win_rate'] = None
    c.execute('SELECT scan_date,COUNT(*) FROM recommendations GROUP BY scan_date ORDER BY scan_date DESC LIMIT 10')
    stats['recent_days'] = [(r[0], r[1]) for r in c.fetchall()]
    c.execute('SELECT symbol,COUNT(*) as cnt,AVG(score) as avg_score FROM recommendations GROUP BY symbol ORDER BY cnt DESC LIMIT 10')
    stats['top_stocks'] = [(r[0], r[1], round(r[2], 1)) for r in c.fetchall()]
    conn.close(); return stats

def export_csv(filepath):
    import csv
    conn = _get_conn(); c = conn.cursor()
    c.execute('SELECT * FROM recommendations ORDER BY scan_date DESC')
    rows = c.fetchall(); conn.close()
    if not rows: return None
    keys = rows[0].keys()
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for row in rows: w.writerow(dict(row))
    return filepath
