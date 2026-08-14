#!/usr/bin/env python3
"""
股票买卖信号分析主脚本

支持美股 / A股 / 港股，输出标准化 5 级买卖评级

用法:
    python analyze_signals.py US.NVDA
    python analyze_signals.py US.NVDA --json
    python analyze_signals.py HK.00700 --timeframe 1w
    python analyze_signals.py SH.600519
"""
from __future__ import annotations

import sys
import os
import json
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from indicators import fetch_kline, compute_indicators, signal_summary
from scoring import (
    compute_rating, generate_signals,
    get_capital_data, get_short_data,
)
from _resonance import compute_timeframe_resonance
from _sr import compute_support_resistance, generate_trade_plan


def _color(text, color, bold=False):
    codes = {"red":31,"green":32,"yellow":33,"blue":34,"magenta":35,"cyan":36,"white":37}
    c = codes.get(color, "")
    if bold: c = f"1;{c}"
    return f"\033[{c}m{text}\033[0m" if c else text


def _bar(value, width=20):
    filled = int(width * value / 100)
    return "[" + "█" * filled + "░" * (width - filled) + f"] {value:.0f}"


def print_text_report(result, code):
    rating = result["rating"]
    score = result["score"]
    confidence = result["confidence"]
    rc_map = {"Buy":"green","Overweight":"green","Hold":"yellow","Underweight":"magenta","Sell":"red"}
    rc = rc_map.get(rating, "white")

    print()
    print("=" * 64)
    print(f"  {_color(code, 'cyan', True)}  技术分析 & 买卖信号")
    print(f"  时间: {result.get('timestamp', 'N/A')}")
    print("=" * 64)
    print()
    print(f"  {_color(f'评级: {rating}', rc, True)}")
    print(f"  综合得分: {_color(f'{score:.1f}/100', rc)}")
    print(f"  置信度: {_color(confidence, 'cyan')}")
    print()

    print("  各维度评分:")
    dims = result.get("dimensions", {})
    dim_order = ["trend", "momentum", "volume", "volatility", "capital"]
    dim_labels = {"trend":"趋势","momentum":"动量","volume":"量能","volatility":"波动率","capital":"资金面"}
    for dim in dim_order:
        d = dims.get(dim, {})
        ds = d.get("score", 50)
        dw = d.get("weight", 0.20)
        dr = d.get("reason", "")
        label = dim_labels.get(dim, dim)
        bc = "green" if ds >= 65 else ("red" if ds <= 35 else "yellow")
        print(f"    {_color(label+':', True)} {_bar(ds, 16)}  ({dw*100:.0f}%)")
        if dr and "不可用" not in dr and "跳过" not in dr:
            print(f"      {_color(dr, 'dim')}")
    print()

    ta = result.get("technical_analysis", {})
    print("  技术指标:")
    print(f"    最新价: {ta.get('last_close',0):.2f}  MA5={ta.get('ma5',0):.2f} MA10={ta.get('ma10',0):.2f} MA20={ta.get('ma20',0):.2f} MA60={ta.get('ma60',0):.2f}")
    print(f"    MACD: DIF={ta.get('macd_dif',0):.4f} DEA={ta.get('macd_dea',0):.4f} Hist={ta.get('macd_hist',0):.4f}")
    print(f"    RSI:  6={ta.get('rsi_6',0):.1f} 12={ta.get('rsi_12',0):.1f} 14={ta.get('rsi_14',0):.1f}")
    print(f"    KDJ:  K={ta.get('kdj_k',0):.1f} D={ta.get('kdj_d',0):.1f} J={ta.get('kdj_j',0):.1f}")
    print(f"    BOLL: 上={ta.get('boll_upper',0):.2f} 中={ta.get('boll_mid',0):.2f} 下={ta.get('boll_lower',0):.2f} 宽={ta.get('boll_width',0):.1f}%")
    print(f"    ATR:  {ta.get('atr_14',0):.2f}  量比={ta.get('vol_ratio',0):.2f}  OBV={ta.get('obv_trend','?')}")
    print()

    signals = result.get("signals", [])
    if signals:
        bullish = [s for s in signals if s["side"]=="bullish"]
        bearish = [s for s in signals if s["side"]=="bearish"]
        neutral = [s for s in signals if s["side"]=="neutral"]
        if bullish:
            print(f"    {_color(f'BUY 信号 ({len(bullish)}个):', 'green')}")
            for s in bullish:
                print(f"      + {s['desc']}")
        if bearish:
            print(f"    {_color(f'SELL 信号 ({len(bearish)}个):', 'red')}")
            for s in bearish:
                print(f"      - {s['desc']}")
        if neutral:
            print(f"    {_color(f'中性信号 ({len(neutral)}个):', 'yellow')}")
            for s in neutral:
                print(f"      ~ {s['desc']}")
        print()

    summary = result.get("summary", [])
    if summary:
        print("  信号摘要:")
        for dim, desc in summary:
            print(f"    [{dim}] {desc}")
        print()

    # Multi-timeframe resonance
    res = result.get("resonance")
    if res:
        print("  多时间框架共振")
        print(f"    日线: {res['daily_rating']} ({res['daily_score']:.1f})  周线: {res['weekly_rating']} ({res['weekly_score']:.1f})  月线: {res['monthly_rating']} ({res['monthly_score']:.1f})")
        align_colors = {"strong_up":"green","aligned":"green","strong_down":"red","aligned_down":"red","mixed":"yellow"}
        ac = align_colors.get(res["alignment"], "white")
        boost_str = f"+{res['confidence_boost']:.0f}" if res['confidence_boost'] > 0 else f"{res['confidence_boost']:.0f}"
        print(f"    共振状态: {_color(res['alignment'], ac)}  置信度调整: {boost_str}")
        print(f"    {_color(res['details'], 'dim')}")
        print()

    # Support/Resistance
    sr = result.get("support_resistance")
    if sr:
        print("  支撑/阻力位")
        r1, r2 = sr.get("resistance_1", 0), sr.get("resistance_2", 0)
        s1, s2 = sr.get("support_1", 0), sr.get("support_2", 0)
        vp = result.get("last_close", 0)
        print(f"    阻力2: {r2:.2f}  阻力1: {r1:.2f}  当前: {vp:.2f}  支撑1: {s1:.2f}  支撑2: {s2:.2f}")
        if r1 > 0 and vp > 0:
            print(f"      距阻力1: {((r1-vp)/vp*100):+.1f}%")
        if s1 > 0 and vp > 0:
            print(f"      距支撑1: {((s1-vp)/vp*100):+.1f}%")
        print()

    # Trend Phase
    tp = result.get("trend_phase")
    if tp:
        phase_labels = {
            "accumulation": "吸筹阶段", "early_rally": "上涨早期", "rally": "上涨阶段",
            "distribution": "派发阶段", "decline": "下跌阶段"
        }
        pl = phase_labels.get(tp, tp)
        print(f"  趋势阶段: {pl}")
        print()

    # Trade Plan
    tp_plan = result.get("trade_plan")
    if tp_plan and tp_plan.get("entry_zone", 0) > 0:
        print("  交易计划")
        print(f"    建议买入区间: {tp_plan['entry_zone']:.2f}")
        print(f"    止损位: {tp_plan['stop_loss']:.2f}  (风险: ${tp_plan['risk_usd']:.2f})")
        print(f"    目标1: {tp_plan['target_1']:.2f}  目标2: {tp_plan['target_2']:.2f}")
        rr = tp_plan['risk_reward_ratio']
        print(f"    风险收益比: {rr:.2f}:1  建议仓位: {tp_plan['position_size_pct']:.1f}%")
        print()

    print("  " + "-" * 60)
    print("  技术分析仅供参考，不构成投资建议")
    print("  请结合基本面、消息面综合判断")
    print("=" * 64)
    print()


