# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import numpy as np
import logging

logger = logging.getLogger("tech-signal-skill")
from dataclasses import dataclass
from typing import Optional

@dataclass
class TradePlan:
    entry_zone: float = 0.0
    stop_loss: float = 0.0
    target_1: float = 0.0
    target_2: float = 0.0
    risk_reward: float = 0.0
    risk_usd: float = 0.0
    reward_usd: float = 0.0
    position_size_pct: float = 0.0


def compute_support_resistance(df, n=20):
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    lookback = min(120, len(close))
    c = close[-lookback:]
    h = high[-lookback:]
    l = low[-lookback:]
    recent_high = float(h.max())
    recent_low = float(l.min())
    pn = min(10, n)
    swings_high, swings_low = [], []
    for i2 in range(pn, len(c) - pn):
        wh = h[i2-pn:i2+pn+1]
        wl = l[i2-pn:i2+pn+1]
        if c[i2] >= wh.max() * 0.97:
            swings_high.append(c[i2])
        if c[i2] <= wl.min() * 1.03:
            swings_low.append(c[i2])
    def _cluster(vals, tol=0.02):
        if not vals: return []
        vals = sorted(vals, reverse=True)
        clusters, cur = [], [vals[0]]
        for v in vals[1:]:
            if v < cur[0] * (1 - tol):
                clusters.append(float(np.mean(cur)))
                cur = [v]
            else:
                cur.append(v)
        if cur: clusters.append(float(np.mean(cur)))
        return clusters
    resists = _cluster(swings_high)
    supports = _cluster(swings_low)
    ma20 = float(np.mean(c[-20:]))
    std20 = float(np.std(c[-20:], ddof=1))
    boll_up = ma20 + 2 * std20
    boll_lo = ma20 - 2 * std20
    ma_vals = []
    for pp in (20, 50, 100, 200):
        if len(c) >= pp: ma_vals.append(float(np.mean(c[-pp:])))
    ma_clusters = sorted(set(round(m, 2) for m in ma_vals), reverse=True)
    vol = df["volume"].values.astype(float)
    lb_vol = min(20, len(c))
    vs = float(np.sum(vol[-lb_vol:]))
    tp = (h[-lb_vol:] + l[-lb_vol:]) / 2
    tv = float(np.sum(tp * vol[-lb_vol:]))
    vwap = tv / vs if vs > 0 else ma20
    cur = float(c[-1])
    resists_above = [v for v in resists if v > cur]
    supports_below = [v for v in supports if v < cur]
    if not resists_above:
        resists_above = [v for v in resists if v > cur] or [recent_high]
    if not supports_below:
        supports_below = [v for v in supports if v < cur] or [recent_low]

    return {
        "resistance_1": resists_above[0],
        "resistance_2": resists_above[1] if len(resists_above) > 1 else (resists_above[0] * 1.02),
        "support_2": supports_below[1] if len(supports_below) > 1 else (supports_below[0] * 0.98),
        "support_1": supports_below[0],
        "swing_resistances": resists_above[:3],
        "swing_supports": supports_below[:3],
        "boll_upper": boll_up, "boll_lower": boll_lo,
        "ma_levels": ma_clusters, "vwap": vwap,
    }

def compute_trend_phase(df, ind):
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float)
    ma200 = ind.ma200
    rsi = ind.rsi_14
    obv = ind.obv_trend
    vr = ind.vol_ratio
    dist200 = (close[-1] - ma200) / ma200 * 100 if ma200 > 0 else 0
    low_arr = df["low"].values.astype(float)
    high_slice = high[-20:]
    low_slice = low_arr[-20:]
    rng20 = float(np.max(high_slice) - np.min(low_slice))
    avg20 = float(np.mean(close[-20:]))
    rng_pct = rng20 / avg20 * 100 if avg20 > 0 else 0
    if ma200 > 0 and dist200 < -15: return "decline"
    if ma200 > 0 and dist200 > 30 and rsi > 65: return "rally"
    if ma200 > 0 and dist200 > 10 and ind.ma20 > ind.ma60: return "early_rally"
    if rsi > 60 and rsi < 75 and rng_pct < 15 and vr < 1.5: return "accumulation"
    if rsi > 70 and rng_pct > 20: return "distribution"
    if dist200 < -5 and obv == "down": return "decline"
    if ind.ma20 > ind.ma60 > ma200: return "rally"
    if ind.ma20 < ind.ma60 < ma200: return "decline"
    return "accumulation"

