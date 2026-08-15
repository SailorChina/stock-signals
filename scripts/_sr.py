# -* coding: utf-8
import numpy as np
from dataclasses import dataclass

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
    recent_high = float(high[-n:].max())
    recent_low = float(low[-n:].min())
    pn = min(60, n)
    swings_high, swings_low = [], []
    for i in range(pn, len(close) - pn):
        wh = high[i-pn:i+pn+1]
        wl = low[i-pn:i+pn+1]
        # 使用 >= 允许略低于极值点，避免精确匹配遗漏
        if close[i] >= wh.max() * 0.999 and close[i] >= high[i] * 0.999:
            swings_high.append(close[i])
        if close[i] <= wl.max() * 1.001 and close[i] <= low[i] * 1.001:
            swings_low.append(close[i])
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
    ma20 = float(np.mean(close[-20:]))
    std20 = float(np.std(close[-20:], ddof=1))
    boll_up = ma20 + 2 * std20
    boll_lo = ma20 - 2 * std20
    ma_vals = []
    for pp in (20, 50, 100, 200):
        if len(close) >= pp: ma_vals.append(float(np.mean(close[-pp:])))
    ma_clusters = sorted(set(round(m, 2) for m in ma_vals), reverse=True)
    vol = df["volume"].values.astype(float)
    if n >= 20:
        vs = float(np.sum(vol[-n:]))
        tp = (high[-n:] + low[-n:]) / 2
        tv = float(np.sum(tp * vol[-n:]))
        vwap = tv / vs if vs > 0 else ma20
    else:
        vwap = ma20
    return {
        "resistance_1": resists[0] if resists else recent_high,
        "resistance_2": resists[1] if len(resists) > 1 else boll_up,
        "support_1": supports[0] if supports else recent_low,
        "support_2": supports[1] if len(supports) > 1 else boll_lo,
        "swing_resistances": resists[:3],
        "swing_supports": supports[:3],
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

def generate_trade_plan(ind, sr, trend_phase):
    price = ind.last_close
    atr = ind.atr_14
    r1, r2 = sr["support_1"], sr["support_2"]
    res1, res2 = sr["resistance_1"], sr["resistance_2"]
    # Entry: prefer support near current price, not too far below
    # 优先选择距当前价20%以内的支撑
    near_candidates = [v for v in (r1, ind.ma20, sr["vwap"]) if v > 0 and v < price and v > price * 0.8]
    entry = max(near_candidates) if near_candidates else (r1 if r1 > 0 else price * 0.95)
    # Stop: below the next support level or 2 ATRs below entry
    sl_sr = r2 * 0.98 if r2 > 0 and r2 < entry else entry * 0.96
    sl_atr = entry - 2 * atr
    stop = min(sl_sr, sl_atr)
    stop = max(stop, price * 0.85)  # never more than 15% below price
    # Targets: above current price toward resistance
    tgt1 = min(res1, res2) if res1 > 0 and res2 > 0 else (res1 if res1 > 0 else res2)
    tgt1 = max(tgt1, price * 1.03)  # at least 3% above current
    tgt2 = tgt1 + atr * 2 if atr > 0 else tgt1 * 1.08
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
