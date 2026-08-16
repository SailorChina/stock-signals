# -*- coding: utf-8 -*-
"""Command-line interface for stock-signals"""
from __future__ import annotations

import sys
import os
import json
import argparse
import csv
import logging
from datetime import datetime
from typing import List, Optional

try:
    from stock_signals.indicators import fetch_kline, compute_indicators, signal_summary
    from stock_signals.scoring import (
        compute_rating, generate_signals,
        get_capital_data, get_short_data,
    )
    from stock_signals._resonance import compute_timeframe_resonance
    from stock_signals._sr import compute_support_resistance, generate_trade_plan
    from stock_signals.screener import scan, ScanConfig
    from stock_signals.reporter import print_scan_report
except ImportError:
    pass


def setup_logging(log_level="INFO", log_file=""):
    level = getattr(logging, log_level.upper(), logging.INFO)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handlers = [logging.StreamHandler(sys.stderr)]
    if log_file:
        h = logging.FileHandler(log_file, encoding="utf-8")
        h.setFormatter(fmt)
        handlers.append(h)
    logging.basicConfig(level=level, handlers=handlers)


logger = logging.getLogger("stock-signals")

# ── Rating color & Chinese label maps ──────────────────────────────
RC_COLOR = {"Buy": "green", "Overweight": "green", "Hold": "yellow",
            "Underweight": "magenta", "Sell": "red"}
RATING_CN = {"Buy": "买入", "Overweight": "偏多", "Hold": "观望",
             "Underweight": "偏空", "Sell": "卖出"}

# ── Confidence Chinese labels ──────────────────────────────────────
CONF_CN = {"high": "高", "medium": "中", "low": "低"}

# ── OBV trend Chinese labels ───────────────────────────────────────
OBV_CN = {"up": "上升", "down": "下降"}

# ── Resonance alignment colors & Chinese labels ────────────────────
ALIGN_COLOR = {"strong_up": "green", "aligned": "green", "mixed": "yellow",
               "aligned_down": "magenta", "strong_down": "red", "none": "white"}
ALIGN_CN = {"strong_up": "强共振看多", "aligned": "共振看多", "mixed": "分歧",
            "aligned_down": "共振看空", "strong_down": "强共振看空", "none": "无"}



def _color(text, color, bold=False):
    codes = {"red":31,"green":32,"yellow":33,"blue":34,"magenta":35,"cyan":36,"white":37}
    c = codes.get(color, "")
    if bold:
        c = f"1;{c}"
    return f"[{c}m{text}[0m" if c else text


def _bar(value, width=20):
    filled = int(width * value / 100)
    return "[" + chr(9608) * filled + chr(9617) * (width - filled) + f"] {value:.0f}"


