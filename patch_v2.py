# -*- coding: utf-8 -*-
import re

path = r'D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\screener.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Add import after line 22
insert_line = 22  # after "from .config import config"
lines.insert(insert_line, 'from .hot_fetcher import fetch_hot_stocks as _fetch_hot_stocks_live\n')

# 2. Find and replace the two old functions (lines 259-318 in original, shifted by 1)
# Find start: def _fetch_hot_stocks_free
start = -1
end = -1
for i, line in enumerate(lines):
    if line.startswith('def _fetch_hot_stocks_free('):
        start = i
    if start != -1 and end == -1 and line.startswith('MARKET_NAMES'):
        end = i
        break

print(f'Replacing lines {start+1} to {end} (total {end-start} lines)')

# Build new code
new_code = [
    'def _fetch_hot_stocks(market: str, top_n: int = 300) -> List[str]:\n',
    '    """Get hot stocks - live API first, fallback to static pool."""\n',
    '    live_codes = _fetch_hot_stocks_live(market, top_n)\n',
    '    live_codes = [c for c in live_codes if not _is_blacklisted(c)]\n',
    '    if live_codes:\n',
    '        logger.info(f"  Hot stocks (live): {len(live_codes)}")\n',
    '        return live_codes\n',
    '    logger.info("  Hot stocks: fallback to static pool")\n',
    '    if market == "A":\n',
    '        codes = _A_HOT_STOCKS_POOL[:top_n]\n',
    '    elif market == "HK":\n',
    '        codes = _HK_HOT_STOCKS_POOL[:top_n]\n',
    '    elif market == "US":\n',
    '        codes = _US_HOT_STOCKS_POOL[:top_n]\n',
    '    else:\n',
    '        codes = []\n',
    '    return [c for c in codes if not _is_blacklisted(c)]\n',
    '\n',
    '\n',
    'def sync_hot_stocks(market: str, top_n: int = 300) -> int:\n',
    '    """Sync today hot stocks to static pool and persist to file."""\n',
    '    from .hot_fetcher import fetch_a_hot_stocks, fetch_hk_hot_stocks, fetch_us_hot_stocks\n',
    '    if market == "A":\n',
    '        codes = fetch_a_hot_stocks(top_n)\n',
    '    elif market == "HK":\n',
    '        codes = fetch_hk_hot_stocks(top_n)\n',
    '    elif market == "US":\n',
    '        codes = fetch_us_hot_stocks(top_n)\n',
    '    else:\n',
    '        return 0\n',
    '    codes = [c for c in codes if not _is_blacklisted(c)]\n',
    '    if not codes:\n',
    '        logger.warning(f"  No hot stocks to sync ({market})")\n',
    '        return 0\n',
    '    pool_key = f"_{market.upper()}_HOT_STOCKS_POOL"\n',
    '    existing = globals().get(pool_key, [])\n',
    '    merged = list(dict.fromkeys(codes + existing))[:top_n]\n',
    '    globals()[pool_key] = merged\n',
    '    _write_pool_to_file(pool_key, merged)\n',
    '    logger.info(f"  Synced {len(codes)} hot stocks to {market} pool (total {len(merged)})")\n',
    '    return len(codes)\n',
    '\n',
    '\n',
    'def _write_pool_to_file(var_name: str, codes: List[str]):\n',
    '    """Write hot stock pool back to screener.py."""\n',
    '    import re as _re\n',
    '    pool_str = ", ".join(f\'{c}\' for c in codes)\n',
    "    pat = _re.escape(var_name) + r'\\s*=\\s*\\[([^\\]]*?)\\n\\s*\\]'\n",
    "    repl = var_name + ' = [\n' + '    ' + pool_str + ',\n]'\n",
    "    with open(path, 'r', encoding='utf-8') as f:\n",
    '        cnt = f.read()\n',
    '    cnt = _re.sub(pat, repl, cnt, count=1)\n',
    "    with open(path, 'w', encoding='utf-8') as f:\n",
    '        f.write(cnt)\n',
    '\n',
    '\n',
]

result = lines[:start] + new_code + lines[end:]
with open(path, 'w', encoding='utf-8') as f:
    f.writelines(result)
print(f'Done. New file has {len(result)} lines')
