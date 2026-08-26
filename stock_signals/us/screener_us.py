# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional
from .indicators_us import fetch_kline_us, compute_indicators_us
from .scoring_us import compute_rating_us

logger = logging.getLogger("tech-signal-skill")

US_POOL = [
    "US.AAPL", "US.MSFT", "US.GOOG", "US.AMZN", "US.META",
    "US.NVDA", "US.TSLA", "US.AVGO", "US.CSCO", "US.ORCL",
    "US.INTC", "US.QCOM", "US.TXN", "US.AMAT", "US.LRCX",
    "US.ASML", "US.NXPI",
    "US.MCD", "US.NKE", "US.TGT", "US.KO", "US.PEP",
    "US.WMT", "US.COST", "US.DIS", "US.BKNG",
    "US.JNJ", "US.PFE", "US.UNH", "US.LLY", "US.ABBV",
    "US.MRK", "US.BMY", "US.AMGN", "US.GILD", "US.ZTS",
    "US.HON", "US.CAT", "US.BA", "US.DE", "US.FCX",
    "US.NEM", "US.CP",
    "US.XOM", "US.COP", "US.OXY",
]
US_POOL = list(dict.fromkeys(US_POOL))

US_BLACKLIST = {
    "US.JPM", "US.BAC", "US.WFC", "US.C", "US.GS", "US.MS",
    "US.USB", "US.PNC", "US.TFC", "US.BK", "US.AXP",
    "US.SPY", "US.QQQ", "US.IWM", "US.VTI", "US.VOO",
}

@dataclass
class USConfig:
    min_score: float = 50.0
    min_rr: float = 2.5
    min_dist_from_high: float = 5.0
    max_hold_days: int = 10
    stop_loss_atr: float = 1.4
    max_per_market: int = 10
    max_delay: float = 0.5

@dataclass
class USScanResult:
    code: str
    score: float
    rating: str
    dist_high: float
    rr: float
    entry: float = 0.0
    stop_loss: float = 0.0
    target_1: float = 0.0
    last_close: float = 0.0
    reasons: List[str] = field(default_factory=list)

def _is_blacklisted(code: str) -> bool:
    return code in US_BLACKLIST

def _compute_trade_plan(ind, atr_mult: float = 1.8) -> dict:
    entry = ind.last_close
    atr = ind.atr_14
    if atr <= 0 or entry <= 0:
        return {"entry": entry, "stop_loss": entry * 0.95, "target_1": entry * 1.08, "risk_reward": 0, "position_pct": 0.2}
    stop = entry - atr_mult * atr
    target_1 = entry + atr * 4.0
    risk = entry - stop
    reward = target_1 - entry
    rr = reward / risk if risk > 0 else 0
    pos_pct = min(20.0, (risk / entry * 100) * 0.5) if risk > 0 else 20.0
    return {"entry": round(entry, 2), "stop_loss": round(stop, 2), "target_1": round(target_1, 2), "risk_reward": round(rr, 2), "position_pct": round(pos_pct, 1)}

def analyze_one_us(code: str, config: USConfig = None) -> Optional[USScanResult]:
    if config is None:
        config = USConfig()
    if _is_blacklisted(code):
        return None
    try:
        df = fetch_kline_us(code, num=500)
        if df is None or df.empty or len(df) < 60:
            return None
        ind = compute_indicators_us(df, code, "1d")
        rat = compute_rating_us(ind)
        score = rat["score"]
        if score < config.min_score:
            return None
        dist_high = ind.distance_from_52w_high
        if dist_high > -config.min_dist_from_high:
            return None
        tp = _compute_trade_plan(ind, config.stop_loss_atr)
        rr = tp["risk_reward"]
        if rr < config.min_rr:
            return None
        if ind.rsi_14 > 75:
            return None
        ma_gap = ind.ma5 / ind.ma20 - 1 if ind.ma20 > 0 else 0
        if ma_gap > 10:
            return None
        if ind.td_turn == "sell_turn":
            return None
        reasons = []
        if ind.ma5_ma10_cross == "golden":
            reasons.append("MA5/MA10 golden cross")
        if ind.macd_dif_dea_cross == "golden":
            reasons.append("MACD golden cross")
        if ind.vol_ratio > 1.5:
            reasons.append(f"Volume {ind.vol_ratio:.1f}x")
        if ind.obv_trend == "up":
            reasons.append("OBV rising")
        if 5 <= dist_high <= 20 and ind.rsi_14 < 65:
            reasons.append(f"Pullback entry (dist={dist_high:.1f}%)")
        return USScanResult(code=code, score=score, rating=rat["rating"], dist_high=round(dist_high, 1), rr=rr, entry=tp["entry"], stop_loss=tp["stop_loss"], target_1=tp["target_1"], last_close=ind.last_close, reasons=reasons)
    except Exception as e:
        logger.debug(f"  {code} failed: {e}")
        return None

def scan_us(config: USConfig = None):
    if config is None:
        config = USConfig()
    logger.info(f"US scan started (pool: {len(US_POOL)})")
    picks = []
    for i, code in enumerate(US_POOL):
        result = analyze_one_us(code, config)
        if result is not None:
            picks.append(result)
        if (i + 1) % 10 == 0:
            logger.info(f"  Progress: {i+1}/{len(US_POOL)}, found {len(picks)} picks")
    picks.sort(key=lambda x: -x.score)
    return {"scan_time": time.strftime("%Y-%m-%d %H:%M:%S"), "total_analyzed": len(US_POOL), "total_picks": len(picks), "picks": [{"code": p.code, "score": p.score, "rating": p.rating, "dist_high": p.dist_high, "rr": p.rr, "entry": p.entry, "stop_loss": p.stop_loss, "target_1": p.target_1, "last_close": p.last_close, "reasons": p.reasons} for p in picks[:config.max_per_market]], "all_picks": [{"code": p.code, "score": p.score, "rating": p.rating, "dist_high": p.dist_high, "rr": p.rr, "entry": p.entry, "stop_loss": p.stop_loss, "target_1": p.target_1} for p in picks]}
