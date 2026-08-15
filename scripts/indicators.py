#!/usr/bin/env python3


"""


股票买卖信号分析模块





? Futu OpenAPI ?? K ????? pandas/numpy 股票买卖信号分析模块???


??? LLM股票买卖信号分析模块?


"""


from __future__ import annotations





import sys


import os as _os


from dataclasses import dataclass, field


from typing import List, Optional





import pandas as pd


import numpy as np





sys.path.insert(


    0,


    _os.path.normpath(


        _os.path.join(


            _os.path.dirname(_os.path.abspath(__file__)),


            "..", "..", "futuapi", "scripts",


        )


    ),


)


from common import create_quote_context, check_ret, safe_close, KLType, AuType, RET_OK





KTYPE_MAP = {


    "1m": KLType.K_1M, "3m": KLType.K_3M, "5m": KLType.K_5M,


    "15m": KLType.K_15M, "30m": KLType.K_30M, "60m": KLType.K_60M,


    "1d": KLType.K_DAY, "1w": KLType.K_WEEK, "1M": KLType.K_MON,


}








def fetch_kline(code: str, ktype: str = "1d", num: int = 300) -> pd.DataFrame:


    kl_type = KTYPE_MAP.get(ktype, KLType.K_DAY)


    ctx = None


    try:


        ctx = create_quote_context()


        ret, data, _ = ctx.request_history_kline(


            code, ktype=kl_type, autype=AuType.QFQ, max_count=num,


        )


        check_ret(ret, data, ctx, "获取K线")


        if data is None or data.empty:


            return pd.DataFrame()


        df = data.copy()


        df["time"] = df["time_key"].astype(str)


        for col in ("open", "high", "low", "close", "volume"):


            df[col] = pd.to_numeric(df[col], errors="coerce")


        df = df[["time", "open", "high", "low", "close", "volume"]].dropna(subset=["close"])


        return df.sort_values("time").reset_index(drop=True)


    except Exception as e:


        print(f"[ERROR] 获取K线数据失败 {code}: {e}", file=sys.stderr)


        return pd.DataFrame()


    finally:


        safe_close(ctx)








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


    return signals