def print_text_report(result, code):
    rating = result["rating"]
    score = result["score"]
    confidence = result["confidence"]
    rating_cn_label = RATING_CN.get(rating, "")
    rc = RC_COLOR.get(rating, "white")

    print()
    print("=" * 64)
    print(f"  {_color(code, 'cyan', True)}  技术分析 & 买卖信号")
    print(f"  时间: {result.get('timestamp', 'N/A')}")
    print("=" * 64)
    print()
    print(f"  {_color(f'评级: {rating}' + (f' ({rating_cn_label})' if rating_cn_label else ''), rc, True)}")
    print(f"  综合得分: {_color(f'{score:.1f}/100', rc)}")
    conf_cn = CONF_CN.get(confidence, "")
    print(f"  置信度: {_color(confidence + (f' ({conf_cn})' if conf_cn else ''), 'cyan')}")
    print()

    print("  各维度评分")
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
        if dr and "Unavailable" not in dr and "Skipped" not in dr:
            print(f"      {_color(dr, 'dim')}")
    print()

    ta = result.get("technical_analysis", {})
    print("  技术指标")
    print(f"    最新价: {ta.get('last_close',0):.2f}  MA5={ta.get('ma5',0):.2f} MA10={ta.get('ma10',0):.2f} MA20={ta.get('ma20',0):.2f} MA60={ta.get('ma60',0):.2f}")
    print(f"    MACD: DIF={ta.get('macd_dif',0):.4f} DEA={ta.get('macd_dea',0):.4f} Hist={ta.get('macd_hist',0):.4f}")
    print(f"    RSI:  6={ta.get('rsi_6',0):.1f} 12={ta.get('rsi_12',0):.1f} 14={ta.get('rsi_14',0):.1f}")
    print(f"    KDJ:  K={ta.get('kdj_k',0):.1f} D={ta.get('kdj_d',0):.1f} J={ta.get('kdj_j',0):.1f}")
    print(f"    BOLL: 上={ta.get('boll_upper',0):.2f} 中={ta.get('boll_mid',0):.2f} 下={ta.get('boll_lower',0):.2f} 宽={ta.get('boll_width',0):.1f}%")
    obv_v = ta.get('obv_trend','?'); obv_cn = OBV_CN.get(obv_v, obv_v)
    print(f"    ATR:  {ta.get('atr_14',0):.2f}  量比={ta.get('vol_ratio',0):.2f}  OBV={obv_cn}")
    # ADX
    adx = ta.get("adx", 0)
    pdi = ta.get("plus_di", 0)
    mdi = ta.get("minus_di", 0)
    if adx > 0:
        adx_c = "green" if adx > 40 else ("yellow" if adx > 25 else "dim")
        trend_dir = "多" if pdi > mdi else "空"
        print(f"    ADX:  {_color(f"{adx:.1f}", adx_c)}  +DI={pdi:.1f} -DI={mdi:.1f} ({trend_dir})")
    # Divergence
    macd_div = ta.get("macd_divergence", "none")
    rsi_div = ta.get("rsi_divergence", "none")
    if macd_div != "none":
        div_c = "red" if macd_div == "bearish" else "green"
        print(f"    MACD背离: {_color("顶背离" if macd_div == "bearish" else "底背离", div_c)}")
    if rsi_div != "none":
        div_c = "red" if rsi_div == "bearish" else "green"
        print(f"    RSI背离:  {_color("顶背离" if rsi_div == "bearish" else "底背离", div_c)}")
    # Candle pattern
    cp = ta.get("candle_pattern", "none")
    if cp != "none":
        print(f"    K线形态: {ta.get("candle_pattern_name", "")}")
    # Gap
    gap = ta.get("gap_pct", 0)
    if gap != 0 and abs(gap) > 0.01:
        gap_c = "green" if gap > 0 else "red"
        filled_str = "已回补" if ta.get("gap_filled", False) else "未回补"
        print(f"    缺口: {_color(f"{gap:+.1f}%", gap_c)} ({filled_str})")
    print()

    signals = result.get("signals", [])
    if signals:
        bullish = [s for s in signals if s["side"]=="bullish"]
        bearish = [s for s in signals if s["side"]=="bearish"]
        neutral = [s for s in signals if s["side"]=="neutral"]
        if bullish:
            print(f"    {_color(f'买入信号 ({len(bullish)}个):', 'green')}")
            for s in bullish:
                print(f"      + {s['desc']}")
        if bearish:
            print(f"    {_color(f'卖出信号 ({len(bearish)}个):', 'red')}")
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

    res = result.get("resonance")
    if res:
        print("  多时间框架共振")
        ac = ALIGN_COLOR.get(res["alignment"], "white")

        _dr=res["daily_rating"]; _wr=res["weekly_rating"]; _mr=res["monthly_rating"]
        _dc=RATING_CN.get(_dr,""); _wc=RATING_CN.get(_wr,""); _mc=RATING_CN.get(_mr,"")
        _ds=res["daily_score"]; _ws=res["weekly_score"]; _ms=res["monthly_score"]
        print(f"    日线: {_dr}" + (f" ({_dc})" if _dc else "") + f" ({_ds:.1f})  周线: {_wr}" + (f" ({_wc})" if _wc else "") + f" ({_ws:.1f})  月线: {_mr}" + (f" ({_mc})" if _mc else "") + f" ({_ms:.1f})")
        boost = res["confidence_boost"]
        align_cn = ALIGN_CN.get(res['alignment'], '')
        print(f"    共振: {_color(res['alignment'] + (f' ({align_cn})' if align_cn else ''), ac)}  置信度调整: { '+' if boost>=0 else ''}{boost:.0f}")
        if res.get("details"):
            print(f"    {_color(res['details'], 'dim')}")
        print()

    sr = result.get("support_resistance")
    if sr:
        print("  支撑 / 阻力位")
        print(f"    阻力1: {sr['resistance_1']:.2f}  阻力2: {sr['resistance_2']:.2f}")
        print(f"    支撑1: {sr['support_1']:.2f}  支撑2: {sr['support_2']:.2f}")
        print(f"    VWAP(20): {sr.get('vwap',0):.2f}")
        cur = result.get("last_close", 0)
        if cur > 0:
            for label, val in [("阻力1","resistance_1"),("阻力2","resistance_2"),("支撑1","support_1"),("支撑2","support_2"),("VWAP","vwap")]:
                if val in sr and sr[val] > 0:
                    dist = (sr[val] - cur) / cur * 100
                    print(f"      {label}: {dist:+.1f}%")
        print()

    tp = result.get("trade_plan")
    if tp and tp.get("entry_zone", 0) > 0:
        print("  交易计划")
        print(f"    建议入场: {tp['entry_zone']:.2f}")
        print(f"    止损位:   {tp['stop_loss']:.2f}")
        print(f"    第一目标: {tp['target_1']:.2f}")
        print(f"    第二目标: {tp['target_2']:.2f}")
        rr = tp.get("risk_reward", 0)
        rr_c = "green" if rr >= 2 else ("yellow" if rr >= 1 else "red")
        print(f"    风险收益比: {_color(f'{rr:.2f}:1', rr_c)}")
        print(f"    建议仓位:   {tp['position_size_pct']:.1f}%")
        print()

    # 波动率市况
    vol_regime = ta.get("vol_regime", "normal")
    regime_labels = {"low": "低波震荡市", "normal": "正常市况", "high": "高波趋势市"}
    regime_colors = {"low": "yellow", "normal": "cyan", "high": "magenta"}
    rc = regime_colors.get(vol_regime, "white")
    print(f"  市况分类: {_color(regime_labels.get(vol_regime, vol_regime), rc)}  (ATR%={ta.get("atr_14_pct", 0):.2f}%)")
    print()

    trend = result.get("trend_phase")
    if trend:
        phase_colors = {"accumulation":"yellow","early_rally":"green","rally":"green","distribution":"magenta","decline":"red"}
        pc = phase_colors.get(trend, "white")
        phase_labels = {"accumulation":"吸筹阶段","early_rally":"上涨早期","rally":"上涨","distribution":"派发","decline":"下跌"}
        print(f"  趋势阶段: {_color(phase_labels.get(trend, trend), pc)}")
        print()
    print("=" * 64)
    print()


