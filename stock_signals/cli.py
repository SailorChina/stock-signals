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
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from indicators import fetch_kline, compute_indicators, signal_summary
    from scoring import (
        compute_rating, generate_signals,
        get_capital_data, get_short_data,
    )
    from _resonance import compute_timeframe_resonance
    from _sr import compute_support_resistance, generate_trade_plan


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
    rc_map = {"Buy":"green","Overweight":"green","Hold":"yellow","Underweight":"magenta","Sell":"red"}
    rc = rc_map.get(rating, "white")

    print()
    print("=" * 64)
    print(f"  {_color(code, 'cyan', True)}  Technical Analysis and Signals")
    print(f"  Time: {result.get('timestamp', 'N/A')}")
    print("=" * 64)
    print()
    print(f"  {_color(f'Rating: {rating}', rc, True)}")
    print(f"  Score: {_color(f'{score:.1f}/100', rc)}")
    print(f"  Confidence: {_color(confidence, 'cyan')}")
    print()

    print("  Dimension Scores")
    dims = result.get("dimensions", {})
    dim_order = ["trend", "momentum", "volume", "volatility", "capital"]
    dim_labels = {"trend":"Trend","momentum":"Momentum","volume":"Volume","volatility":"Volatility","capital":"Capital"}
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
    print("  Technical Indicators")
    print(f"    Price: {ta.get('last_close',0):.2f}  MA5={ta.get('ma5',0):.2f} MA10={ta.get('ma10',0):.2f} MA20={ta.get('ma20',0):.2f} MA60={ta.get('ma60',0):.2f}")
    print(f"    MACD: DIF={ta.get('macd_dif',0):.4f} DEA={ta.get('macd_dea',0):.4f} Hist={ta.get('macd_hist',0):.4f}")
    print(f"    RSI:  6={ta.get('rsi_6',0):.1f} 12={ta.get('rsi_12',0):.1f} 14={ta.get('rsi_14',0):.1f}")
    print(f"    KDJ:  K={ta.get('kdj_k',0):.1f} D={ta.get('kdj_d',0):.1f} J={ta.get('kdj_j',0):.1f}")
    print(f"    BOLL: U={ta.get('boll_upper',0):.2f} M={ta.get('boll_mid',0):.2f} L={ta.get('boll_lower',0):.2f} W={ta.get('boll_width',0):.1f}%")
    print(f"    ATR:  {ta.get('atr_14',0):.2f}  VolRatio={ta.get('vol_ratio',0):.2f}  OBV={ta.get('obv_trend','?')}")
    print()

    signals = result.get("signals", [])
    if signals:
        bullish = [s for s in signals if s["side"]=="bullish"]
        bearish = [s for s in signals if s["side"]=="bearish"]
        neutral = [s for s in signals if s["side"]=="neutral"]
        if bullish:
            print(f"    {_color(f'BUY signals ({len(bullish)}):', 'green')}")
            for s in bullish:
                print(f"      + {s['desc']}")
        if bearish:
            print(f"    {_color(f'SELL signals ({len(bearish)}):', 'red')}")
            for s in bearish:
                print(f"      - {s['desc']}")
        if neutral:
            print(f"    {_color(f'Neutral ({len(neutral)}):', 'yellow')}")
            for s in neutral:
                print(f"      ~ {s['desc']}")
        print()

    summary = result.get("summary", [])
    if summary:
        print("  Signal Summary:")
        for dim, desc in summary:
            print(f"    [{dim}] {desc}")
        print()

    res = result.get("resonance")
    if res:
        print("  Multi-Timeframe Resonance")
        align_colors = {"strong_up":"green","aligned":"green","mixed":"yellow","aligned_down":"magenta","strong_down":"red","none":"white"}
        ac = align_colors.get(res["alignment"], "white")
        print(f"    Daily: {res['daily_rating']} ({res['daily_score']:.1f})  Weekly: {res['weekly_rating']} ({res['weekly_score']:.1f})  Monthly: {res['monthly_rating']} ({res['monthly_score']:.1f})")
        print(f"    Alignment: {_color(res['alignment'], ac)}  Confidence boost: { '+' if res['confidence_boost']>=0 else ''}{res['confidence_boost']:.0f}")
        if res.get("details"):
            print(f"    {_color(res['details'], 'dim')}")
        print()

    sr = result.get("support_resistance")
    if sr:
        print("  Support / Resistance")
        print(f"    R1: {sr['resistance_1']:.2f}  R2: {sr['resistance_2']:.2f}")
        print(f"    S1: {sr['support_1']:.2f}  S2: {sr['support_2']:.2f}")
        print(f"    VWAP(20): {sr.get('vwap',0):.2f}")
        cur = result.get("last_close", 0)
        if cur > 0:
            for label, val in [("R1","resistance_1"),("R2","resistance_2"),("S1","support_1"),("S2","support_2"),("VWAP","vwap")]:
                if val in sr and sr[val] > 0:
                    dist = (sr[val] - cur) / cur * 100
                    print(f"      {label}: {dist:+.1f}%")
        print()

    tp = result.get("trade_plan")
    if tp and tp.get("entry_zone", 0) > 0:
        print("  Trade Plan")
        print(f"    Entry:    {tp['entry_zone']:.2f}")
        print(f"    Stop:     {tp['stop_loss']:.2f}")
        print(f"    Target1:  {tp['target_1']:.2f}")
        print(f"    Target2:  {tp['target_2']:.2f}")
        rr = tp.get("risk_reward_ratio", 0)
        rr_c = "green" if rr >= 2 else ("yellow" if rr >= 1 else "red")
        print(f"    R:R ratio: {_color(f'{rr:.2f}:1', rr_c)}")
        print(f"    Position:  {tp['position_size_pct']:.1f}%")
        print()

    trend = result.get("trend_phase")
    if trend:
        phase_colors = {"accumulation":"yellow","early_rally":"green","rally":"green","distribution":"magenta","decline":"red"}
        pc = phase_colors.get(trend, "white")
        print(f"  Trend Phase: {_color(trend, pc)}")
        print()
    print("=" * 64)
    print()


