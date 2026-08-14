"""
信号评分引擎

基于技术指标计算 5 级评级（Buy / Overweight / Hold / Underweight / Sell）
纯确定性计算，不依赖 LLM
"""
from __future__ import annotations

import sys
import os as _os
from dataclasses import dataclass, field
from typing import List, Tuple

sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "futuapi", "scripts")))
from common import create_quote_context, check_ret, safe_close


# ---------------------------------------------------------------------------
# 评级定义
# ---------------------------------------------------------------------------

RATINGS = ("Buy", "Overweight", "Hold", "Underweight", "Sell")
RATING_LEVELS = {r: i for i, r in enumerate(RATINGS)}  # 0=Buy ... 4=Sell

# 维度权重
DIM_WEIGHTS = {
    "trend":    0.30,
    "momentum": 0.25,
    "volume":   0.20,
    "volatility": 0.15,
    "capital":  0.10,
}


# ---------------------------------------------------------------------------
# 各维度评分
# ---------------------------------------------------------------------------

def score_trend(ind) -> Tuple[float, str]:
    """趋势维度评分（0-100），返回 (分数, 理由)"""
    score = 50.0
    reasons = []

    # 均线排列
    if ind.ma5 > ind.ma10 > ind.ma20 > ind.ma60 > ind.ma120:
        score += 25
        reasons.append("均线多头排列，强势")
    elif ind.ma5 < ind.ma10 < ind.ma20 < ind.ma60 < ind.ma120:
        score -= 25
        reasons.append("均线空头排列，弱势")
    elif ind.ma5 > ind.ma20 > ind.ma60:
        score += 10
        reasons.append("短期均线在中期均线之上")
    elif ind.ma5 < ind.ma20 < ind.ma60:
        score -= 10
        reasons.append("短期均线在中期均线之下")

    # 价格在均线上方/下方
    if ind.ma60 > 0:
        price_vs_ma60 = (ind.last_close - ind.ma60) / ind.ma60 * 100
        if price_vs_ma60 > 5:
            score += 8
            reasons.append(f"价格高于MA60 {price_vs_ma60:.1f}%")
        elif price_vs_ma60 < -5:
            score -= 8
            reasons.append(f"价格低于MA60 {abs(price_vs_ma60):.1f}%")

    # MA金叉/死叉
    if ind.ma5_ma10_cross == 'golden':
        score += 10
        reasons.append("MA5/MA10 金叉")
    elif ind.ma5_ma10_cross == 'death':
        score -= 10
        reasons.append("MA5/MA10 死叉")

    return min(100, max(0, score)), "; ".join(reasons) if reasons else "均线震荡，方向不明"


def score_momentum(ind) -> Tuple[float, str]:
    """动量维度评分（0-100）"""
    score = 50.0
    reasons = []

    # RSI
    rsi = ind.rsi_14
    if rsi > 80:
        score -= 25
        reasons.append(f"RSI(14)={rsi:.1f}，严重超买")
    elif rsi > 70:
        score -= 10
        reasons.append(f"RSI(14)={rsi:.1f}，超买")
    elif rsi < 20:
        score += 25
        reasons.append(f"RSI(14)={rsi:.1f}，严重超卖")
    elif rsi < 30:
        score += 10
        reasons.append(f"RSI(14)={rsi:.1f}，超卖")
    elif 45 <= rsi <= 55:
        reasons.append(f"RSI(14)={rsi:.1f}，中性")

    # MACD
    if ind.macd_hist > 0:
        score += 12
        reasons.append("MACD柱为正，多头动能")
    else:
        score -= 12
        reasons.append("MACD柱为负，空头动能")

    if ind.macd_dif_dea_cross == 'golden':
        score += 10
        reasons.append("MACD金叉")
    elif ind.macd_dif_dea_cross == 'death':
        score -= 10
        reasons.append("MACD死叉")

    # KDJ
    k = ind.kdj_k
    if k > 80:
        score -= 8
        reasons.append(f"KDJ K={k:.1f}，超买")
    elif k < 20:
        score += 8
        reasons.append(f"KDJ K={k:.1f}，超卖")

    return min(100, max(0, score)), "; ".join(reasons) if reasons else "动量中性"


