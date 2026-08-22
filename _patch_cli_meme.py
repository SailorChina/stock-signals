import os
cwd = os.getcwd()
path = os.path.join(cwd, 'stock_signals', 'cli.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Patch 1: Add meme import
old = 'from stock_signals.sector import get_sector_ranking, get_sector_ranking_for_display'
new = old + chr(10) + 'from stock_signals.meme_tracker import get_meme_stocks, get_meme_codes, add_meme_stock, remove_meme_stock, list_meme_watchlist'
content = content.replace(old, new)

# Patch 2: Add meme subcommand
old2 = '    p_sector.add_argument("--top", "-t", type=int, default=10, help="显示前N个板块")'
new2 = old2 + chr(10) + '    p_sector.add_argument("--json", "-j", action="store_true", help="JSON output")' + chr(10) + '    p_sector.add_argument("--top", "-t", type=int, default=10, help="显示前N个板块")'
# Actually let me find the right place
old2 = '    p_sector.add_argument("--top", "-t", type=int, default=10, help="显示前N个板块")'
if old2 in content:
    new2 = '    p_sector.add_argument("--top", "-t", type=int, default=10, help="显示前N个板块")' + chr(10)
    content = content.replace(old2, new2, 1)

# Find the sector command handling and add meme after it
old3 = '        sys.exit(0)'
# Only replace the first occurrence (after sector)
idx3 = content.find('        sys.exit(0)')
if idx3 > 0:
    sector_exit = content[idx3:idx3+20]
    # Find the sector section
    sector_idx = content.find('if args.cmd == "sector":')
    if sector_idx > 0:
        # Find the sys.exit(0) after the sector section
        exit_idx = content.find('sys.exit(0)', sector_idx)
        if exit_idx > 0:
            after_exit = content[exit_idx+len('sys.exit(0)'):]
            meme_cmd = '''
    if args.cmd == "meme":
        subcmd = getattr(args, "meme_cmd", None)
        if subcmd == "list":
            _print_meme_list()
        elif subcmd == "add":
            codes = getattr(args, "meme_add", [])
            for code in codes:
                add_meme_stock(code, source=getattr(args, "meme_source", "manual"), note=getattr(args, "meme_note", ""))
        elif subcmd == "remove":
            codes = getattr(args, "meme_remove", [])
            for code in codes:
                remove_meme_stock(code)
        elif subcmd == "scan":
            _print_meme_scan()
        elif subcmd == "scrape":
            n = auto_scrape()
            print(f"  新增 {n} 只股票到 meme watchlist")
        else:
            _print_meme_list()
        sys.exit(0)
'''
            content = content[:exit_idx+len('sys.exit(0)')] + meme_cmd + after_exit

# Patch 3: Add meme subparser and functions
old4 = 'def main():'
new4 = '''def _print_meme_list():
    stocks = get_meme_stocks()
    print()
    print("=" * 64)
    print("  猫姐 Meme Watchlist")
    print("=" * 64)
    print()
    if not stocks:
        print("  (空，使用 meme add 添加股票)")
    else:
        print(f"  {len(stocks)} 只股票")
        print()
        for s in stocks:
            bonus = get_meme_bonus(s.code)
            print(f"  {s.code:10s}  [{s.source:12s}]  mentions={s.mention_count}  bonus={bonus:.2f}")
            if s.note:
                print(f"             note: {s.note}")
    print()
    print("  命令:")
    print("    meme list          查看 watchlist")
    print("    meme add US.NVDA   添加股票")
    print("    meme remove US.NVDA 移除股票")
    print("    meme scan          分析所有 meme 股票")
    print("    meme scrape        尝试自动抓取")
    print()


def _print_meme_scan():
    from stock_signals.indicators import fetch_kline, compute_indicators
    from stock_signals.scoring import compute_rating
    from stock_signals.sector import get_sector_ranking, get_sector_bonus
    stocks = get_meme_stocks()
    if not stocks:
        print("  (watchlist 为空，使用 meme add 添加)")
        return
    ranks = get_sector_ranking()
    print()
    print("=" * 64)
    print("  猫姐 Meme Stocks 分析")
    print("=" * 64)
    print()
    for s in stocks:
        try:
            df = fetch_kline(s.code, "1d", 300)
            if df is None or df.empty or len(df) < 60:
                print(f"  {s.code:10s}  数据不足")
                continue
            ind = compute_indicators(df, s.code, "1d")
            rating = compute_rating(ind)
            sector_bonus = get_sector_bonus(s.code, ranks)
            meme_bonus = get_meme_bonus(s.code)
            final_score = rating["score"] * sector_bonus * meme_bonus
            print(f"  {s.code:10s}  {rating['rating']:12s}  score={final_score:5.1f}  meme={meme_bonus:.2f}  sector={sector_bonus:.2f}")
        except Exception as e:
            print(f"  {s.code:10s}  分析失败: {e}")
    print()


def main():'''
content = content.replace(old4, new4, 1)

# Patch 4: Add meme subparser in the argparser section
old5 = '    p_sector = sub.add_parser("sector", help="板块热度排名")'
new5 = '    p_meme = sub.add_parser("meme", help="猫姐 meme 股票追踪")' + chr(10) + '    meme_sub = p_meme.add_subparsers(dest="meme_cmd")' + chr(10) + '    meme_sub.add_parser("list", help="查看 watchlist")' + chr(10) + '    p_add = meme_sub.add_parser("add", help="添加股票")' + chr(10) + '    p_add.add_argument("codes", nargs="+", help="股票代码")' + chr(10) + '    p_add.add_argument("--source", default="manual")' + chr(10) + '    p_add.add_argument("--note", default="")' + chr(10) + '    meme_sub.add_parser("remove", help="移除股票")' + chr(10) + '    p_rem = meme_sub.add_parser("remove", help="移除股票")' + chr(10) + '    p_rem.add_argument("codes", nargs="+", help="股票代码")' + chr(10) + '    meme_sub.add_parser("scan", help="分析所有 meme 股票")' + chr(10) + '    meme_sub.add_parser("scrape", help="尝试自动抓取")' + chr(10) + '    p_sector = sub.add_parser("sector", help="板块热度排名")'
content = content.replace(old5, new5)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'CLI patched, length: {len(content)}')

import ast
with open(path, 'r', encoding='utf-8') as f:
    ast.parse(f.read())
print('Syntax OK')