def analyze(code, timeframe="1d", output_json=False):
    logger.info(f"分析 {code} {timeframe}...")
    df = fetch_kline(code, timeframe, num=300)
    if df.empty:
        result = {"error": f"无法获取 K 线数据: {code}", "code": code}
        if output_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.error(f"无法获取 {code}")
        return result

    logger.info("计算技术指标...")
    ind = compute_indicators(df, code, timeframe)

    logger.info("获取资金/卖空数据...")
    capital = get_capital_data(code)
    short_pct = get_short_data(code) if code.startswith(("US.", "HK.")) else None

    logger.info("计算评级 & 生成信号...")
    rating_result = compute_rating(ind, capital, short_pct)
    signals = generate_signals(ind, rating_result["rating"], capital, short_pct)
    summary = signal_summary(ind)

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
            "atr_14": ind.atr_14, "atr_14_pct": ind.atr_14_pct,
            "obv_trend": ind.obv_trend, "vol_ratio": ind.vol_ratio, "vwma_20": ind.vwma_20,
            "adx": ind.adx, "plus_di": ind.plus_di, "minus_di": ind.minus_di,
            "macd_divergence": ind.macd_divergence,
            "rsi_divergence": ind.rsi_divergence,
            "candle_pattern": ind.candle_pattern,
            "candle_pattern_name": ind.candle_pattern_name,
            "gap_pct": ind.gap_pct,
            "gap_type": ind.gap_type,
            "gap_filled": ind.gap_filled,
            "vol_regime": ind.vol_regime,
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


def batch_analyze(codes, timeframe="1d", output_csv=None, output_json=False):
    results = []
    for code in codes:
        code = code.strip()
        if not code or "." not in code:
            logger.warning(f"跳过无效代码: {code}")
            continue
        try:
            r = analyze(code, timeframe, output_json=False)
            results.append(r)
        except Exception as e:
            logger.error(f"分析失败: {code}: {e}")
            results.append({"error": str(e), "code": code})
    if output_csv:
        _export_csv(results, output_csv)
    return results