def score_volume(ind) -> Tuple[float, str]:
    """量能维度评分（0-100）"""
    score = 50.0
    reasons = []

    # OBV趋势
    if ind.obv_trend == "up":
        score += 15
        reasons.append("OBV上升趋势，资金持续流入")
    elif ind.obv_trend == "down":
        score -= 15
        reasons.append("OBV下降趋势，资金持续流出")
    else:
        reasons.append("OBV横盘，资金方向不明")

    # 量比
    vr = ind.vol_ratio
    if vr > 2.0:
        score += 5
        reasons.append(f"量比={vr:.2f}，显著放量")
    elif vr > 1.5:
        score += 3
        reasons.append(f"量比={vr:.2f}，温和放量")
    elif vr < 0.5:
        score -= 5
        reasons.append(f"量比={vr:.2f}，明显缩量")

    # 价格与量配合
    price_change = (ind.last_close - ind.prev_close) / ind.prev_close * 100 if ind.prev_close > 0 else 0
    if price_change > 0 and vr > 1.0:
        score += 5
        reasons.append("价量齐升，量价配合良好")
    elif price_change < 0 and vr > 1.0:
        score -= 5
        reasons.append("放量下跌，抛压较重")
    elif price_change > 0 and vr < 0.7:
        score -= 3
        reasons.append("缩量上涨，上攻动能不足")

    return min(100, max(0, score)), "; ".join(reasons) if reasons else "量能中性"


def score_volatility(ind) -> Tuple[float, str]:
    """波动率维度评分（0-100）"""
    score = 50.0
    reasons = []

    # 价格相对布林带位置
    bw = ind.boll_width
    if ind.boll_upper > 0:
        pos = (ind.last_close - ind.boll_lower) / (ind.boll_upper - ind.boll_lower) * 100
        if pos > 95:
            score -= 10
            reasons.append("价格触及布林上轨，短期超买")
        elif pos < 5:
            score += 10
            reasons.append("价格触及布林下轨，短期超卖")
        elif 40 <= pos <= 60:
            reasons.append("价格在布林带中部，波动正常")

    # 布林带宽（低波动预示变盘）
    if bw < 5:
        score += 5
        reasons.append(f"布林带宽={bw:.1f}%，低波动，或有变盘")
    elif bw > 20:
        score -= 5
        reasons.append(f"布林带宽={bw:.1f}%，高波动，趋势明显")

    # ATR
    if ind.ma20 > 0:
        atr_pct = ind.atr_14 / ind.ma20 * 100
        if atr_pct > 5:
            reasons.append(f"ATR={ind.atr_14:.2f}，波动较大")
        else:
            reasons.append(f"ATR={ind.atr_14:.2f}，波动正常")

    return min(100, max(0, score)), "; ".join(reasons) if reasons else "波动率中性"


def score_capital(ind, capital=None, short_pct=None) -> Tuple[float, str]:
    """资金面维度评分（0-100）"""
    score = 50.0
    reasons = []

    if capital is not None:
        super_net = capital.get("super_net", 0)
        big_net = capital.get("big_net", 0)
        mid_net = capital.get("mid_net", 0)
        sml_net = capital.get("sml_net", 0)
        total = super_net + big_net + mid_net + sml_net

        if super_net < 0 and sml_net > 0:
            score -= 15
            reasons.append("特大单流出、小单流入，大资金离场")
        elif super_net > 0 and sml_net < 0:
            score += 15
            reasons.append("特大单流入、小单流出，大资金进场")
        elif total > 0:
            score += 8
            reasons.append(f"总净流入 {total:,.0f}")
        else:
            score -= 8
            reasons.append(f"总净流出 {abs(total):,.0f}")

        if abs(super_net) > abs(big_net) * 2:
            reasons.append("超大单主导资金流向")
    else:
        reasons.append("资金数据不可用，跳过")

    if short_pct is not None and short_pct > 0:
        if short_pct > 15:
            score -= 15
            reasons.append(f"卖空比例={short_pct:.1f}%，空头强势")
        elif short_pct > 10:
            score -= 8
            reasons.append(f"卖空比例={short_pct:.1f}%，偏高")
        elif short_pct < 5:
            score += 5
            reasons.append(f"卖空比例={short_pct:.1f}%，空头弱势")

    return min(100, max(0, score)), "; ".join(reasons) if reasons else "资金面中性"