def analyze(code, timeframe="1d", output_json=False):
    print(f"[1/4] 拉取 {code} {timeframe} K 线...", file=sys.stderr)
    df = fetch_kline(code, timeframe, num=300)
    if df.empty:
        result = {"error": f"无法获取 K 线数据: {code}", "code": code}
        if output_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"[ERROR] 无法获取 {code} 的 K 线数据", file=sys.stderr)
        return result

    print(f"[2/4] 计算技术指标...", file=sys.stderr)
    ind = compute_indicators(df, code, timeframe)

    print(f"[3/4] 获取资金/卖空数据...", file=sys.stderr)
    capital = get_capital_data(code)
    short_pct = get_short_data(code) if code.startswith(("US.", "HK.")) else None

    print(f"[4/4] 计算评级 & 生成信号...", file=sys.stderr)
    rating_result = compute_rating(ind, capital, short_pct)
    signals = generate_signals(ind, rating_result["rating"], capital, short_pct)
    summary = signal_summary(ind)


    # Multi-timeframe resonance
    resonance = compute_timeframe_resonance(code, ind, capital, short_pct)
    sr = compute_support_resistance(df)
    trend_phase = ind.trend_phase
    trade_plan = generate_trade_plan(ind, sr, trend_phase)

    result = {
        "code": code,
        "timeframe": timeframe,
        "timestamp": ind.last_time,
        "last_close": ind.last_close,
        "rating": rating_result["rating"],
        "score": rating_result["score"],
        "confidence": rating_result["confidence"],
        "dimensions": rating_result["dimensions"],
        "signals": signals,
        "summary": summary,
        "resonance": {
            "daily_rating": resonance.daily_rating,
            "weekly_rating": resonance.weekly_rating,
            "monthly_rating": resonance.monthly_rating,
            "daily_score": resonance.daily_score,
            "weekly_score": resonance.weekly_score,
            "monthly_score": resonance.monthly_score,
            "alignment": resonance.alignment,
            "confidence_boost": resonance.confidence_boost,
            "details": resonance.details,
        },
        "support_resistance": sr,
        "trade_plan": {
            "entry_zone": trade_plan.entry_zone,
            "stop_loss": trade_plan.stop_loss,
            "target_1": trade_plan.target_1,
            "target_2": trade_plan.target_2,
            "risk_reward_ratio": trade_plan.risk_reward,
            "risk_usd": trade_plan.risk_usd,
            "reward_usd": trade_plan.reward_usd,
            "position_size_pct": trade_plan.position_size_pct,
        },
        "trend_phase": trend_phase,
        "technical_analysis": {
            "last_close": ind.last_close, "prev_close": ind.prev_close,
            "last_time": ind.last_time,
            "ma5": ind.ma5, "ma10": ind.ma10, "ma20": ind.ma20,
            "ma60": ind.ma60, "ma120": ind.ma120, "ma200": ind.ma200,
            "macd_dif": ind.macd_dif, "macd_dea": ind.macd_dea, "macd_hist": ind.macd_hist,
            "rsi_6": ind.rsi_6, "rsi_12": ind.rsi_12, "rsi_14": ind.rsi_14, "rsi_24": ind.rsi_24,
            "kdj_k": ind.kdj_k, "kdj_d": ind.kdj_d, "kdj_j": ind.kdj_j,
            "boll_mid": ind.boll_mid, "boll_upper": ind.boll_upper,
            "boll_lower": ind.boll_lower, "boll_width": ind.boll_width,
            "atr_14": ind.atr_14,
            "obv_trend": ind.obv_trend, "vol_ratio": ind.vol_ratio, "vwma_20": ind.vwma_20,
            "ma5_ma10_cross": ind.ma5_ma10_cross == "golden",
            "macd_dif_dea_cross": ind.macd_dif_dea_cross == "golden",
        },
        "capital_flow": capital if capital else None,
        "short_interest_pct": short_pct,
    }

    if output_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text_report(result, code)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="股票技术分析 & 买卖信号生成器 (美股/A股/港股)")
    parser.add_argument("code", help="股票代码，如 US.NVDA / SH.600519 / HK.00700")
    parser.add_argument("--timeframe", "-t", default="1d",
                        choices=["1d", "1w", "1m"], help="K 线周期: 1d(默认) / 1w / 1m")
    parser.add_argument("--json", "-j", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--num", "-n", type=int, default=300, help="K 线根数（默认 300）")
    args = parser.parse_args()

    code = args.code.strip()
    if "." not in code:
        print(f"[ERROR] 股票代码格式错误: {code}，示例: US.NVDA / SH.600519 / HK.00700", file=sys.stderr)
        sys.exit(1)

    analyze(code, args.timeframe, args.json)


if __name__ == "__main__":
    main()
