# -*- coding: utf-8 -*-
"""每日推荐报告生成器"""
from __future__ import annotations

import logging
from typing import Dict, List
from ._info import get_stock_info

logger = logging.getLogger("stock-signals")

RATING_CN = {
    "Buy": "买入", "Overweight": "偏多", "Hold": "观望",
    "Underweight": "偏空", "Sell": "卖出",
}
CONF_CN = {"high": "高", "medium": "中", "low": "低"}
ALIGN_CN = {
    "strong_up": "强共振看多", "aligned": "共振看多",
    "mixed": "分歧", "aligned_down": "共振看空",
    "strong_down": "强共振看空", "none": "无",
}
PHASE_CN = {
    "accumulation": "吸筹阶段", "early_rally": "上涨早期",
    "rally": "上涨阶段", "distribution": "派发阶段",
    "decline": "下跌阶段", "unknown": "未知",
}
MARKET_NAMES = {
    "SH": "¥A股（沪）", "SZ": "¥A股（深）",
    "HK": "¥香港", "US": "¥美股", "A": "¥A股",
}


def print_scan_report(result: Dict) -> None:
    import time
    date = result.get("date", time.strftime("%Y-%m-%d"))
    summary = result.get("summary", {})
    picks = result.get("picks", {})
    watchlist = result.get("watchlist", {})
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  ¥每日股票推荐报告  {date}")
    print(sep)
    print(f"  扫描时间: {summary.get('scan_time', '未知')}")
    print(f"  分析 {summary.get('total_analyzed', 0)} 只 | 推荐 {summary.get('total_picks', 0)} 只 | 观察 {summary.get('total_watchlist', 0)} 只")
    print()
    for market in ["A", "HK", "US"]:
        market_picks = picks.get(market, [])
        market_watch = watchlist.get(market, [])
        if not market_picks and not market_watch:
            continue
        mname = MARKET_NAMES.get(market, market)
        print(f"{'─' * 60}")
        print(f"  {mname}")
        print(f"{'─' * 60}")
        if market_picks:
            print(f"  ¥推荐（{len(market_picks)}只）:")
            for i, r in enumerate(market_picks, 1):
                _print_stock(r, i)
            print()
        if market_watch:
            print(f"  ¥观察（候选）（{len(market_watch)}只）:")
            for i, r in enumerate(market_watch, 1):
                _print_stock(r, i, watch=True)
            print()
    print(sep)
    print("  免责声明: 本工具仅供技术参考，不构成任何投资建议。")
    print(sep + "\n")


def _fmt_pct(value: float, current: float) -> str:
    if current <= 0:
        return ""
    pct = (value - current) / current * 100
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}%"


def _gen_entry_conditions(r) -> List[str]:
    conditions = []
    reasons = getattr(r, 'reasons', []) or []
    reason_str = " ".join(reasons) if reasons else ""
    info = get_stock_info(r.code)
    cn_name = info.get("name", "")

    # RSI 超买/超卖
    if "RSI" in reason_str and ("超买" in reason_str or "严重超买" in reason_str):
        conditions.append("RSI极端超买，等待回调至RSI<65再考虑买入")
    elif "RSI" in reason_str and ("超卖" in reason_str or "严重超卖" in reason_str):
        conditions.append("RSI严重超卖，等待企稳反弹信号")

    # ADX 趋势强度
    if "ADX" in reason_str and ("弱" in reason_str or "weak" in reason_str.lower()):
        conditions.append("ADX趋势弱(<20)，等待ADX>25确认趋势后再买入")
    elif "ADX" in reason_str and ("强" in reason_str or "strong" in reason_str.lower()):
        conditions.append("ADX趋势强劲，可顺势跟进")

    # MACD 信号
    if "MACD" in reason_str and "死叉" in reason_str:
        conditions.append("MACD死叉，中期偏空，等待金叉后再考虑")
    elif "MACD" in reason_str and ("负" in reason_str or "空头" in reason_str):
        conditions.append("MACD柱为负，等待金叉或柱翻正后再买入")
    elif "MACD" in reason_str and "金叉" in reason_str:
        conditions.append("MACD金叉确认，多头动能较强")

    # MA60 位置
    if "MA60" in reason_str and "深度回调" in reason_str:
        conditions.append(f"{cn_name}价格深度回调，等待缩量止跌企稳信号")
    elif "MA60" in reason_str and "高于" in reason_str and ("过度" in reason_str or "超买" in reason_str):
        conditions.append(f"{cn_name}价格偏离MA60过大，等待回踩MA20/MA60附近支撑")
    elif "MA60" in reason_str and "健康" in reason_str:
        conditions.append(f"{cn_name}价格处于MA60健康区间，趋势稳健")

    # KDJ 超买
    if "KDJ" in reason_str and "超买" in reason_str:
        conditions.append("KDJ超买(J>100)，等待K值回落至80以下再考虑")

    # TD 9转信号
    if "TD" in reason_str and "卖出" in reason_str and "完成" in reason_str:
        conditions.append("TD卖出序列已完成，短期见顶信号，谨慎追高")
    elif "TD" in reason_str and "买入" in reason_str and "完成" in reason_str:
        conditions.append("TD买入序列完成(9转)，可关注低吸机会")
    elif "TD" in reason_str and "卖出" in reason_str:
        conditions.append("TD卖出序列进行中，等待9转完成确认")
    elif "TD" in reason_str and "买入" in reason_str and "进行中" in reason_str:
        conditions.append("TD买入序列进行中，继续观察")

    # VCP 模式
    if "VCP" in reason_str and "强" in reason_str:
        conditions.append(f"{cn_name}VCP强模式确认，等待价格突破pivot点入场")
    elif "VCP" in reason_str:
        conditions.append(f"{cn_name}VCP波动率收缩模式，等待突破确认后入场")
    elif "Episodic" in reason_str or "事件性转折" in reason_str:
        conditions.append(f"{cn_name}事件性突破，等待回踩确认支撑后再入场")

    # OBV 资金流向
    if "OBV" in reason_str and "下降" in reason_str:
        conditions.append(f"{cn_name}OBV资金流出，等待放量企稳信号")
    elif "OBV" in reason_str and "上升" in reason_str:
        conditions.append(f"{cn_name}OBV资金持续流入，上涨动能健康")

    # 默认：根据入场价距离生成条件
    if not conditions:
        if r.entry > 0 and r.last_close > 0:
            dist = (r.entry - r.last_close) / r.last_close * 100
            if dist < -3:
                conditions.append(f"{cn_name}: 等待价格回落至入场区{r.entry:.2f}（距现价{dist:.1f}%）")
            elif dist < 0:
                conditions.append(f"{cn_name}: 等待价格轻微回落至入场区{r.entry:.2f}（约{abs(dist):.1f}%）")
            elif dist < 5:
                conditions.append(f"{cn_name}: 等待价格突破入场区{r.entry:.2f}（距现价+{dist:.1f}%）")
            else:
                conditions.append(f"{cn_name}: 当前价格接近入场区{r.entry:.2f}，可关注突破机会")
        elif r.entry > 0:
            conditions.append(f"等待价格到达入场区{r.entry:.2f}附近")
        else:
            conditions.append("等待技术信号进一步确认后再入场")

    return conditions[:5]


