# -*- coding: utf-8 -*-
import json, os, subprocess, sys, shutil
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
DATA_BRANCH = 'data'

def _git(cmd, cwd=None):
    if cwd is None:
        cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return (r.returncode == 0, r.stdout.strip(), r.stderr.strip())

def export_to_json(filepath=None):
    if filepath is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs(DATA_DIR, exist_ok=True)
        filepath = os.path.join(DATA_DIR, 'journal_' + timestamp + '.json')
    from stock_signals.tracker import get_recommendations
    recs = get_recommendations()
    data = {'exported_at': datetime.now().isoformat(), 'total_records': len(recs), 'records': recs}
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath

def sync_to_github():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = {'success': False, 'message': '', 'file': ''}
    json_path = export_to_json()
    result['file'] = json_path
    result['message'] += '已导出: ' + json_path + chr(10)
    today = datetime.now().strftime('%Y%m%d')
    latest_path = os.path.join(DATA_DIR, 'journal_latest_' + today + '.json')
    shutil.copy2(json_path, latest_path)
_git(['git', 'stash', 'push', '-u', '-m'auto-sync'], repo_root)
    success, stdout, stderr = _git(['git', 'branch', '--list', DATA_BRANCH], repo_root)
    if not success or DATA_BRANCH not in stdout:
        success, stdout, stderr = _git(['git', 'checkout', '-b', DATA_BRANCH, 'main'], repo_root)
        if not success:
            result['message'] += '创建分支失败: ' + stderr + chr(10)
            _git(['git', 'stash', 'pop'], repo_root)
            return result
    else:
        success, stdout, stderr = _git(['git', 'checkout', DATA_BRANCH], repo_root)
        if not success:
            result['message'] += '切换分支失败: ' + stderr + chr(10)
            return result
    success, stdout, stderr = _git(['git', 'pull', 'origin', DATA_BRANCH, '--no-edit'], repo_root)
    if not success and 'nothing to commit' not in stderr.lower():
        result['message'] += '拉取提示: ' + stderr[:100] + chr(10)
    _git(['git', 'add', 'data/'], repo_root)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    msg = 'sync journal data ' + ts
    success, stdout, stderr = _git(['git', 'commit', '-m', msg], repo_root)
    if not success:
        result['message'] += '没有需要提交的更改' + chr(10)
    else:
        success, stdout, stderr = _git(['git', 'push', 'origin', DATA_BRANCH], repo_root)
        if success:
            result['success'] = True
            result['message'] += '同步成功！数据已推送到 GitHub data 分支'
        else:
            result['message'] += '推送失败: ' + stderr + chr(10)
_git(['git', 'stash', 'pop'], repo_root)
    _git(['git', 'checkout', 'main'], repo_root)
    _cleanup_old_backups(repo_root)
    return result

def _cleanup_old_backups(repo_root):
    try:
        files = sorted([f for f in os.listdir(DATA_DIR) if f.startswith('journal_') and f.endswith('.json')], reverse=True)
        for old_file in files[5:]:
            os.remove(os.path.join(DATA_DIR, old_file))
    except Exception:
        pass

def sync_status():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    status = {'has_db': False, 'record_count': 0, 'last_sync': None}
    db_path = os.path.join(os.path.expanduser('~'), '.tech-signal-FUTU-skill', 'journal.db')
    status['has_db'] = os.path.exists(db_path)
    if status['has_db']:
        from stock_signals.tracker import get_recommendations
        status['record_count'] = len(get_recommendations())
    success, stdout, stderr = _git(['git', 'log', 'origin/data', '-1', '--format=%ci'], repo_root)
    if success and stdout:
        status['last_sync'] = stdout.strip()
    return status

def pull_from_github():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = {'success': False, 'message': '', 'imported': 0}
    success, stdout, stderr = _git(['git', 'ls-remote', 'origin', 'refs/heads/data'], repo_root)
    if not success or not stdout.strip():
        result['message'] = 'GitHub 上没有 data 分支'
        return result
    _git(['git', 'checkout', DATA_BRANCH], repo_root)
    _git(['git', 'pull', 'origin', DATA_BRANCH], repo_root)
    json_files = sorted([f for f in os.listdir(DATA_DIR) if f.startswith('journal_') and f.endswith('.json')], reverse=True) if os.path.exists(DATA_DIR) else []
    if not json_files:
        result['message'] = 'data 分支上没有找到 JSON 文件'
        _git(['git', 'checkout', 'main'], repo_root)
        return result
    latest_file = os.path.join(DATA_DIR, json_files[0])
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    from stock_signals.tracker import init_db, _get_conn
    init_db()
    conn = _get_conn()
    c = conn.cursor()
    imported = 0
    fields = ['scan_date','symbol','rating','score','resonance','trend_phase','current_price','entry_price','entry_type','stop_loss','target1','target2','rr_ratio','position_pct','hold_period','buy_strategy','sell_strategy','sector','note','outcome','outcome_price','outcome_pnl_pct']
    for rec in data.get('records', []):
        c.execute('SELECT id FROM recommendations WHERE id = ?', (rec.get('id'),))
        if not c.fetchone():
            vals = [rec.get(field) for field in fields]
            col_str = ','.join(fields)
            ph = ','.join(['?'] * len(fields))
            sql = 'INSERT INTO recommendations (' + col_str + ') VALUES (' + ph + ')'
            c.execute(sql, vals)
            imported += 1
    conn.commit()
    conn.close()
    _git(['git', 'checkout', 'main'], repo_root)
    total = data.get('total_records', 0)
    result['success'] = True
    result['message'] = '已从 GitHub 导入 ' + str(imported) + ' 条新记录（共 ' + str(total) + ' 条）'
    result['imported'] = imported
    return result

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'pull':
        r = pull_from_github()
    else:
        r = sync_to_github()
    print(json.dumps(r, ensure_ascii=False, indent=2))
