# -*- coding: utf-8 -*-
import re

path = r'D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\screener.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import after config import
old_imp = 'from .config import config'
new_imp = old_imp + '\nfrom .hot_fetcher import fetch_hot_stocks as _fetch_hot_stocks_live'
content = content.replace(old_imp, new_imp, 1)

# 2. Replace old functions block
old_start = 'def _fetch_hot_stocks_free(market: str, top_n: int = 300) -> List[str]:'
old_end = '\n\nMARKET_NAMES'
start_idx = content.find(old_start)
end_idx = content.find(old_end, start_idx)
if start_idx == -1 or end_idx == -1:
    print(f'ERROR: start={start_idx}, end={end_idx}')
    exit(1)

new_code = '''def _fetch_hot_stocks(market: str, top_n: int = 300) -> List[str]:
    """Get hot stocks - live API first, fallback to static pool."""
    live_codes = _fetch_hot_stocks_live(market, top_n)
    live_codes = [c for c in live_codes if not _is_blacklisted(c)]
    if live_codes:
        logger.info(f"  Hot stocks (live): {len(live_codes)}")
        return live_codes
    logger.info("  Hot stocks: fallback to static pool")
    if market == "A":
        codes = _A_HOT_STOCKS_POOL[:top_n]
    elif market == "HK":
        codes = _HK_HOT_STOCKS_POOL[:top_n]
    elif market == "US":
        codes = _US_HOT_STOCKS_POOL[:top_n]
    else:
        codes = []
    return [c for c in codes if not _is_blacklisted(c)]


def sync_hot_stocks(market: str, top_n: int = 300) -> int:
    """Sync today hot stocks to static pool and persist to file."""
    from .hot_fetcher import fetch_a_hot_stocks, fetch_hk_hot_stocks, fetch_us_hot_stocks
    if market == "A":
        codes = fetch_a_hot_stocks(top_n)
    elif market == "HK":
        codes = fetch_hk_hot_stocks(top_n)
    elif market == "US":
        codes = fetch_us_hot_stocks(top_n)
    else:
        return 0
    codes = [c for c in codes if not _is_blacklisted(c)]
    if not codes:
        logger.warning(f"  No hot stocks to sync ({market})")
        return 0
    pool_key = f"_{market.upper()}_HOT_STOCKS_POOL"
    existing = globals().get(pool_key, [])
    merged = list(dict.fromkeys(codes + existing))[:top_n]
    globals()[pool_key] = merged
    _write_pool_to_file(pool_key, merged)
    logger.info(f"  Synced {len(codes)} hot stocks to {market} pool (total {len(merged)})")
    return len(codes)


def _write_pool_to_file(var_name: str, codes: List[str]):
    """Write hot stock pool back to screener.py."""
    pool_str = ", ".join(f'"{c}"' for c in codes)
    pat = re.escape(var_name) + r"\s*=\s*\[([\s\S]*?)\n\s*\]"
    repl = var_name + " = [\n    " + pool_str + ",\n]"
    with open(path, "r", encoding="utf-8") as f:
        cnt = f.read()
    cnt = re.sub(pat, repl, cnt, count=1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(cnt)

'''

content = content[:start_idx] + new_code + content[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
