# -*- coding: utf-8 -*-
import re
path = r'D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\screener.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Add import
for i, line in enumerate(lines):
    if 'from .config import config' in line:
        lines.insert(i+1, 'from .hot_fetcher import fetch_hot_stocks as _fetch_hot_stocks_live\n')
        print(f"Added import at line {i+2}")
        break

# 2. Find function boundaries
start = -1
end = -1
for i, line in enumerate(lines):
    if line.startswith('def _fetch_hot_stocks_free('):
        start = i
    if start != -1 and end == -1 and line.startswith('MARKET_NAMES'):
        end = i
        break
print(f"Replacing lines {start+1} to {end}")

new_code = []
new_code.append('def _fetch_hot_stocks(market: str, top_n: int = 300) -> List[str]:')
new_code.append('    \"\"\"Get hot stocks - live API first, fallback to static pool.\"\"\"')
new_code.append('    live_codes = _fetch_hot_stocks_live(market, top_n)')
new_code.append('    live_codes = [c for c in live_codes if not _is_blacklisted(c)]')
new_code.append('    if live_codes:')
new_code.append('        logger.info(f\"  Hot stocks (live): {len(live_codes)}\")')
new_code.append('        return live_codes')
new_code.append('    logger.info(\"  Hot stocks: fallback to static pool\")')
new_code.append('    if market == \"A\":')
new_code.append('        codes = _A_HOT_STOCKS_POOL[:top_n]')
new_code.append('    elif market == \"HK\":')
new_code.append('        codes = _HK_HOT_STOCKS_POOL[:top_n]')
new_code.append('    elif market == \"US\":')
new_code.append('        codes = _US_HOT_STOCKS_POOL[:top_n]')
new_code.append('    else:')
new_code.append('        codes = []')
new_code.append('    return [c for c in codes if not _is_blacklisted(c)]')
new_code.append('')
new_code.append('')
new_code.append('def sync_hot_stocks(market: str, top_n: int = 300) -> int:')
new_code.append('    \"\"\"Sync today hot stocks to static pool and persist to file.\"\"\"')
new_code.append('    from .hot_fetcher import fetch_a_hot_stocks, fetch_hk_hot_stocks, fetch_us_hot_stocks')
new_code.append('    if market == \"A\":')
new_code.append('        codes = fetch_a_hot_stocks(top_n)')
new_code.append('    elif market == \"HK\":')
new_code.append('        codes = fetch_hk_hot_stocks(top_n)')
new_code.append('    elif market == \"US\":')
new_code.append('        codes = fetch_us_hot_stocks(top_n)')
new_code.append('    else:')
new_code.append('        return 0')
new_code.append('    codes = [c for c in codes if not _is_blacklisted(c)]')
new_code.append('    if not codes:')
new_code.append('        logger.warning(f\"  No hot stocks to sync ({market})\")')
new_code.append('        return 0')
new_code.append('    pool_key = f\"_{market.upper()}_HOT_STOCKS_POOL\"')
new_code.append('    existing = globals().get(pool_key, [])')
new_code.append('    merged = list(dict.fromkeys(codes + existing))[:top_n]')
new_code.append('    globals()[pool_key] = merged')
new_code.append('    _write_pool_to_file(pool_key, merged)')
new_code.append('    logger.info(f\"  Synced {len(codes)} hot stocks to {market} pool (total {len(merged)})\")')
new_code.append('    return len(codes)')
new_code.append('')
new_code.append('')
new_code.append('def _write_pool_to_file(var_name: str, codes: List[str]):')
new_code.append('    \"\"\"Write hot stock pool back to screener.py.\"\"\"')
new_code.append('    import re as _re')
new_code.append(\"    pool_str = ', '.join('\\"' + c + '\\"' for c in codes)\")
new_code.append(\"    pat = _re.escape(var_name) + r'\\\\s*=\\\\s*\\\\[([^\\\\]]*?)\\\\n\\\\s*\\\\]'\")
new_code.append(\"    repl = var_name + ' = [\\\\n    ' + pool_str + ',\\\\n]'\")
new_code.append(\"    with open(path, 'r', encoding='utf-8') as f:\")
new_code.append('        cnt = f.read()')
new_code.append('    cnt = _re.sub(pat, repl, cnt, count=1)')
new_code.append(\"    with open(path, 'w', encoding='utf-8') as f:\")
new_code.append('        f.write(cnt)')
new_code.append('')
new_code.append('')

result = lines[:start] + new_code + lines[end:]
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(result)
print(f"Done. Lines: {len(result)}")
print(f'Has ScanConfig: {any(\"class ScanConfig\" in l for l in result)}')
print(f'Has sync_hot_stocks: {any(\"def sync_hot_stocks\" in l for l in result)}')