def _export_csv(results, path):
    if not results:
        return
    fieldnames = ["code", "timeframe", "timestamp", "rating", "score", "confidence",
                  "trend_score", "momentum_score", "volume_score", "volatility_score", "capital_score",
                  "resonance_alignment", "trend_phase",
                  "entry_zone", "stop_loss", "target_1", "target_2", "risk_reward_ratio",
                  "resistance_1", "support_1"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            dims = r.get("dimensions", {})
            row = {
                "code": r.get("code", ""),
                "timeframe": r.get("timeframe", ""),
                "timestamp": r.get("timestamp", ""),
                "rating": r.get("rating", ""),
                "score": r.get("score", ""),
                "confidence": r.get("confidence", ""),
                "trend_score": dims.get("trend", {}).get("score", ""),
                "momentum_score": dims.get("momentum", {}).get("score", ""),
                "volume_score": dims.get("volume", {}).get("score", ""),
                "volatility_score": dims.get("volatility", {}).get("score", ""),
                "capital_score": dims.get("capital", {}).get("score", ""),
                "resonance_alignment": r.get("resonance", {}).get("alignment", ""),
                "trend_phase": r.get("trend_phase", ""),
                "entry_zone": r.get("trade_plan", {}).get("entry_zone", ""),
                "stop_loss": r.get("trade_plan", {}).get("stop_loss", ""),
                "target_1": r.get("trade_plan", {}).get("target_1", ""),
                "target_2": r.get("trade_plan", {}).get("target_2", ""),
                "risk_reward_ratio": r.get("trade_plan", {}).get("risk_reward_ratio", ""),
                "resistance_1": r.get("support_resistance", {}).get("resistance_1", ""),
                "support_1": r.get("support_resistance", {}).get("support_1", ""),
            }
            writer.writerow(row)
    logger.info(f"CSV 已导出: {path} ({len(results)} rows)")


def main():
    parser = argparse.ArgumentParser(description="股票技术分析 & 买卖信号生成器 (美股/A股/港股)")

    # Subcommands
    sub = parser.add_subparsers(dest="cmd")

    # --- analyze subcommand ---
    p_analyze = sub.add_parser("analyze", help="分析单只/多只股票")
    p_analyze.add_argument("codes", nargs="+", help="股票代码，如 US.NVDA / SH.600519 / HK.00700")
    p_analyze.add_argument("--timeframe", "-t", default="1d", choices=["1d", "1w", "1m"])
    p_analyze.add_argument("--json", "-j", action="store_true", help="JSON output")
    p_analyze.add_argument("--num", "-n", type=int, default=300, help="K线根数")
    p_analyze.add_argument("--csv", "-c", type=str, help="导出 CSV")
    p_analyze.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"])
    p_analyze.add_argument("--log-file", type=str, help="日志文件路径")
    p_analyze.add_argument("--config", type=str, help="配置文件路径(JSON)")

    # --- scan subcommand ---
    p_scan = sub.add_parser("scan", help="扫描多市场推荐股票")
    p_scan.add_argument("--markets", "-m", default="A,US,HK", help="市场: A,US,HK")
    p_scan.add_argument("--min-score", type=float, default=60.0, help="最低评分门槛")
    p_scan.add_argument("--max-picks", type=int, default=3, help="每市场最多推荐数")
    p_scan.add_argument("--delay", type=float, default=0.5, help="请求间隔(秒)")
    p_scan.add_argument("--json", "-j", action="store_true", help="JSON output")
    p_scan.add_argument("--output", "-o", type=str, help="保存结果到文件")
    p_scan.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"])
    p_scan.add_argument("--log-file", type=str, help="日志文件路径")

    args = parser.parse_args()

    if not args.cmd:
        parser.print_help()
        sys.exit(0)

    setup_logging(getattr(args, "log_level", "INFO"), getattr(args, "log_file", ""))
    logger.info("stock-signals v2.4.0 启动")

    if args.cmd == "scan":
        # Interactive market selection
        markets_input = getattr(args, "markets", None)
        if markets_input:
            markets = [m.strip() for m in markets_input.split(",")]
        else:
            print()
            print("  请选择扫描市场:")
            print("  [1] A股（沪深核心龙头）")
            print("  [2] 港股（恒生+恒生科技）")
            print("  [3] 美股（道指+标普500+纳指）")
            print("  [4] 全部市场")
            print()
            choice = input("  输入选项 (1/2/3/4): ").strip()
            market_map = {"1": ["A"], "2": ["HK"], "3": ["US"], "4": ["A", "HK", "US"]}
            markets = market_map.get(choice, ["A"])
            print(f"  已选择: {markets}")
            print()

        cfg = ScanConfig(
            min_score=args.min_score,
            max_per_market=args.max_picks,
            max_delay=args.delay,
        )
        result = scan(markets=markets, config=cfg, output_json=args.json, output_file=getattr(args, "output", ""))
        if not args.json:
            print_scan_report(result)
        sys.exit(0)

    # analyze mode
    for code in args.codes:
        code = code.strip()
        if "." not in code:
            logger.error(f"股票代码格式错误: {code}，示例: US.NVDA / SH.600519 / HK.00700")
            sys.exit(1)
        analyze(code, args.timeframe, args.json)

    if getattr(args, "csv", None):
        logger.warning("--csv 需要多只股票批量模式")

if __name__ == "__main__":
    main()