def _gen_risk_warnings(r) -> List[str]:
    warnings = []
    reasons = getattr(r, 'reasons', []) or []
    reason_str = " ".join(reasons) if reasons else ""

    if "严重超买" in reason_str:
        warnings.append("严重超买，回调风险高")
    elif "超买" in reason_str:
        warnings.append("超买区域，注意短线回调")
    if "严重超卖" in reason_str:
        warnings.append("严重超卖，可能有继续下跌空间")
    if "MACD死叉" in reason_str:
        warnings.append("MACD死叉，中期趋势偏空")
    if "均线空头排列" in reason_str:
        warnings.append("均线空头排列，趋势向下")
    if r.risk_reward > 0 and r.risk_reward < 2.0:
        warnings.append(f"RR={r.risk_reward:.1f}:1，风险回报不足，谨慎")

    return warnings


def _print_stock(r, index: int, watch: bool = False):
    rating_cn = RATING_CN.get(r.rating, r.rating)
    align_cn = ALIGN_CN.get(r.alignment, r.alignment)
    phase_cn = PHASE_CN.get(r.trend_phase, r.trend_phase)
    prefix = "[观]" if watch else f"{index}."

    # 股票基本信息
    info = get_stock_info(r.code)
    cn_name = info.get("name", "")
    sector = info.get("sector", "")
    desc = info.get("desc", "")
    meta = f" {cn_name}" + (f" · {sector}" if sector else "")

    print(f"  {prefix} {r.code}{meta}  现价: {r.last_close:.2f}")
    print(f"      评级: {r.rating} ({rating_cn}) · 分: {r.score:.1f} · 共振: {align_cn}")
    print(f"      趋势: {phase_cn}" + (f"  |  {desc}" if desc else ""))

    if r.entry > 0:
        dist_entry = _fmt_pct(r.entry, r.last_close)
        dist_t1 = _fmt_pct(r.target_1, r.last_close)
        dist_t2 = _fmt_pct(r.target_2, r.last_close)
        dist_sl = _fmt_pct(r.stop_loss, r.last_close)
        # 入场类型说明
        entry_pct = float(dist_entry.replace("%","").replace("+","").replace("-",""))
        if abs(entry_pct) < 2:
            entry_type = " [现价附近入场]"
        elif entry_pct < 0:
            entry_type = " [等待回调入场]"
        else:
            entry_type = " [突破入场]"
        print(f"      入场: {r.entry:.2f} ({dist_entry}){entry_type}  止损: {r.stop_loss:.2f} ({dist_sl})")
        print(f"      目标1: {r.target_1:.2f} ({dist_t1})  目标2: {r.target_2:.2f} ({dist_t2})")
        print(f"      风险回报: {r.risk_reward:.1f}:1  仓位建议: {r.position_pct:.1f}%")

    # 入场条件 & 风险提示（推荐和观察都显示）
    conditions = _gen_entry_conditions(r)
    if conditions:
        print(f"      等待条件: {' | '.join(conditions)}")
    warnings = _gen_risk_warnings(r)
    if warnings:
        print(f"      风险提示: {' | '.join(warnings)}")

    if r.reasons:
        reasons_display = ", ".join(r.reasons[:5])
        print(f"      指标: {reasons_display}")


def get_summary_text(result: Dict) -> str:
    lines = [f"¥每日股票推荐 {result.get('date', '')}"]
    for market in ["A", "HK", "US"]:
        picks = result.get("picks", {}).get(market, [])
        if picks:
            names = [f"{p.code}({p.rating})" for p in picks[:3]]
            lines.append(f"  {MARKET_NAMES.get(market, market)}: {', '.join(names)}")
    return "\n".join(lines)
