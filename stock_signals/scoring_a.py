# -*- coding: utf-8 -*-
"""A股专属评分模块"""
from __future__ import annotations
A_DIM_WEIGHTS = {"trend": 0.10, "momentum": 0.10, "volume": 0.10, "turnover": 0.07, "capital": 0.12, "sentiment": 0.12, "kdj": 0.12, "limit_prot": 0.12, "sector": 0.12, "boll": 0.05}
A_MIN_SCORE = 55; A_WATCHLIST_MIN = 45

def compute_a_rating(ind, capital=None, short_pct=None):
    scores = {"trend": _trend(ind), "momentum": _momentum(ind), "volume": _volume(ind), "turnover": _turnover(ind), "capital": _capital(ind), "sentiment": _sentiment(ind), "kdj": _kdj(ind), "limit_prot": _limit_protection(ind), "sector": _sector(ind), "boll": _boll(ind)}
    total = sum(scores[k] * v for k, v in A_DIM_WEIGHTS.items())
    rating = "Buy" if total >= 70 else "Overweight" if total >= 60 else "Hold" if total >= 50 else "Underweight" if total >= 40 else "Sell"
    confidence = "high" if total >= 70 else "medium" if total >= 60 else "low"
    return {"score": round(total, 1), "rating": rating, "confidence": confidence, "dimensions": scores}

def _trend(ind):
    s = 50
    if ind.ma5 > ind.ma10 > ind.ma20: s += 15
    elif ind.ma5 > ind.ma10: s += 8
    if ind.last_close > ind.ma20: s += 10
    if 50 < ind.rsi_14 < 65: s += 10
    elif ind.rsi_14 >= 65: s -= 5
    return max(0, min(100, s))

def _momentum(ind):
    s = 50
    if ind.macd_dif > ind.macd_dea: s += 15
    if ind.day_change_pct > 0: s += 10
    if ind.rsi_14 > 50: s += 5
    return max(0, min(100, s))

def _volume(ind):
    s = 50
    if ind.vol_ratio > 1.5: s += 20
    elif ind.vol_ratio > 1.2: s += 10
    elif ind.vol_ratio < 0.8: s -= 10
    if ind.obv_trend == "up": s += 10
    return max(0, min(100, s))

def _turnover(ind):
    s = 50; tr = ind.turnover_rate
    if 3 < tr < 8: s += 20
    elif 8 <= tr < 15: s += 10
    elif tr >= 15: s -= 10
    elif tr < 1: s -= 5
    return max(0, min(100, s))

def _capital(ind):
    s = 50
    if ind.north_flow > 0: s += 15
    elif ind.north_flow < -0.5: s -= 10
    return max(0, min(100, s))

def _sentiment(ind):
    s = 50
    if ind.is_longhubang: s += 15
    if ind.is_sector_leader: s += 10
    if ind.limit_up_prob > 0.5: s += 10
    if ind.sector_change > 2: s += 5
    return max(0, min(100, s))

def _kdj(ind):
    try:
        s = 50
        j = float(getattr(ind, 'kdj_j', 50))
        k = float(getattr(ind, 'kdj_k', 50))
        if j > 100: s -= 20
        elif j > 80: s -= 10
        elif j < 0: s += 20
        elif j < 20: s += 10
        if 40 < k < 60: s += 5
        return max(0, min(100, s))
    except:
        return 50

def _limit_protection(ind):
    s = 50
    if getattr(ind, 'is_limit_up', False): s -= 30
    elif getattr(ind, 'is_limit_down', False): s -= 20
    change5 = getattr(ind, 'change_pct_5d', 0)
    if change5 > 15: s -= 15
    elif change5 > 10: s -= 8
    elif change5 < -10: s += 5

def _sector(ind):
    """板块联动评分 - A股核心: 板块涨个股跟涨是最佳形态"""
    s = 50
    change5 = getattr(ind, 'change_pct_5d', 0)
    price_vs_ma20 = getattr(ind, 'price_vs_ma20', 0)
    # 板块联动: 5日涨幅适中(3-8%)且未偏离MA20过大 → 板块带动中
    if 3 < change5 < 10 and price_vs_ma20 < 10: s += 15
    elif change5 < 0 and price_vs_ma20 < -5: s += 5  # 超跌有板块支撑
    elif change5 > 15: s -= 10  # 涨太多可能见顶
    return max(0, min(100, s))

def _boll(ind):
    """布林带评分"""
    s = 50
    pos = getattr(ind, 'price_vs_bb', 'middle')
    width = getattr(ind, 'bb_width', 5)
    if pos == 'lower_half': s += 10  # 下轨附近支撑
    elif pos == 'above': s -= 10  # 突破上轨可能过热
    if width < 3: s += 5  # 布林带收口预示突破
    elif width > 10: s -= 5  # 波动率过大
    return max(0, min(100, s))

    return max(0, min(100, s))