# ---------------------------------------------------------------------------
# 综合评分
# ---------------------------------------------------------------------------

def compute_rating(ind, capital=None, short_pct=None) -> dict:
    """计算综合评分和评级"""
    dims = {}
    total = 0.0
    weighted_sum = 0.0

    dim_scores = [
        ("trend",    score_trend(ind)),
        ("momentum", score_momentum(ind)),
        ("volume",   score_volume(ind)),
        ("volatility", score_volatility(ind)),
        ("capital",  score_capital(ind, capital, short_pct)),
    ]

    for name, (score, reason) in dim_scores:
        weight = DIM_WEIGHTS.get(name, 0.20)
        dims[name] = {"score": score, "reason": reason, "weight": weight}
        weighted_sum += score * weight
        total += weight

    final_score = weighted_sum / total if total > 0 else 50.0
    final_score = round(min(100, max(0, final_score)), 1)

    # 确定置信度
    scores = [d["score"] for d in dims.values()]
    score_range = max(scores) - min(scores) if scores else 0
    data_availability = sum(
        1 for d in dims.values() if d["reason"] and "不可用" not in d["reason"] and "跳过" not in d["reason"]
    ) / max(len(dims), 1)

    if data_availability < 0.5:
        confidence = "low"
    elif score_range > 30 and data_availability > 0.8:
        confidence = "high"
    else:
        confidence = "medium"

    # 确定评级
    if final_score >= 70:
        rating = "Buy"
    elif final_score >= 58:
        rating = "Overweight"
    elif final_score >= 42:
        rating = "Hold"
    elif final_score >= 30:
        rating = "Underweight"
    else:
        rating = "Sell"

    return {
        "rating": rating,
        "score": final_score,
        "confidence": confidence,
        "dimensions": dims,
        "timestamp": ind.last_time,
    }


# ---------------------------------------------------------------------------
# 买卖信号列表
# ---------------------------------------------------------------------------

def generate_signals(ind, rating: str, capital=None, short_pct=None) -> List[dict]:
    """生成具体的买卖信号列表"""
    signals = []

    # 趋势信号
    if ind.ma5 > ind.ma10 and ind.ma10 > ind.ma20:
        signals.append({"type": "trend", "side": "bullish", "desc": "短中期均线多头排列"})
    if ind.ma5 < ind.ma10 and ind.ma10 < ind.ma20:
        signals.append({"type": "trend", "side": "bearish", "desc": "短中期均线空头排列"})
    if ind.ma5_ma10_cross == 'golden':
        signals.append({"type": "trend", "side": "bullish", "desc": "MA5/MA10 金叉信号"})
    if ind.ma5_ma10_cross == 'death':
        signals.append({"type": "trend", "side": "bearish", "desc": "MA5/MA10 死叉信号"})

    # 动量信号
    if ind.rsi_14 < 30:
        signals.append({"type": "momentum", "side": "bullish", "desc": f"RSI(14)={ind.rsi_14:.1f}，超卖反弹信号"})
    if ind.rsi_14 > 70:
        signals.append({"type": "momentum", "side": "bearish", "desc": f"RSI(14)={ind.rsi_14:.1f}，超买回调信号"})
    if ind.macd_dif_dea_cross == 'golden':
        signals.append({"type": "momentum", "side": "bullish", "desc": "MACD 金叉信号"})
    if ind.macd_dif_dea_cross == 'death':
        signals.append({"type": "momentum", "side": "bearish", "desc": "MACD 死叉信号"})
    if ind.kdj_k < 20:
        signals.append({"type": "momentum", "side": "bullish", "desc": f"KDJ K={ind.kdj_k:.1f}，超卖信号"})
    if ind.kdj_k > 80:
        signals.append({"type": "momentum", "side": "bearish", "desc": f"KDJ K={ind.kdj_k:.1f}，超买信号"})

    # 布林信号
    if ind.boll_upper > 0:
        pos = (ind.last_close - ind.boll_lower) / (ind.boll_upper - ind.boll_lower)
        if pos > 0.95:
            signals.append({"type": "volatility", "side": "bearish", "desc": "触及布林上轨，短期超买"})
        elif pos < 0.05:
            signals.append({"type": "volatility", "side": "bullish", "desc": "触及布林下轨，短期超卖"})

    # 量能信号
    if ind.vol_ratio > 2.0:
        signals.append({"type": "volume", "side": "neutral", "desc": f"量比={ind.vol_ratio:.2f}，显著放量，关注方向"})
    if ind.obv_trend == "up":
        signals.append({"type": "volume", "side": "bullish", "desc": "OBV持续上升，资金流入"})
    elif ind.obv_trend == "down":
        signals.append({"type": "volume", "side": "bearish", "desc": "OBV持续下降，资金流出"})

    # 资金信号
    if capital:
        super_net = capital.get("super_net", 0)
        if super_net < -1e6:
            signals.append({"type": "capital", "side": "bearish", "desc": f"特大单净流出 ${abs(super_net/10000):.0f}万"})
        elif super_net > 1e6:
            signals.append({"type": "capital", "side": "bullish", "desc": f"特大单净流入 ${super_net/10000:.0f}万"})

    # 卖空信号
    if short_pct is not None and short_pct > 15:
        signals.append({"type": "short", "side": "bearish", "desc": f"卖空比例={short_pct:.1f}%，空头强势"})
    elif short_pct is not None and short_pct < 5:
        signals.append({"type": "short", "side": "bullish", "desc": f"卖空比例={short_pct:.1f}%，空头弱势"})

    return signals