def analyze(code, timeframe="1d", output_json=False):
    logger.info(f"Analyzing {code} {timeframe}...")
    df = fetch_kline(code, timeframe, num=300)
    if df.empty:
        result = {"error": f"Cannot fetch K-line data: {code}", "code": code}
        if output_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            logger.error(f"Cannot get K-line data for {code}")
        return result

    logger.info("Computing indicators...")
    ind = compute_indicators(df, code, timeframe)

    logger.info("Fetching capital/short data...")
    capital = get_capital_data(code)
    short_pct = get_short_data(code) if code.startswith(("US.", "HK.")) else None

    logger.info("Computing rating and signals...")
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


def batch_analyze(codes, timeframe="1d", output_csv=None, output_json=False):
    results = []
    for code in codes:
        code = code.strip()
        if not code or "." not in code:
            logger.warning(f"Skipping invalid code: {code}")
            continue
        try:
            r = analyze(code, timeframe, output_json=False)
            results.append(r)
        except Exception as e:
            logger.error(f"Analysis failed for {code}: {e}")
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
    logger.info(f"CSV exported: {path} ({len(results)} rows)")


def main():
    parser = argparse.ArgumentParser(description="Stock Technical Analysis and Signal Generator (US/A/HK)")
    parser.add_argument("codes", nargs="+", help="Stock codes, e.g. US.NVDA / SH.600519 / HK.00700")
    parser.add_argument("--timeframe", "-t", default="1d", choices=["1d", "1w", "1m"])
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--num", "-n", type=int, default=300, help="K-line count (default 300)")
    parser.add_argument("--csv", "-c", type=str, help="Export results to CSV")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG","INFO","WARNING","ERROR"])
    parser.add_argument("--log-file", type=str, help="Log file path")
    parser.add_argument("--config", type=str, help="Config file path (JSON)")
    args = parser.parse_args()

    setup_logging(args.log_level, args.log_file)
    logger.info("stock-signals v2.1.0 started")

    for code in args.codes:
        code = code.strip()
        if "." not in code:
            logger.error(f"Invalid code format: {code}, expected e.g. US.NVDA / SH.600519 / HK.00700")
            sys.exit(1)
        analyze(code, args.timeframe, args.json)

    if args.csv:
        logger.warning("--csv requires batch mode with multiple codes")


if __name__ == "__main__":
    main()
