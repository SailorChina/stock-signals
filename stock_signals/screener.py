# -*- coding: utf-8 -*-
"""股票筛选引擎 — 多市场扫描 + 智能选股"""
from __future__ import annotations

import sys
import os as _os
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional

sys.path.insert(0, r'C:\Users\Administrator\.codex\skills\futuapi\scripts')

from .indicators import fetch_kline, compute_indicators, signal_summary
from .scoring import compute_rating, RATINGS
from ._resonance import compute_timeframe_resonance
from ._sr import compute_support_resistance, generate_trade_plan
from ._vcp import detect_vcp
from ._episodic_pivot import detect_episodic_pivot
from .config import config


logger = logging.getLogger("stock-signals")

# ─────────────────────────────────────────────────────────────────────
# 股票池（指数成分股精选）
# ─────────────────────────────────────────────────────────────────────

STOCK_POOLS: Dict[str, List[str]] = {
    # ── A 股：沪深 300 + 核心龙头 ─────────────────────────────────
    "SH": [
        "SH.600519", "SH.601318", "SH.601398", "SH.601288", "SH.601166",
        "SH.600030", "SH.600036", "SH.601818", "SH.601881",
        # 消费
        "SH.600887", "SH.603288", "SH.603259", "SH.600085",
        "SH.603899", "SH.600104", "SH.603160",
        # 科技 / 半导体
        "SH.688981", "SH.688012", "SH.688396", "SH.688111",
        "SH.600584", "SH.603501", "SH.688256",
        # 新能源 / 光伏
        "SH.601012", "SH.601865", "SH.600438", "SH.600460",
        "SH.603010", "SH.688599",
        # 医药
        "SH.600276", "SH.600196", "SH.600572",
        # 周期 / 资源
        "SH.600028", "SH.600026", "SH.601088", "SH.601857",
        "SH.600309", "SH.600585",
        # 地产 / 基建
        "SH.600048", "SH.601155", "SH.600000",
    ],
    "SZ": [
        "SZ.000001", "SZ.000002", "SZ.002142", "SZ.000776",
        # 消费
        "SZ.000858", "SZ.002304", "SZ.002557", "SZ.002714",
        "SZ.000063", "SZ.002415", "SZ.002475",
        # 科技 / 电子
        "SZ.300750", "SZ.300014", "SZ.300124", "SZ.300308",
        "SZ.300408", "SZ.002371", "SZ.002439", "SZ.002236",
        # 新能源
        "SZ.002594", "SZ.002460", "SZ.002459",
        # 医药
        "SZ.300015", "SZ.000661", "SZ.300122", "SZ.002007",
        "SZ.300760",
        # 制造 / 工业
        "SZ.000333", "SZ.000651", "SZ.000725",
    ],
    # ── 港股：恒生指数 + 恒生科技 ────────────────────────────────
    "HK": [
        # 互联网 / 科技
        "HK.00700", "HK.09988", "HK.03690", "HK.09618",
        "HK.09888", "HK.02382", "HK.09999", "HK.09660",
        "HK.02015", "HK.02359",
        "HK.00005", "HK.02388", "HK.03968", "HK.00939",
        "HK.01288", "HK.03988",
        # 消费 / 餐饮
        "HK.00686", "HK.00291", "HK.00322", "HK.01071",
        "HK.09922",
        # 新能源 / 汽车
        "HK.09866", "HK.09961",
        # 地产 / 综合
        "HK.00012", "HK.00001", "HK.00003",
        # 电信 / 能源
        "HK.00006", "HK.00009", "HK.00883",
    ],
    # ── 美股：道指 + 标普 500 + 纳指 100 精选 ────────────────────
    "US": [
        # 科技
        "US.NVDA", "US.AAPL", "US.MSFT", "US.GOOG", "US.AMZN",
        "US.META", "US.TSLA", "US.AVGO", "US.CSCO", "US.ORCL",
        "US.AMAT", "US.LRCX", "US.ASML",
        "US.INTC", "US.QCOM", "US.MU", "US.NXPI",
        "US.MCD", "US.NKE", "US.TGT", "US.KO", "US.PEP",
        "US.WMT", "US.COST",
        # 医药
        "US.JNJ", "US.PFE", "US.UNH", "US.LLY", "US.ABBV",
        "US.MRK", "US.BMY", "US.AMGN", "US.GILD",
        # 工业 / 周期
        "US.HON", "US.CAT", "US.BA", "US.DE",
        "US.FCX", "US.NEM", "US.CP",
        # 能源
        "US.XOM", "US.COP", "US.OXY",
    ],
}
MARKET_NAMES = {
    "SH": "A股\u30fb\u6caa", "SZ": "A股\u30fb\u6df1",
    "HK": "\u9999\u6e2f", "US": "\u7f8e\u80a1", "A": "A\u80a1",
}

