# -*- coding: utf-8 -*-
"""每日推荐报告生成器"""
from __future__ import annotations

import logging
from typing import Dict, List

logger = logging.getLogger("stock-signals")

RATING_CN = {
    "Buy": "\u4e70\u5165", "Overweight": "\u504f\u591a", "Hold": "\u89c2\u671b",
    "Underweight": "\u504f\u7a7a", "Sell": "\u5356\u51fa",
}
CONF_CN = {"high": "\u9ad8", "medium": "\u4e2d", "low": "\u4f4e"}
ALIGN_CN = {
    "strong_up": "\u5f3a\u5171\u632f\u770b\u591a", "aligned": "\u5171\u632f\u770b\u591a",
    "mixed": "\u5206\u6b67", "aligned_down": "\u5171\u632f\u770b\u7a7a",
    "strong_down": "\u5f3a\u5171\u632f\u770b\u7a7a", "none": "\u65e0",
}
PHASE_CN = {
    "accumulation": "\u5438\u7b79\u9636\u6bb5", "early_rally": "\u4e0a\u6da8\u65e9\u671f",
    "rally": "\u4e0a\u6da8\u9636\u6bb5", "distribution": "\u6d3e\u53d1\u9636\u6bb5",
    "decline": "\u4e0b\u8dcc\u9636\u6bb5", "unknown": "\u672a\u77e5",
}
MARKET_NAMES = {
    "SH": "\u00a5A\u80a1\uff08\u6caa\uff09", "SZ": "\u00a5A\u80a1\uff08\u6df1\uff09",
    "HK": "\u00a5\u9999\u6e2f", "US": "\u00a5\u7f8e\u80a1", "A": "\u00a5A\u80a1",
}


def print_scan_report(result: Dict) -> None:
    """\u6253\u5370\u6bcf\u65e5\u63a8\u8350\u62a5\u544a\uff08\u4e2d\u6587\uff09"""
    import time
    date = result.get("date", time.strftime("%Y-%m-%d"))
    summary = result.get("summary", {})
    picks = result.get("picks", {})
    watchlist = result.get("watchlist", {})
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  \u00a5\u6bcf\u65e5\u80a1\u7968\u63a8\u8350\u62a5\u544a  {date}")
    print(sep)
    print(f"  \u626b\u63cf\u65f6\u95f4: {summary.get('scan_time', '\u672a\u77e5')}")
    print(f"  \u5206\u6790 {summary.get('total_analyzed', 0)} \u53ea | \u63a8\u8350 {summary.get('total_picks', 0)} \u53ea | \u89c2\u5bdf {summary.get('total_watchlist', 0)} \u53ea")
    print()
    # 逐市场输出
    for market in ["A", "HK", "US"]:
        market_picks = picks.get(market, [])
        market_watch = watchlist.get(market, [])
        if not market_picks and not market_watch:
            continue
        mname = MARKET_NAMES.get(market, market)
        print(f"{'─' * 60}")
        print(f"  {mname}")
        print(f"{'─' * 60}")
        # 主推荐
        if market_picks:
            print(f"  \u00a5\u63a8\u8350\uff08{len(market_picks)}\u53ea\uff09:")
            for i, r in enumerate(market_picks, 1):
                _print_stock(r, i)
            print()
        # 观察名单
        if market_watch:
            print(f"  \u00a5\u89c2\u5bdf\uff08\u6697\u624b\uff09\uff08{len(market_watch)}\u53ea\uff09:")
            for i, r in enumerate(market_watch, 1):
                _print_stock(r, i, watch=True)
            print()
    print(sep)
    print("  \u514d\u8d23\u58f0\u660e: \u672c\u5de5\u5177\u4ec5\u4f9b\u6280\u672f\u53c2\u8003\uff0c\u4e0d\u6784\u6210\u4efb\u4f55\u6295\u8d44\u5efa\u8bae\u3002")
    print(sep + "\n")


def _print_stock(r, index: int, watch: bool = False):
    """\u6253\u5370\u5355\u53ea\u80a1\u7968\u4fe1\u606f"""
    rating_cn = RATING_CN.get(r.rating, r.rating)
    align_cn = ALIGN_CN.get(r.alignment, r.alignment)
    phase_cn = PHASE_CN.get(r.trend_phase, r.trend_phase)
    prefix = "[\u89c2]" if watch else f"{index}."
    print(f"  {prefix} {r.code}  \u4ef7\u683c: {r.last_close:.2f}")
    print(f"      \u8bc4\u7ea7: {r.rating} ({rating_cn}) \u00b7 \u5206: {r.score:.1f} \u00b7 \u5171\u632f: {align_cn}")
    print(f"      \u8d8b\u52bf: {phase_cn}")
    if r.entry > 0:
        print(f"      \u5165\u573a: {r.entry:.2f}  \u6b62\u635f: {r.stop_loss:.2f}"
              f"  \u76ee\u68071: {r.target_1:.2f}  \u76ee\u68072: {r.target_2:.2f}"
              f"  RR: {r.risk_reward:.1f}:1")
    if r.reasons:
        print(f"      \u7406\u7531: {', '.join(r.reasons[:5])}")


def get_summary_text(result: Dict) -> str:
    """\u8fd4\u56de\u7b80\u77ed\u6587\u672c\u6458\u8981\uff08\u7528\u4e8e\u63a8\u9001\uff09"""
    lines = [f"\u00a5\u6bcf\u65e5\u80a1\u7968\u63a8\u8350 {result.get('date', '')}"]
    for market in ["A", "HK", "US"]:
        picks = result.get("picks", {}).get(market, [])
        if picks:
            names = [f"{p.code}({p.rating})" for p in picks[:3]]
            lines.append(f"  {MARKET_NAMES.get(market, market)}: {', '.join(names)}")
    return "\n".join(lines)
