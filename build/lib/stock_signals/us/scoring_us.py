# -*- coding: utf-8 -*-
"""
美股独立评分引擎
4维度: trend(35%) + momentum(30%) + volume(20%) + volatility(15%)
不含 capital/short 维度(仅US)
"""
from __future__ import annotations
import sys
from typing import Tuple, List
from .indicators_us import IndicatorsUS

RATINGS = ("Buy", "Overweight", "Hold", "Underweight", "Sell")

# 美股维度权重
DIM_WEIGHTS_US = {
    "trend": 0.35,
    "momentum": 0.30,
    "volume": 0.20,
    "volatility": 0.15,
}


def score_trend_us(ind: IndicatorsUS) -> Tuple[float, str]:
    """趋势维度评分(0-100)"""
    score = 50.0
    reasons = []

    # 均线排列
    if ind.ma5 > ind.ma10 > ind.ma20 > ind.ma60:
        score += 20
        reasons.append("均线多头排列")
    elif ind.ma5 < ind.ma10 < ind.ma20 < ind.ma60:
        score -= 20
        reasons.append("均线空头排列")
    elif ind.ma5 > ind.ma20 > ind.ma60:
        score += 10
        reasons.append("短期均线在中长期之上")
    elif ind.ma5 < ind.ma20 < ind.ma60:
        score -= 10
        reasons.append("短期均线在中长期之下")

    # 价格 vs MA60
    if ind.ma60 > 0:
        pv_ma60 = ind.price_vs_ma60
        if pv_ma60 > 20:
            score -= 15
            reasons.append(f"价格远超MA60 +{pv_ma60:.1f}%")
        elif pv_ma60 > 10:
            score -= 8
            reasons.append(f"价格高于MA60 +{pv_ma60:.1f}%")
        elif pv_ma60 > 5:
            score += 5
            reasons.append(f"价格高于MA60 +{pv_ma60:.1f}%")
        elif -5 <= pv_ma60 <= 5:
            score += 5
            reasons.append(f"价格贴近MA60({pv_ma60:.1f}%)")
        elif pv_ma60 < -10:
            score -= 5
            reasons.append(f"价格低于MA60 {pv_ma60:.1f}%")

    # MA金叉/死叉
    if ind.ma5_ma10_cross == "golden":
        score += 10
        reasons.append("MA5/MA10金叉")
    elif ind.ma5_ma10_cross == "death":
        score -= 10
        reasons.append("MA5/MA10死叉")

    # 52周位置
    dist_high = ind.distance_from_52w_high
    dist_low = ind.distance_from_52w_low
    if dist_high > 5:
        score += 8
        reasons.append(f"距52周高点仅{abs(dist_high):.1f}%")
    elif dist_high < -20:
        score -= 5
        reasons.append(f"距52周高点{abs(dist_high):.1f}%")
    if dist_low > 30:
        score += 5
        reasons.append(f"距52周低点+{dist_low:.1f}%")

    # ADX
    if ind.adx > 0:
        if ind.adx > 40:
            score += 5
            reasons.append(f"ADX={ind.adx:.1f}趋势强劲")
        elif ind.adx < 20:
            score -= 5
            reasons.append(f"ADX={ind.adx:.1f}趋势极弱")

    return min(100, max(0, score)), "; ".join(reasons) if reasons else "均线震荡"


def score_momentum_us(ind: IndicatorsUS) -> Tuple[float, str]:
    """动量维度评分(0-100)"""
    score = 50.0
    reasons = []

    # RSI
    rsi = ind.rsi_14
    if rsi > 80:
        score -= 25
        reasons.append(f"RSI(14)={rsi:.1f}严重超买")
    elif rsi > 70:
        score -= 10
        reasons.append(f"RSI(14)={rsi:.1f}超买")
    elif rsi > 60:
        score += 5
        reasons.append(f"RSI(14)={rsi:.1f}偏强")
    elif rsi > 50:
        score += 3
    elif rsi > 40:
        score -= 3
    elif rsi > 30:
        score -= 5
        reasons.append(f"RSI(14)={rsi:.1f}偏弱")
    elif rsi <= 30:
        score += 10
        reasons.append(f"RSI(14)={rsi:.1f}超卖反弹机会")

    # MACD
    if ind.macd_dif > ind.macd_dea:
        score += 10
        reasons.append("MACD DIF>DEA")
    else:
        score -= 5
    if ind.macd_hist > 0:
        score += 5
    if ind.macd_dif_dea_cross == "golden":
        score += 8
        reasons.append("MACD金叉")
    elif ind.macd_dif_dea_cross == "death":
        score -= 8
        reasons.append("MACD死叉")

    # KDJ
    j = ind.kdj_j
    if j > 100:
        score -= 15
        reasons.append(f"KDJ J={j:.1f}严重超买")
    elif j > 80:
        score -= 8
        reasons.append(f"KDJ J={j:.1f}超买")
    elif j < 0:
        score += 15
        reasons.append(f"KDJ J={j:.1f}严重超卖")
    elif j < 20:
        score += 8
        reasons.append(f"KDJ J={j:.1f}超卖")

    # 日内动量
    chg = ind.day_change_pct
    if chg > 5:
        score -= 10
        reasons.append(f"单日涨幅{chg:.1f}%过大")
    elif chg > 3:
        score -= 5
    elif chg < -5:
        score += 10
        reasons.append(f"单日跌幅{chg:.1f}%超卖")
    elif chg < -3:
        score += 5

    return min(100, max(0, score)), "; ".join(reasons) if reasons else "动量中性"