RATING_ORDER = {"Buy": 0, "Overweight": 1, "Hold": 2, "Underweight": 3, "Sell": 4}


@dataclass
class ScanConfig:
    """\u626b\u63cf\u914d\u7f6e"""
    min_score: float = 60.0
    watchlist_min: float = 55.0
    strong_score: float = 65.0
    min_alignment: str = "aligned"
    preferred_phases: tuple = ("accumulation", "early_rally", "rally")
    require_golden_cross: bool = True
    require_macd_cross: bool = False
    allow_td_buy: bool = True
    allow_oversold: bool = False
    max_delay: float = 1.0
    max_per_market: int = 5


@dataclass
class ScanResult:
    code: str
    market: str
    score: float
    rating: str
    alignment: str
    trend_phase: str
    entry: float = 0.0
    stop_loss: float = 0.0
    target_1: float = 0.0
    target_2: float = 0.0
    risk_reward: float = 0.0
    position_pct: float = 0.0
    last_close: float = 0.0
    reasons: List[str] = field(default_factory=list)
    trade_plan: Optional[dict] = None
    pullback_score: int = 0


def _analyze_one(code, capital=None, short_pct=None, delay=1.0):

    try:
        time.sleep(delay)
        df = fetch_kline(code, "1d", num=300)
        time.sleep(0.8)
        if df is None or df.empty or len(df) < 60:
            return None
        ind = compute_indicators(df, code, "1d")
        rating = compute_rating(ind, capital, short_pct)
        time.sleep(0.8)
        score = rating["score"]
        r_name = rating["rating"]
        resonance = compute_timeframe_resonance(code, ind, capital, short_pct)
        time.sleep(0.8)
        from ._sr import compute_trend_phase
        try:
            phase = compute_trend_phase(df, ind)
        except Exception:
            phase = "unknown"
        sr = compute_support_resistance(df)
        vcp_res = detect_vcp(df, lookback=100)
        ep_res = detect_episodic_pivot(df, lookback=60)
        tp = generate_trade_plan(ind, sr, phase, vcp_res)
        # v2.5: VCP 模式增强 - 成交量确认
        if vcp_res.detected and not vcp_res.volume_drying:
            logger.warning(f"  {code} VCP模式但成交量未萎缩，跳过")
            return None
        # v2.4: 扩展度过滤 - 距高点太近则跳过
        dist_to_high = getattr(ind, 'price_to_high_pct', 0)
        if dist_to_high > -8:
            logger.warning(f"  {code} 距高点仅{abs(dist_to_high):.1f}%，跳过(追高风险)")
            return None
        # v2.4.1: 风险收益比硬过滤(RR<2.0跳过)
        rr = getattr(tp, "risk_reward", 0) if tp else 0
        if rr < 2.0:
            logger.warning(f"  {code} RR={rr:.2f}:1 不足2:1，跳过")
            return None
        # v2.4.2: TD卖出Turn确认 → 卖出信号，跳过
        if getattr(ind, 'td_turn', '') == 'sell_turn':
            logger.warning(f"  {code} TD卖出Turn确认，看跌反转，跳过")
            return None
        # v2.4.2: MACD看跌背离 → 动量衰竭，跳过
        if getattr(ind, 'macd_divergence', '') == 'bearish':
            logger.warning(f"  {code} MACD看跌背离，动量衰竭，跳过")
            return None
        # v2.4.2: 看跌K线形态 → 短期回调风险，跳过
        if getattr(ind, 'candle_pattern', '') in ('bearish_engulfing', 'shooting_star'):
            logger.warning(f"  {code} K线形态{ind.candle_pattern_name}，看跌，跳过")
            return None
        # v2.4: MA5与MA20过度延伸检查
        ma_gap = getattr(ind, 'ma5_ma20_gap', 0)
        if ma_gap > 8:
            logger.warning(f"  {code} MA5偏离MA20 {ma_gap:.1f}%，过度延伸，跳过")
            return None
        reasons = []
        pullback_score = 0
        # v2.4: RSI极端超买硬过滤
        if getattr(ind, "rsi_14", 50) > 75:
            logger.warning(f"  {code} RSI={ind.rsi_14:.1f} 极端超买，跳过")
            return None
        if -15 <= dist_to_high <= -5 and ind.rsi_14 < 65:
            pullback_score = 5  # 回调到位 + RSI不超买
        elif -30 <= dist_to_high <= -15 and ind.rsi_14 < 55:
            pullback_score = 10  # 健康回调 + RSI中性
        if pullback_score > 0:
            reasons.append(f"回调入场机会(距高点{dist_to_high:.1f}%)")
        if ind.ma5_ma10_cross == "golden":
            reasons.append("MA5/MA10 \u91d1\u53c9")
        if ind.macd_dif_dea_cross == "golden":
            reasons.append("MACD \u91d1\u53c9")
        if ind.td_buy_setup:
            reasons.append("\u0039\u8f6c\u4e70\u5165\u5e8f\u5217\u5b8c\u6210")
        elif ind.td_buy_count > 0:
            reasons.append(f"\u0039\u8f6c\u4e70\u5165\u8fdb\u884c\u4e2d({ind.td_buy_count}/9)")
        if ind.vol_regime == "low":
            reasons.append("\u4f4e\u6ce2\u52a8\u7387\uff0c\u9707\u8361\u7b79\u5e95")
        if ind.vol_regime == "high":
            reasons.append("\u9ad8\u6ce2\u52a8\u7387\uff0c\u8d8b\u52bf\u660e\u663e")
        if ind.obv_trend == "up":
            reasons.append("OBV \u4e0a\u5347\uff0c\u8d44\u91d1\u6d41\u5165")
        if ep_res.detected:
            reasons.append(f"事件性转折(跳空{ep_res.gap_up_pct:.1f}%+成交量{ep_res.volume_spike:.1f}x)")
        if tp and tp.risk_reward >= 2.0:
            reasons.append(f"\u98ce\u9669\u6536\u76ca\u6bd4 {tp.risk_reward:.1f}:1")
        return ScanResult(
            code=code, market=_code_market(code), score=score, rating=r_name,
            alignment=resonance.alignment, trend_phase=phase,
            entry=tp.entry_zone if tp else 0.0,
            stop_loss=tp.stop_loss if tp else 0.0,
            target_1=tp.target_1 if tp else 0.0,
            target_2=tp.target_2 if tp else 0.0,
            risk_reward=tp.risk_reward if tp else 0.0,
            position_pct=tp.position_size_pct if tp else 0.0,
            last_close=ind.last_close, reasons=reasons,
            trade_plan={
                "entry": tp.entry_zone if tp else 0.0,
                "stop_loss": tp.stop_loss if tp else 0.0,
                "target_1": tp.target_1 if tp else 0.0,
                "target_2": tp.target_2 if tp else 0.0,
                "risk_reward": tp.risk_reward if tp else 0.0,
                "position_pct": tp.position_size_pct if tp else 0.0,
            } if tp else None,
        )
    except Exception as e:
        err_str = str(e)
        if "频率" in err_str or "rate" in err_str.lower() or "limit" in err_str.lower():
            wait = delay * 2
            logger.warning(f"  {code} 触发API限流，等待 {wait:.1f}s 后重试...")
            time.sleep(wait)
            return _analyze_one(code, delay=delay * 1.5)
        logger.warning(f"  分析 {code} 失败: {e}")
        return None


