#!/usr/bin/env python3


"""


股票买卖信号分析模块





? Futu OpenAPI ?? K ????? pandas/numpy 股票买卖信号分析模块???


??? LLM股票买卖信号分析模块?


"""


from __future__ import annotations





import sys


import os as _os
import time


from dataclasses import dataclass, field


from typing import List, Optional





import pandas as pd
import threading


import numpy as np





sys.path.insert(0, 'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
from common import create_quote_context, check_ret, safe_close, KLType, AuType, RET_OK





KTYPE_MAP = {


    "1m": KLType.K_1M, "3m": KLType.K_3M, "5m": KLType.K_5M,


    "15m": KLType.K_15M, "30m": KLType.K_30M, "60m": KLType.K_60M,


    "1d": KLType.K_DAY, "1w": KLType.K_WEEK, "1M": KLType.K_MON,


}








# ============================================================
# ============================================================
# ============================================================
# FUTU OPENAPI 限流规则（重点标记，禁止修改）
# 限制: 每 30 秒最多 60 次 K 线请求 (request_history_kline)
# 说明: 每次 create_quote_context() 新建连接都计入请求配额
# 策略: 单例 context + 锁保护，串行化 API 调用避免超限
# ============================================================
_ctx = None  # 单例 Futu 行情上下文
_ctx_lock = threading.Lock()  # 保护 API 调用，确保串行

def _get_ctx():
    """获取单例行情上下文（线程安全）"""
    global _ctx
    if _ctx is None:
        try:
            _ctx = create_quote_context()
        except Exception as e:
            raise RuntimeError(f"无法连接 Futu OpenD: {e}")
    return _ctx

def _reset_ctx():
    """重置上下文（出错时调用）"""
    global _ctx
    with _ctx_lock:
        if _ctx is not None:
            try:
                _ctx.close()
            except Exception:
                pass
            _ctx = None

def fetch_kline(code: str, ktype: str = "1d", num: int = 300) -> pd.DataFrame:
    kl_type = KTYPE_MAP.get(ktype, KLType.K_DAY)
    ctx = None
    try:
        ctx = _get_ctx()
        ret, data, _ = ctx.request_history_kline(
            code, ktype=kl_type, autype=AuType.QFQ, max_count=num,
        )
        check_ret(ret, data, ctx, "获取K线")
        time.sleep(0.15)
        if data is None or data.empty:
            return pd.DataFrame()
        df = data.copy()
        df["time"] = df["time_key"].astype(str)
        for col in ("open", "high", "low", "close", "volume"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.sort_values("time").reset_index(drop=True)
    except Exception as e:
        print(f"[ERROR] 获取K线数据失败 {code}: {e}", file=sys.stderr)
        _reset_ctx()
        return pd.DataFrame()

@dataclass


class Indicators:


    code: str = ""


    ktype: str = ""


    df: pd.DataFrame = field(default_factory=pd.DataFrame)


    last_close: float = 0.0


    last_time: str = ""


    prev_close: float = 0.0


    day_change_pct: float = 0.0


    ma5: float = 0.0; ma10: float = 0.0; ma20: float = 0.0


    ma60: float = 0.0; ma120: float = 0.0; ma200: float = 0.0


    macd_dif: float = 0.0; macd_dea: float = 0.0; macd_hist: float = 0.0


    rsi_6: float = 0.0; rsi_12: float = 0.0; rsi_14: float = 0.0; rsi_24: float = 0.0


    kdj_k: float = 0.0; kdj_d: float = 0.0; kdj_j: float = 0.0


    boll_mid: float = 0.0; boll_upper: float = 0.0; boll_lower: float = 0.0


    boll_width: float = 0.0


    atr_14: float = 0.0


    obv: float = 0.0; obv_trend: str = "flat"


    vwma_20: float = 0.0


    vol_ratio: float = 0.0


    ma5_ma10_cross: str = ""       # golden / death / none


    macd_dif_dea_cross: str = ""   # golden / death / none


    price_vs_ma20: float = 0.0     # 价格距MA20比例 %


    price_vs_ma60: float = 0.0


    price_vs_ma200: float = 0.0

    # ── ADX trend strength ─────────────────────────────────────────
    adx: float = 0.0
    plus_di: float = 0.0
    minus_di: float = 0.0

    # ── Divergence detection ───────────────────────────────────────
    macd_divergence: str = "none"
    rsi_divergence: str = "none"

    # ── Candlestick patterns ───────────────────────────────────────
    candle_pattern: str = "none"
    candle_pattern_name: str = ""

    # ── Gap analysis ───────────────────────────────────────────────
    gap_pct: float = 0.0
    gap_type: str = "none"
    gap_filled: bool = False

    # ── Volatility regime ──────────────────────────────────────────
    vol_regime: str = "normal"
    vol_regime_score: float = 50.0

    # ── TD Sequential (9转信号) ────────────────────────────────────
    td_buy_setup: bool = False       # TD买入序列完成(9连阴)
    td_sell_setup: bool = False      # TD卖出序列完成(9连阳)
    td_buy_count: int = 0            # 当前买入计数 1-9
    td_sell_count: int = 0           # 当前卖出计数 1-9
    td_turn: str = "none"            # turn信号: buy_turn / sell_turn / none
    
    # ── VCP (Volatility Contraction Pattern) ──────────────────────
    vcp_detected: bool = False        # 是否检测到 VCP 模式
    vcp_contractions: int = 0          # 收缩次数
    vcp_pivot_point: float = 0.0      # pivot 点 (入场价)
    vcp_pattern_width: float = 0.0    # 模式宽度 (%)
    vcp_volume_drying: bool = False   # 成交量是否萎缩
    vcp_quality: str = "none"          # 质量: strong/medium/weak/none
    
    # ── 相对强度 (RS) 评分 (Minervini RS Rating) ──────────────────
    rs_rating: int = 0                  # 相对强度评分 1-99
    rs_percentile: float = 0.0          # 价格处于历史Percentile
    distance_from_52w_high: float = 0.0 # 距52周高点距离 (%)
    distance_from_52w_low: float = 0.0  # 距52周低点距离 (%)
    trend_template_pass: bool = False    # 是否通过8点趋势模板
    # ── Episodic Pivot (事件性转折) ────────────────────────────────
    ep_detected: bool = False           # 是否检测到事件性转折
    ep_gap_up_pct: float = 0.0          # 跳空高开幅度 (%)
    ep_volume_spike: float = 0.0        # 成交量放大倍数
    ep_catalyst_score: float = 0.0      # 催化剂评分
    ep_quality: str = "none"            # 质量: strong/medium/weak/none








def compute_indicators(df: pd.DataFrame, code: str = "", ktype: str = "1d") -> Indicators:


    if df is None or df.empty or len(df) < 1:
        return Indicators(code=code, ktype=ktype)







    ind = Indicators(code=code, ktype=ktype, df=df)


    close = df["close"].values.astype(float)


    high = df["high"].values.astype(float)


    low = df["low"].values.astype(float)


    volume = df["volume"].values.astype(float)


    n = len(close)


    last = n - 1





    ind.last_close = float(close[last])


    ind.last_time = str(df["time"].iloc[last])


    ind.prev_close = float(close[last - 1]) if last > 0 else ind.last_close


    ind.day_change_pct = (close[last] - ind.prev_close) / ind.prev_close * 100 if ind.prev_close > 0 else 0.0





    # ---- MA均线 ----


    for period, attr in [(5, "ma5"), (10, "ma10"), (20, "ma20"),


                          (60, "ma60"), (120, "ma120"), (200, "ma200")]:


        if n >= period:


            val = float(np.mean(close[-period:]))


        elif n > 0:


            val = float(np.mean(close))


        else:


            val = 0.0


        setattr(ind, attr, val)





    # ---- 价格偏离度 ----


    for ma_attr, pct_attr in [("ma20", "price_vs_ma20"),


                               ("ma60", "price_vs_ma60"),


                               ("ma200", "price_vs_ma200")]:


        ma_val = getattr(ind, ma_attr)


        if ma_val > 0:


            setattr(ind, pct_attr, (ind.last_close - ma_val) / ma_val * 100)


        else:


            setattr(ind, pct_attr, 0.0)





    # ---- MACD (12, 26, 9) ----


    if n >= 26:


        ema12 = _ema(close, 12)


        ema26 = _ema(close, 26)


        dif_series = ema12 - ema26


        dea_series = _ema(dif_series, 9)


        ind.macd_dif = float(dif_series[-1])


        ind.macd_dea = float(dea_series[-1])


        ind.macd_hist = float(2 * (dif_series[-1] - dea_series[-1]))


        # ??/???????10?K?


        for i in range(max(0, n - 10), n - 1):


            if dif_series[i] <= dea_series[i] and dif_series[i + 1] > dea_series[i + 1]:


                ind.macd_dif_dea_cross = "golden"


                break


            if dif_series[i] >= dea_series[i] and dif_series[i + 1] < dea_series[i + 1]:


                ind.macd_dif_dea_cross = "death"


                break


    else:


        ind.macd_dif = ind.macd_dea = ind.macd_hist = 0.0


        ind.macd_dif_dea_cross = "none"





    # ---- RSI (EMA滑动平均) ----


    deltas = np.diff(close)


    for period, attr in [(6, "rsi_6"), (12, "rsi_12"), (14, "rsi_14"), (24, "rsi_24")]:
        if len(deltas) < period:
            setattr(ind, attr, 50.0)
            continue
        gains = np.where(deltas[-period:] > 0, deltas[-period:], 0.0)
        losses = np.where(deltas[-period:] < 0, -deltas[-period:], 0.0)
        avg_gain = float(np.mean(gains))
        avg_loss = float(np.mean(losses))
        if avg_loss == 0:
            all_same = bool(np.all(deltas[-period:] == 0))
            rsi = 50.0 if all_same else 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
        setattr(ind, attr, rsi)

    # ---- KDJ(9,3,3)标准参数 ----


    if n >= 9:


        k_vals, d_vals = _kdj_full_series(low, high, close, 9, 3, 3)


        ind.kdj_k = float(k_vals[-1])


        ind.kdj_d = float(d_vals[-1])


        ind.kdj_j = float(3.0 * k_vals[-1] - 2.0 * d_vals[-1])


        # KDJ金叉/死叉


        for i in range(max(0, n - 10), n - 1):


            if k_vals[i] <= d_vals[i] and k_vals[i + 1] > d_vals[i + 1]:


                ind.kdj_cross = "golden"  # 记录KDJ金叉


                break


            if k_vals[i] >= d_vals[i] and k_vals[i + 1] < d_vals[i + 1]:


                ind.kdj_cross = "death"


                break


    else:


        ind.kdj_k = ind.kdj_d = ind.kdj_j = 50.0





    # ---- BOLL?20, 2? ----


    if n >= 20:


        mid = float(np.mean(close[-20:]))


        std = float(np.std(close[-20:], ddof=1))


        ind.boll_mid = mid


        ind.boll_upper = mid + 2 * std


        ind.boll_lower = mid - 2 * std


        ind.boll_width = (ind.boll_upper - ind.boll_lower) / mid * 100 if mid != 0 else 0.0


    else:


        ind.boll_mid = ind.last_close


        ind.boll_upper = ind.last_close * 1.05


        ind.boll_lower = ind.last_close * 0.95


        ind.boll_width = 10.0





    # ---- ATR(14) ----


    if n >= 15:


        tr = np.zeros(n)


        tr[0] = high[0] - low[0]


        for i in range(1, n):


            tr[i] = max(high[i] - low[i],


                        abs(high[i] - close[i - 1]),


                        abs(low[i] - close[i - 1]))


        ind.atr_14 = float(_ema(tr, 14)[-1]) if len(_ema(tr, 14)) > 0 else 0.0


    else:


        ind.atr_14 = float(np.mean(high - low)) if n > 0 else 0.0





    # ---- OBV ----


    if n >= 2:


        obv_vals = [0.0]


        for i in range(1, n):


            if close[i] > close[i - 1]:


                obv_vals.append(obv_vals[-1] + volume[i])


            elif close[i] < close[i - 1]:


                obv_vals.append(obv_vals[-1] - volume[i])


            else:


                obv_vals.append(obv_vals[-1])


        ind.obv = obv_vals[-1]


        if len(obv_vals) >= 5:


            if obv_vals[-1] > obv_vals[-5] * 1.05:


                ind.obv_trend = "up"


            elif obv_vals[-1] < obv_vals[-5] * 0.95:


                ind.obv_trend = "down"


            else:


                ind.obv_trend = "flat"





    # ---- VWMA(20) ----


    if n >= 20:


        vol_sum = float(np.sum(volume[-20:]))


        pv_sum = float(np.sum(close[-20:] * volume[-20:]))


        ind.vwma_20 = pv_sum / vol_sum if vol_sum != 0 else ind.last_close


    else:


        ind.vwma_20 = ind.last_close





    # ---- MA均线 ----


    if n >= 5:


        avg_vol_5 = float(np.mean(volume[-5:]))


        ind.vol_ratio = volume[last] / avg_vol_5 if avg_vol_5 != 0 else 1.0


    else:


        ind.vol_ratio = 1.0





    # ---- MA金叉/死叉检测(5/10和20) ----


    if n >= 11:


        # 股票买卖信号分析模块


        ma5_vals = []


        ma10_vals = []


        for i in range(n):


            s5 = max(0, i - 4)


            s10 = max(0, i - 9)


            ma5_vals.append(float(np.mean(close[s5:i + 1])))


            ma10_vals.append(float(np.mean(close[s10:i + 1])))


        for i in range(max(0, n - 20), n - 1):


            if ma5_vals[i] <= ma10_vals[i] and ma5_vals[i + 1] > ma10_vals[i + 1]:


                ind.ma5_ma10_cross = "golden"


                break


            if ma5_vals[i] >= ma10_vals[i] and ma5_vals[i + 1] < ma10_vals[i + 1]:


                ind.ma5_ma10_cross = "death"


                break


        else:


            ind.ma5_ma10_cross = "none"








    # ---- Support/Resistance ----


    try:
        from stock_signals._sr import compute_support_resistance
    except ImportError:
        from _sr import compute_support_resistance


    sr = compute_support_resistance(df)


    ind.support_1 = sr["support_1"]


    ind.support_2 = sr["support_2"]


    ind.resistance_1 = sr["resistance_1"]


    ind.resistance_2 = sr["resistance_2"]


    ind.swing_resistances = sr["swing_resistances"]


    ind.swing_supports = sr["swing_supports"]


    ind.ma_levels = sr["ma_levels"]


    ind.vwap_20 = sr["vwap"]





    # ---- Trend Phase ----


    try:
        from stock_signals._sr import compute_trend_phase
    except ImportError:
        from _sr import compute_trend_phase


    ind.trend_phase = compute_trend_phase(df, ind)





    # ---- VWAP (typical price weighted) ----


    if n >= 20:


        vol = df["volume"].values.astype(float)


        tp = (df["high"].values.astype(float) + df["low"].values.astype(float)) / 2


        vs = float(np.sum(vol[-20:]))


        tv = float(np.sum(tp[-20:] * vol[-20:]))


        ind.vwap_20 = tv / vs if vs > 0 else ind.last_close





    # ---- ATR % of price ----


    if ind.atr_14 > 0 and ind.last_close > 0:


        ind.atr_14_pct = ind.atr_14 / ind.last_close * 100





    # ---- Prev high/low (last 20 bars) ----


    if n >= 20:


        ind.prev_high = float(df["high"].iloc[-20:].max())


        ind.prev_low = float(df["low"].iloc[-20:].min())






    # ═══════════════════════════════════════════════════════════════
    # ADX (Average Directional Index)
    # ═══════════════════════════════════════════════════════════════
    if n >= 28:
        tr_arr = np.zeros(n)
        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        tr_arr[0] = high[0] - low[0]
        for i in range(1, n):
            hp = high[i] - high[i - 1]
            lm = low[i - 1] - low[i]
            tr_arr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
            if hp > lm and hp > 0:
                plus_dm[i] = hp
            elif lm > hp and lm > 0:
                minus_dm[i] = lm
        tr_exp = _ema(tr_arr, 14)
        pdi_exp = _ema(plus_dm, 14)
        mdi_exp = _ema(minus_dm, 14)
        dx_arr = np.zeros(n)
        for i in range(14, n):
            denom = pdi_exp[i] + mdi_exp[i]
            dx_arr[i] = 100.0 * abs(pdi_exp[i] - mdi_exp[i]) / denom if denom > 0 else 0.0
        adx_arr = _ema(dx_arr, 14)
        ind.adx = float(adx_arr[-1]) if len(adx_arr) > 0 else 0.0
        ind.plus_di = float(pdi_exp[-1]) if len(pdi_exp) > 0 else 0.0
        ind.minus_di = float(mdi_exp[-1]) if len(mdi_exp) > 0 else 0.0
    else:
        ind.adx, ind.plus_di, ind.minus_di = 0.0, 0.0, 0.0

    # ═══════════════════════════════════════════════════════════════
    # MACD & RSI Divergence Detection
    # ═══════════════════════════════════════════════════════════════
    if n >= 30:
        ema12 = _ema(close, 12)
        ema26 = _ema(close, 26)
        dif_s = ema12 - ema26
        dea_s = _ema(dif_s, 9)
        hist_s = 2.0 * (dif_s - dea_s)
        # MACD histogram divergence (5-bar lookback)
        if hist_s[-1] < hist_s[-2] and close[-1] > close[-2] and hist_s[-2] > 0:
            if hist_s[-1] < hist_s[-5] * 0.95:
                ind.macd_divergence = "bearish"
        elif hist_s[-1] > hist_s[-2] and close[-1] < close[-2] and hist_s[-2] < 0:
            if hist_s[-1] > hist_s[-5] * 1.05:
                ind.macd_divergence = "bullish"
        # RSI divergence
        deltas = np.diff(close)
        if len(deltas) >= 14:
            gains = np.where(deltas[-14:] > 0, deltas[-14:], 0.0)
            losses = np.where(deltas[-14:] < 0, -deltas[-14:], 0.0)
            ag = float(np.mean(gains))
            al = float(np.mean(losses))
            rsi_last = 100.0 - 100.0 / (1.0 + ag / al) if al > 0 else (100.0 if ag > 0 else 50.0)
            # Simple RSI divergence check
            if close[-1] > close[-5] and rsi_last < ind.rsi_14 * 0.97 and ind.rsi_14 > 50:
                ind.rsi_divergence = "bearish"
            elif close[-1] < close[-5] and rsi_last > ind.rsi_14 * 1.03 and ind.rsi_14 < 50:
                ind.rsi_divergence = "bullish"

    # ═══════════════════════════════════════════════════════════════
    # K-line Pattern Recognition
    # ═══════════════════════════════════════════════════════════════
    if n >= 3:
        for i in range(max(0, n - 5), n):
            o = float(df["open"].iloc[i])
            h = float(df["high"].iloc[i])
            l = float(df["low"].iloc[i])
            c = float(df["close"].iloc[i])
            body = abs(c - o)
            rng = h - l
            upper_w = h - max(o, c)
            lower_w = min(o, c) - l
            if rng > 0:
                # Hammer / Inverted Hammer
                if lower_w >= body * 2 and upper_w <= body * 0.5 and body / rng > 0.2:
                    if c > o:
                        ind.candle_pattern, ind.candle_pattern_name = "bullish_hammer", "锤子线(看涨)"
                    else:
                        ind.candle_pattern, ind.candle_pattern_name = "inverted_hammer", "倒锤子线"
                # Shooting Star
                if upper_w >= body * 2 and lower_w <= body * 0.5 and body / rng > 0.2:
                    ind.candle_pattern, ind.candle_pattern_name = "shooting_star", "流星线(看跌)"
                # Engulfing
                if i > 0:
                    po = float(df["open"].iloc[i - 1])
                    pc = float(df["close"].iloc[i - 1])
                    pb = pc - po
                    cb = c - o
                    if pb < 0 and cb > 0 and o <= pc and c >= po:
                        ind.candle_pattern, ind.candle_pattern_name = "bullish_engulfing", "阳包阴(看涨)"
                    elif pb > 0 and cb < 0 and o >= pc and c <= po:
                        ind.candle_pattern, ind.candle_pattern_name = "bearish_engulfing", "阴包阳(看跌)"

    # ═══════════════════════════════════════════════════════════════
    # Gap Analysis
    # ═══════════════════════════════════════════════════════════════
    if n >= 2:
        prev_close_val = float(close[-2])
        curr_open = float(df["open"].iloc[-1])
        if prev_close_val > 0:
            gap = (curr_open - prev_close_val) / prev_close_val * 100
            ind.gap_pct = gap
            if gap > 1.5:
                ind.gap_type = "gap_up"
            elif gap < -1.5:
                ind.gap_type = "gap_down"
            else:
                ind.gap_type = "none"
            if ind.gap_type != "none":
                recent = close[-min(10, n):]
                if ind.gap_type == "gap_up" and float(np.min(recent)) <= prev_close_val * 1.005:
                    ind.gap_filled = True
                elif ind.gap_type == "gap_down" and float(np.max(recent)) >= prev_close_val * 0.995:
                    ind.gap_filled = True

    # ═══════════════════════════════════════════════════════════════
    # Volatility Regime Classification
    # ═══════════════════════════════════════════════════════════════
    if n >= 60:
        atr_pct = ind.atr_14 / ind.last_close * 100 if ind.last_close > 0 else 0
        ind.vol_regime_score = atr_pct
        if atr_pct > 5.0:
            ind.vol_regime = "high"
        elif atr_pct < 1.5:
            ind.vol_regime = "low"
        else:
            ind.vol_regime = "normal"
    else:
        ind.vol_regime = "normal"
        ind.vol_regime_score = ind.atr_14 / ind.last_close * 100 if ind.last_close > 0 else 0


    # ═══════════════════════════════════════════════════════════════
    # TD Sequential (9转信号)
    # ═══════════════════════════════════════════════════════════════
    if n >= 9:
        td_buy_count = 0
        td_sell_count = 0
        for i in range(4, n):
            if close[i] < close[i - 4]:
                td_buy_count += 1
                td_sell_count = 0
            elif close[i] > close[i - 4]:
                td_sell_count += 1
                td_buy_count = 0
            else:
                td_buy_count = 0
                td_sell_count = 0
            if td_buy_count >= 9:
                ind.td_buy_count = min(td_buy_count, 9)
                if td_buy_count == 9:
                    ind.td_buy_setup = True
            if td_sell_count >= 9:
                ind.td_sell_count = min(td_sell_count, 9)
                if td_sell_count == 9:
                    ind.td_sell_setup = True
        # TD Turn: 10th bar breaks setup direction
        if n >= 10:
            if ind.td_buy_setup:
                if close[-1] > close[-5]:
                    ind.td_turn = "buy_turn"
            if ind.td_sell_setup:
                if close[-1] < close[-5]:
                    ind.td_turn = "sell_turn"

    
    # ── v2.4: 扩展度 & 回调检测 ────────────────────────────────────────
    # 距N日高/低点
    lookback = min(252, len(df))  # 最多看一年
    df_look = df.tail(lookback)
    high_n = df_look['high'].max()
    low_n = df_look['low'].min()
    last_close = ind.last_close
    if high_n > 0:
        ind.price_to_high_pct = (last_close - high_n) / high_n * 100  # 负值=低于高点
    if low_n > 0:
        ind.price_to_low_pct = (last_close - low_n) / low_n * 100     # 正值=高于低点

    # MA5与MA20偏离度（衡量短期是否过度延伸）
    if ind.ma20 > 0:
        ind.ma5_ma20_gap = (ind.ma5 - ind.ma20) / ind.ma20 * 100

    # MACD金叉距今几根K线
    if ind.macd_dif_dea_cross == 'golden':
        # 找金叉发生在第几根
        df_calc = df.tail(40)
        dif_arr = df_calc['macd_dif'].values if 'macd_dif' in df_calc.columns else []
        if len(dif_arr) > 2:
            for i in range(1, len(dif_arr)):
                if dif_arr[i-1] <= df_calc['macd_dea'].values[i-1] and dif_arr[i] > df_calc['macd_dea'].values[i]:
                    ind.macd_cross_bar = len(dif_arr) - 1 - i
                    break
    elif ind.macd_dif_dea_cross == 'death':
        df_calc = df.tail(40)
        dif_arr = df_calc['macd_dif'].values if 'macd_dif' in df_calc.columns else []
        if len(dif_arr) > 2:
            for i in range(1, len(dif_arr)):
                if dif_arr[i-1] >= df_calc['macd_dea'].values[i-1] and dif_arr[i] < df_calc['macd_dea'].values[i]:
                    ind.macd_cross_bar = len(dif_arr) - 1 - i
                    break


    # ── VCP (Volatility Contraction Pattern) 检测 ──────────────────────
    try:
        from ._vcp import detect_vcp
        vcp_res = detect_vcp(df, lookback=100)
        ind.vcp_detected = vcp_res.detected
        ind.vcp_contractions = vcp_res.contractions
        ind.vcp_pivot_point = vcp_res.pivot_point
        ind.vcp_pattern_width = vcp_res.pattern_width
        ind.vcp_volume_drying = vcp_res.volume_drying
        ind.vcp_quality = vcp_res.quality
    except Exception:
        ind.vcp_detected = False
        ind.vcp_contractions = 0
        ind.vcp_pivot_point = 0.0
        ind.vcp_pattern_width = 0.0
        ind.vcp_volume_drying = False
        ind.vcp_quality = "none"

    # ── 相对强度 (RS) 评分 ──────────────────────────────────────────
    # 计算52周高点和低点
    _52w = min(252, n)
    if n >= 20:
        _recent_high = float(np.max(close[-252:])) if n >= 252 else float(np.max(close))
        _recent_low = float(np.min(close[-252:])) if n >= 252 else float(np.min(close))
        if _recent_high > 0:
            ind.distance_from_52w_high = round((ind.last_close - _recent_high) / _recent_high * 100, 2)
            ind.distance_from_52w_low = round((ind.last_close - _recent_low) / _recent_low * 100, 2)
            ind.rs_percentile = round((ind.last_close - _recent_low) / (_recent_high - _recent_low) * 100, 1) if _recent_high > _recent_low else 50.0
            ind.rs_rating = int(ind.rs_percentile)
    
    # Trend Template 验证 (Minervini 8点模板)
    _passed = True
    if ind.ma200 > 0:
        if close[-1] <= ind.ma20: _passed = False
        if close[-1] <= ind.ma60: _passed = False
        if close[-1] <= ind.ma200: _passed = False
        if ind.ma60 <= ind.ma200: _passed = False
        if n >= 200:
            _ma200_prev = float(np.mean(close[-201:-1]))
            if ind.ma200 <= _ma200_prev: _passed = False
    ind.trend_template_pass = _passed


    # ── Episodic Pivot (事件性转折) 检测 ───────────────────────────
    try:
        from ._episodic_pivot import detect_episodic_pivot
        ep_res = detect_episodic_pivot(df, lookback=60)
        ind.ep_detected = ep_res.detected
        ind.ep_gap_up_pct = ep_res.gap_up_pct
        ind.ep_volume_spike = ep_res.volume_spike
        ind.ep_catalyst_score = ep_res.catalyst_score
        ind.ep_quality = ep_res.quality
    except Exception:
        ind.ep_detected = False
        ind.ep_gap_up_pct = 0.0
        ind.ep_volume_spike = 0.0
        ind.ep_catalyst_score = 0.0
        ind.ep_quality = "none"

    return ind








def _ema(arr, period):


    if len(arr) == 0:


        return np.array([])


    result = np.zeros(len(arr))


    k = 2.0 / (period + 1)


    result[0] = arr[0]


    for i in range(1, len(arr)):


        result[i] = arr[i] * k + result[i - 1] * (1 - k)


    return result








def _kdj_full_series(low, high, close, n_period, k_period, d_period):


    """计算KDJ指标: RSV->K->D->J"""


    k_vals = np.zeros(len(close))


    d_vals = np.zeros(len(close))


    prev_k = 50.0


    prev_d = 50.0


    for i in range(len(close)):


        if i < n_period - 1:


            k_vals[i] = prev_k


            d_vals[i] = prev_d


            continue


        window_high = high[i - n_period + 1:i + 1].max()


        window_low = low[i - n_period + 1:i + 1].min()


        curr_close = close[i]


        if window_high == window_low:


            rsv = 50.0


        else:


            rsv = (curr_close - window_low) / (window_high - window_low) * 100


        prev_k = (k_period - 1) / k_period * prev_k + 1.0 / k_period * rsv


        prev_d = (d_period - 1) / d_period * prev_d + 1.0 / d_period * prev_k


        k_vals[i] = prev_k


        d_vals[i] = prev_d


    return k_vals, d_vals








def signal_summary(ind: Indicators) -> List[tuple]:


    signals = []


    # 趋势


    if ind.ma5 > ind.ma10 > ind.ma20 > ind.ma60:


        signals.append(("趋势", "均线多头排列，强势上升"))


    elif ind.ma5 < ind.ma10 < ind.ma20 < ind.ma60:


        signals.append(("趋势", "均线空头排列，弱势下跌"))


    elif ind.ma5_ma10_cross == "golden":


        signals.append(("趋势", "MA5/MA10 金叉，短期转强"))


    elif ind.ma5_ma10_cross == "death":


        signals.append(("趋势", "MA5/MA10 死叉，短期转弱"))


    elif ind.ma5 > ind.ma20:


        signals.append(("趋势", "MA5 在MA20之上，短期偏强"))


    else:


        signals.append(("趋势", "均线肩扭，方向不明"))


    # 动量


    if ind.macd_dif_dea_cross == "golden":


        signals.append(("动量", "MACD DIF 上突DEA，金叉"))


    elif ind.macd_dif_dea_cross == "death":


        signals.append(("动量", "MACD DIF 下突DEA，死叉"))


    if ind.rsi_14 > 70:


        signals.append(("动量", f"RSI(14)={ind.rsi_14:.1f}，超买区域"))


    elif ind.rsi_14 < 30:


        signals.append(("动量", f"RSI(14)={ind.rsi_14:.1f}，超卖区域"))


    if ind.kdj_k > 80:


        signals.append(("动量", f"KDJ K={ind.kdj_k:.1f}，超买"))


    elif ind.kdj_k < 20:


        signals.append(("动量", f"KDJ K={ind.kdj_k:.1f}，超卖"))


    # 能量


    if ind.obv_trend == "up":


        signals.append(("能量", "OBV 持续上升，资金持续涌入"))


    elif ind.obv_trend == "down":


        signals.append(("能量", "OBV 持续下降，资金持续涌出"))


    else:


        signals.append(("能量", "OBV 旋转平衡"))


    if ind.vol_ratio > 1.5:


        signals.append(("能量", f"量比={ind.vol_ratio:.2f}，放量明显"))


    elif ind.vol_ratio < 0.5:


        signals.append(("能量", f"量比={ind.vol_ratio:.2f}，缩量明显"))


    # 波动率


    if ind.last_close > ind.boll_upper * 0.98:


        signals.append(("波动", "价格超过布林上轨，短期超买"))


    elif ind.last_close < ind.boll_lower * 1.02:


        signals.append(("波动", "价格突破布林下轨，短期超卖"))


    elif ind.boll_width < 5:


        signals.append(("波动", f"布林幅度={ind.boll_width:.1f}%，窄幅敲合，突破在即"))



    # ADX trend strength
    if ind.adx > 0:
        if ind.adx > 40:
            signals.append(("趋势强度", f"ADX={ind.adx:.1f}，强趋势，适合趋势跟踪"))
        elif ind.adx > 25:
            signals.append(("趋势强度", f"ADX={ind.adx:.1f}，中等趋势，可跟踪"))
        else:
            signals.append(("趋势强度", f"ADX={ind.adx:.1f}，低趋势，震荡市，慎用趋势策略"))
        if ind.plus_di > ind.minus_di * 1.5:
            signals.append(("ADX方向", f"+DI={ind.plus_di:.1f} > -DI={ind.minus_di:.1f}，多头占优"))
        elif ind.minus_di > ind.plus_di * 1.5:
            signals.append(("ADX方向", f"-DI={ind.minus_di:.1f} > +DI={ind.plus_di:.1f}，空头占优"))

    # Divergence
    if ind.macd_divergence != "none":
        side = "看跌" if ind.macd_divergence == "bearish" else "看涨"
        signals.append(("背离", f"MACD{side}背离，价格与动量分歧"))
    if ind.rsi_divergence != "none":
        side = "看跌" if ind.rsi_divergence == "bearish" else "看涨"
        signals.append(("背离", f"RSI{side}背离，短期回调风险"))

    # K-line patterns
    if ind.candle_pattern != "none" and ind.candle_pattern_name:
        signals.append(("K线形态", ind.candle_pattern_name))

    # Gaps
    if ind.gap_type != "none" and abs(ind.gap_pct) > 0.01:
        direction = "向上" if ind.gap_type == "gap_up" else "向下"
        filled = "已回补" if ind.gap_filled else "未回补"
        signals.append(("缺口", f"缺口{direction}{ind.gap_pct:+.1f}%，{filled}"))


    # TD Sequential (9转信号)
    if ind.td_buy_setup:
        signals.append(("9转信号", f"TD买入序列完成(第9根)，当前计数={ind.td_buy_count}"))
    elif ind.td_buy_count > 0:
        signals.append(("9转信号", f"TD买入序列进行中({ind.td_buy_count}/9)，关注回调"))
    if ind.td_sell_setup:
        signals.append(("9转信号", f"TD卖出序列完成(第9根)，当前计数={ind.td_sell_count}"))
    elif ind.td_sell_count > 0:
        signals.append(("9转信号", f"TD卖出序列进行中({ind.td_sell_count}/9)，关注反弹"))
    if ind.td_turn == "buy_turn":
        signals.append(("9转信号", "TD买入Turn确认，反转看涨信号"))
    elif ind.td_turn == "sell_turn":
        signals.append(("9转信号", "TD卖出Turn确认，反转看跌信号"))

    return signals