def generate_trade_plan(code, ind, sr, trend_phase, vcp_result=None):
    """生成交易计划，支持 ATR 动态止损和 VCP pivot 入场"""
    price = ind.last_close
    atr = ind.atr_14
    r1, r2 = sr["support_1"], sr["support_2"]
    res1, res2 = sr["resistance_1"], sr["resistance_2"]
    
    # Entry: 入场点计算（v2.8.2 修复：强势股优先）
    # 1. VCP pivot 点优先
    # 2. 强势股（MACD金叉+OBV上升+RSI 50-70）：现价-1%入场
    # 3. 普通股：支撑位（MA20/VWAP/支撑1），不低于现价15%
    # 4. 保守情况：现价-3%
    entry = 0.0
    
    if vcp_result and vcp_result.detected and vcp_result.pivot_point > 0:
        entry = vcp_result.pivot_point
    else:
        # 先检查是否强势股（强势股不依赖支撑位，直接现价附近入场）
        is_strong = (ind.macd_dif_dea_cross == 'golden' and 
                    ind.obv_trend == 'up' and
                    ind.rsi_14 < 70 and
                    ind.rsi_14 > 50)
        if is_strong:
            # 强势股：现价-1% 或 MA5，取较高者
            ma5_entry = ind.ma5 if ind.ma5 < price else price * 0.99
            entry = max(ma5_entry, price * 0.99)
        else:
            # 普通股：寻找支撑位（不低于现价15%）
            near_candidates = [v for v in (r1, ind.ma20, sr["vwap"]) 
                              if v > 0 and v < price and v > price * 0.85]
            if near_candidates:
                entry = max(near_candidates)
            else:
                entry = price * 0.97  # 保守：现价-3%

    
    # Stop: ATR 动态止损 + 支撑位双重确认（v2.8.1 修复）
    # 关键修复: 止损必须在入场点下方
    max_stop_pct = 0.075
    sl_atr = entry - 1.5 * atr
    sl_sr = r2 * 0.98 if r2 > 0 and r2 < entry else entry * 0.96
    sl_max = entry * (1 - max_stop_pct)
    stop = max(min(sl_sr, sl_atr), sl_max)
    # 确保止损在入场点下方
    stop = min(stop, entry * 0.95)  # 最高不超过入场价5%
    stop = max(stop, entry * 0.90)  # 最低不低于入场价10%


    
    # Targets: 分批止盈策略
    tgt1 = min(res1, res2) if res1 > 0 and res2 > 0 else (res1 if res1 > 0 else res2)
    tgt1 = max(tgt1, price * 1.05)  # 至少 5% 收益
    tgt2 = tgt1 + atr * 3 if atr > 0 else tgt1 * 1.12
    # 如果 VCP 模式质量高，可以放宽目标
    if vcp_result and vcp_result.quality == "strong":
        tgt2 = tgt1 * 1.15
    
    # v2.12: cap target prices
    cap1 = entry * 1.30
    cap2 = entry * 1.50
    if tgt1 > cap1:
        logger.warning(str(code) + ": target_1 " + str(round(tgt1,2)) + " capped to " + str(round(cap1,2)))
        tgt1 = cap1
    if tgt2 > cap2:
        logger.warning(str(code) + ": target_2 " + str(round(tgt2,2)) + " capped to " + str(round(cap2,2)))
        tgt2 = cap2
    if tgt1 > price * 1.30:
        tgt1 = price * 1.25
    if tgt2 > price * 1.50:
        tgt2 = price * 1.45
    risk = entry - stop if entry > stop else atr * 1.5
    reward = tgt2 - entry if tgt2 > entry else atr * 2
    rr = reward / risk if risk > 0 else 0
    pos_pct = min(3.0, (risk / price * 100) * 0.5) if risk > 0 else 1.0
    return TradePlan(
        entry_zone=round(entry, 2), stop_loss=round(stop, 2),
        target_1=round(tgt1, 2), target_2=round(tgt2, 2),
        risk_reward=round(rr, 2), risk_usd=round(risk, 2),
        reward_usd=round(reward, 2), position_size_pct=round(pos_pct, 1),
    )