# ---------------------------------------------------------------------------
# 资金数据获取
# ---------------------------------------------------------------------------

def get_capital_data(code: str) -> dict:
    """从 Futu API 获取资金分布数据"""
    try:
        sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "futuapi", "scripts")))
        from common import create_quote_context, check_ret, safe_close
        ctx = None
        try:
            ctx = create_quote_context()
            ret, data = ctx.get_capital_distribution(code)
            check_ret(ret, data, ctx, "获取资金分布")
            if data is None or data.empty:
                return {}
            row = data.iloc[0]
            super_in = float(row.get("capital_in_super", 0) or 0)
            super_out = float(row.get("capital_out_super", 0) or 0)
            big_in = float(row.get("capital_in_big", 0) or 0)
            big_out = float(row.get("capital_out_big", 0) or 0)
            mid_in = float(row.get("capital_in_mid", 0) or 0)
            mid_out = float(row.get("capital_out_mid", 0) or 0)
            sml_in = float(row.get("capital_in_small", 0) or 0)
            sml_out = float(row.get("capital_out_small", 0) or 0)
            return {
                "super_net": super_in - super_out,
                "big_net": big_in - big_out,
                "mid_net": mid_in - mid_out,
                "sml_net": sml_in - sml_out,
                "super_in": super_in, "super_out": super_out,
                "big_in": big_in, "big_out": big_out,
                "mid_in": mid_in, "mid_out": mid_out,
                "sml_in": sml_in, "sml_out": sml_out,
            }
        finally:
            safe_close(ctx)
    except Exception as e:
        print(f"[WARN] 获取资金数据失败 {code}: {e}", file=sys.stderr)
        return {}


def get_short_data(code: str) -> Optional[float]:
    """从 Futu API 获取最新卖空比例"""
    try:
        sys.path.insert(0, _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "futuapi", "scripts")))
        from common import create_quote_context, check_ret, safe_close
        ctx = None
        try:
            ctx = create_quote_context()
            ret, data, _ = ctx.get_daily_short_volume(code, num=1)
            check_ret(ret, data, ctx, "获取卖空数据")
            if data is None or data.empty:
                return None
            row = data.iloc[0]
            short_pct = float(row.get("short_percent", 0) or 0)
            return short_pct
        finally:
            safe_close(ctx)
    except Exception:
        return None