def _code_market(code):
    if code.startswith("SH") or code.startswith("SZ"):
        return "A"
    elif code.startswith("HK"):
        return "HK"
    elif code.startswith("US"):
        return "US"
    return "unknown"


def scan(markets=None, config=None, output_json=False, output_file=""):
    if config is None:
        config = ScanConfig()
    if markets is None:
        markets = ["A", "HK", "US"]
    picks = {m: [] for m in markets}
    watchlist = {m: [] for m in markets}
    total_analyzed = 0
    total_failed = 0
    logger.info(f"\u5f00\u59cb\u626b\u63cf {markets} \u5e02\u573a...")
    for market in markets:
        market_codes = _get_market_codes(market)
        logger.info(f"  {MARKET_NAMES.get(market, market)}: {len(market_codes)} \u53ea\u5019\u9009")
        for code in market_codes:
            result = _analyze_one(code, delay=config.max_delay)
            total_analyzed += 1
            if result is None:
                total_failed += 1
                continue
            if result.score < config.watchlist_min:
                continue
            entry = picks if result.score >= config.min_score else watchlist
            entry[market].append(result)
            if len(picks[market]) > config.max_per_market * 3:
                picks[market] = picks[market][:config.max_per_market * 3]
        picks[market] = _sort_results(picks[market])
        watchlist[market] = _sort_results(watchlist[market])
    final_picks = {m: picks[m][:config.max_per_market] for m in markets}
    final_watch = {m: watchlist[m][:config.max_per_market] for m in markets}
    total_picks = sum(len(v) for v in final_picks.values())
    total_watch = sum(len(v) for v in final_watch.values())
    summary = {
        "scan_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_analyzed": total_analyzed,
        "total_failed": total_failed,
        "total_picks": total_picks,
        "total_watchlist": total_watch,
        "markets_scanned": markets,
    }
    output = {
        "date": time.strftime("%Y-%m-%d"),
        "summary": summary,
        "picks": final_picks,
        "watchlist": final_watch,
    }
    if output_json or output_file:
        import json
        json_output = json.dumps(_serialize(output), ensure_ascii=False, indent=2)
        if output_json:
            print(json_output)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_output)
            logger.info(f"\u7ed3\u679c\u5df2\u4fdd\u5b58\u5230 {output_file}")
    logger.info(
        f"\u626b\u63cf\u5b8c\u6210: \u5206\u6790 {total_analyzed} \u53ea, \u5931\u8d25 {total_failed} \u53ea, "
        f"\u63a8\u8350 {total_picks} \u53ea, \u89c2\u5bdf {total_watch} \u53ea"
    )
    return output