def score_volume_us(ind: IndicatorsUS) -> Tuple[float, str]:
    """量能维度评分(0-100)"""
    score = 50.0
    reasons = []

    vr = ind.vol_ratio
    if vr > 3.0:
        score += 15
        reasons.append(f"量比={vr:.1f}异常放量")
    elif vr > 2.0:
        score += 10
        reasons.append(f"量比={vr:.1f}显著放量")
    elif vr > 1.5:
        score += 5
    elif vr < 0.5:
        score -= 15
        reasons.append(f"量比={vr:.1f}极度缩量")
    elif vr < 0.7:
        score -= 8
        reasons.append(f"量比={vr:.1f}缩量")

    # OBV trend
    if ind.obv_trend == "up":
        score += 5
        reasons.append("OBV上升资金流入")
    elif ind.obv_trend == "down":
        score -= 5
        reasons.append("OBV下降资金流出")

    return min(100, max(0, score)), "; ".join(reasons) if reasons else "量能中性"


def score_volatility_us(ind: IndicatorsUS) -> Tuple[float, str]:
    """波动率维度评分(0-100)"""
    score = 50.0
    reasons = []

    # ATR百分比
    atr_pct = ind.atr_14 / ind.last_close * 100 if ind.last_close > 0 else 0
    if atr_pct < 1.0:
        score += 10
        reasons.append(f"ATR={atr_pct:.2f}%低波动")
    elif atr_pct < 2.0:
        score += 5
    elif atr_pct > 4.0:
        score -= 10
        reasons.append(f"ATR={atr_pct:.2f}%高波动风险")
    elif atr_pct > 6.0:
        score -= 20

    # BOLL宽度
    if ind.boll_width > 0:
        if ind.boll_width > 10:
            score -= 5
            reasons.append(f"布林带宽{ind.boll_width:.1f}%扩张")
        elif ind.boll_width < 3:
            score += 5
            reasons.append(f"布林带窄{ind.boll_width:.1f}%收缩")

    # Vol regime
    if ind.vol_regime == "low":
        score += 5
        reasons.append("低波动环境")
    elif ind.vol_regime == "high":
        score -= 5
        reasons.append("高波动环境")

    return min(100, max(0, score)), "; ".join(reasons) if reasons else "波动率中性"


def compute_rating_us(ind: IndicatorsUS) -> dict:
    """计算美股综合评分"""
    trend_score, trend_reason = score_trend_us(ind)
    momentum_score, mom_reason = score_momentum_us(ind)
    volume_score, vol_reason = score_volume_us(ind)
    volatility_score, vola_reason = score_volatility_us(ind)

    dims = {
        "trend": {"score": trend_score, "reason": trend_reason, "weight": DIM_WEIGHTS_US["trend"]},
        "momentum": {"score": momentum_score, "reason": mom_reason, "weight": DIM_WEIGHTS_US["momentum"]},
        "volume": {"score": volume_score, "reason": vol_reason, "weight": DIM_WEIGHTS_US["volume"]},
        "volatility": {"score": volatility_score, "reason": vola_reason, "weight": DIM_WEIGHTS_US["volatility"]},
    }

    final_score = (
        trend_score * DIM_WEIGHTS_US["trend"] +
        momentum_score * DIM_WEIGHTS_US["momentum"] +
        volume_score * DIM_WEIGHTS_US["volume"] +
        volatility_score * DIM_WEIGHTS_US["volatility"]
    )

    if final_score >= 70:
        rating = "Buy"
        confidence = "high"
    elif final_score >= 58:
        rating = "Overweight"
        confidence = "medium"
    elif final_score >= 44:
        rating = "Hold"
        confidence = "medium"
    elif final_score >= 32:
        rating = "Underweight"
        confidence = "low"
    else:
        rating = "Sell"
        confidence = "low"

    return {
        "rating": rating,
        "score": round(final_score, 1),
        "confidence": confidence,
        "dimensions": dims,
        "timestamp": ind.last_time,
    }
