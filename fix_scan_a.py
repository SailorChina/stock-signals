
path = r'D:\Backup\Documents\ChatGPT\AI\stock-signals\stock_signals\screener_a.py'
with open(path, 'r', encoding='utf-8') as f:
    txt = f.read()

lines = txt.split('\n')
# Find scan_a function start
start_idx = None
for i, l in enumerate(lines):
    if l.startswith('def scan_a('):
        start_idx = i
        break

# Find end: next function def or end of file
end_idx = len(lines)
for i in range(start_idx + 1, len(lines)):
    if lines[i].startswith('def ') and not lines[i].startswith('def scan_a'):
        end_idx = i
        break

print(f'Found scan_a at lines {start_idx+1}-{end_idx}')

new_func_lines = [
    'def scan_a(markets=None, config=None, output_json=False, output_file=""): ',
    '    from .screener import ScanConfig ',
    '    from .hot_fetcher import fetch_a_hot_stocks ',
    '    if config is None: config = ScanConfig() ',
    '    codes = fetch_a_hot_stocks(300) ',
    '    logger.info(f"A\u80a1\u9884\u9009: {len(codes)}\u53ea") ',
    '    picks, watchlist, total_analyzed = [], [], 0 ',
    '    batch_size = 30 ',
    '    for i in range(0, len(codes), batch_size): ',
    '        batch = codes[i:i+batch_size] ',
    '        batch_results = [] ',
    '        with ThreadPoolExecutor(max_workers=4) as executor: ',
    '            futures = {executor.submit(_analyze_one_a, code, delay=0.05): code for code in batch} ',
    '            for future in as_completed(futures): ',
    '                try: ',
    '                    r = future.result(); total_analyzed += 1 ',
    '                    if r is not None: batch_results.append(r) ',
    '                except Exception as e: ',
    '                    logger.warning(f"\u5e76\u884c\u5206\u6790\u5931\u8d25: {futures[future]} - {e}") ',
    '        for result in batch_results: ',
    '            if result.score >= 55: picks.append(result) ',
    '            elif result.score >= 45: watchlist.append(result) ',
    '        if len(picks) > config.max_per_market * 3: picks = picks[:config.max_per_market * 3] ',
    '        logger.info(f"A\u80a1: \u5df2\u5904\u7406 {min(i+batch_size, len(codes))}/{len(codes)}") ',
    '    picks.sort(key=lambda x: x.score, reverse=True) ',
    '    watchlist.sort(key=lambda x: x.score, reverse=True) ',
    '    final_picks = picks[:config.max_per_market]; final_watch = watchlist[:config.max_per_market] ',
    '    summary = {"scan_time": time.strftime("%Y-%m-%d %H:%M:%S"), "total_analyzed": total_analyzed, "total_picks": len(final_picks), "total_watchlist": len(final_watch), "markets_scanned": ["A"]} ',
    '    output = {"date": time.strftime("%Y-%m-%d"), "summary": summary, "picks": {"A": [{"code": p.code, "score": p.score, "rating": p.rating, "rating_cn": p.rating_cn, "trend_phase": p.trend_phase, "trend_phase_cn": p.trend_phase_cn, "alignment": p.alignment, "alignment_cn": p.alignment_cn, "entry": p.entry, "stop_loss": p.stop_loss, "target_1": p.target_1, "target_2": p.target_2, "risk_reward": p.risk_reward, "position_pct": p.position_pct, "reasons": list(p.reasons) if p.reasons else [], "holding_period": p.holding_period, "last_close": p.last_close} for p in final_picks]}, "watchlist": {"A": [{"code": w.code, "score": w.score, "rating": w.rating, "rating_cn": w.rating_cn, "trend_phase": w.trend_phase, "trend_phase_cn": w.trend_phase_cn, "alignment": w.alignment, "alignment_cn": w.alignment_cn, "entry": w.entry, "stop_loss": w.stop_loss, "target_1": w.target_1, "target_2": w.target_2, "risk_reward": w.risk_reward, "position_pct": w.position_pct, "reasons": list(w.reasons) if w.reasons else [], "holding_period": w.holding_period, "last_close": w.last_close} for w in final_watch]}} ',
    '    if output_json or output_file: ',
    '        json_output = json.dumps(output, ensure_ascii=False, indent=2) ',
    '        if output_json: print(json_output) ',
    '        if output_file: ',
    '            with open(output_file, "w", encoding="utf-8") as f: f.write(json_output) ',
    '    logger.info(f"A\u80a1\u626b\u63cf\u5b8c\u6210: \u5206\u6790{total_analyzed}\u53ea, \u63a8\u8350{len(final_picks)}\u53ea, \u89c2\u5bdf{len(final_watch)}\u53ea") ',
    '    return output ',
]

# Build new content
new_lines = lines[:start_idx] + new_func_lines + lines[end_idx:]
new_txt = '\n'.join(new_lines)

# Ensure concurrent import exists
if 'from concurrent.futures import ThreadPoolExecutor' not in new_txt:
    new_txt = new_txt.replace(
        'import logging, time, json\nfrom dataclasses import dataclass, field\nfrom typing import List, Optional',
        'import logging, time, json\nfrom dataclasses import dataclass, field\nfrom typing import List, Optional\nfrom concurrent.futures import ThreadPoolExecutor, as_completed'
    )

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_txt)
print('Done!')