def _get_market_codes(market):
    if market == "A":
        codes = []
        for prefix in ("SH", "SZ"):
            codes.extend(STOCK_POOLS.get(prefix, []))
        return codes
    return STOCK_POOLS.get(market, [])


def _sort_results(results):
    alignment_score = {
        "strong_up": 4, "aligned": 3, "mixed": 2,
        "aligned_down": 1, "strong_down": 0, "none": -1,
    }
    phase_score = {
        "accumulation": 3, "early_rally": 4, "rally": 5,
        "distribution": 1, "decline": 0, "unknown": 2,
    }
    # v2.4: 排序优先拉回入场机会(pullback_score) + 评分 + 共振
    return sorted(results, key=lambda r: (
        r.pullback_score,
        r.score,
        alignment_score.get(r.alignment, 0),
        phase_score.get(r.trend_phase, 0),
    ), reverse=True)


def _serialize(obj):
    import json
    if isinstance(obj, ScanResult):
        return {
            "code": obj.code, "score": obj.score, "rating": obj.rating,
            "pullback_score": obj.pullback_score,
            "alignment": obj.alignment, "trend_phase": obj.trend_phase,
            "last_close": obj.last_close, "entry": obj.entry,
            "stop_loss": obj.stop_loss, "target_1": obj.target_1,
            "target_2": obj.target_2, "risk_reward": obj.risk_reward,
            "position_pct": obj.position_pct, "reasons": obj.reasons,
        }
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj
