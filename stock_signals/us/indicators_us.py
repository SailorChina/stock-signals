# -*- coding: utf-8 -*-
"""
美股技术指标分析模块
数据源: akshare stock_us_daily (与主模块 indicators.py 保持一致)
完全独立模块，不依赖 py_mini_racer
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger("tech-signal-FUTU-skill")
_kline_cache_us: dict = {}


@dataclass
class IndicatorsUS:
    code: str = ""
    ktype: str = "1d"
    df: pd.DataFrame = field(default_factory=pd.DataFrame)
    last_close: float = 0.0
    last_time: str = ""
    prev_close: float = 0.0
    day_change_pct: float = 0.0
    ma5: float = 0.0; ma10: float = 0.0; ma20: float = 0.0
    ma60: float = 0.0; ma120: float = 0.0; ma200: float = 0.0
    macd_dif: float = 0.0; macd_dea: float = 0.0; macd_hist: float = 0.0
    macd_dif_dea_cross: str = ""
    rsi_6: float = 0.0; rsi_12: float = 0.0; rsi_14: float = 0.0; rsi_24: float = 0.0
    kdj_k: float = 0.0; kdj_d: float = 0.0; kdj_j: float = 0.0
    boll_mid: float = 0.0; boll_upper: float = 0.0; boll_lower: float = 0.0
    boll_width: float = 0.0
    atr_14: float = 0.0
    obv: float = 0.0; obv_trend: str = "flat"
    vol_ratio: float = 0.0
    ma5_ma10_cross: str = ""
    price_vs_ma20: float = 0.0
    price_vs_ma60: float = 0.0
    price_vs_ma200: float = 0.0
    adx: float = 0.0; plus_di: float = 0.0; minus_di: float = 0.0
    distance_from_52w_high: float = 0.0
    distance_from_52w_low: float = 0.0
    vol_regime: str = "normal"
    vol_regime_score: float = 50.0
    td_buy_setup: bool = False; td_sell_setup: bool = False
    td_buy_count: int = 0; td_sell_count: int = 0
    td_turn: str = "none"
    gap_pct: float = 0.0; gap_type: str = "none"


def _ema(series, period):
    if len(series) < period: return series.copy()
    alpha = 2.0 / (period + 1.0)
    result = np.empty(len(series))
    result[0] = series[0]
    for i in range(1, len(series)):
        result[i] = series[i] * alpha + result[i-1] * (1 - alpha)
    return result


def _kdj_series(low, high, close, n=9):
    k_vals = np.zeros(len(close))
    d_vals = np.zeros(len(close))
    for i in range(n-1, len(close)):
        hn = high[i-n+1:i+1]
        ln = low[i-n+1:i+1]
        rsv = (close[i] - np.min(ln)) / (np.max(hn) - np.min(ln)) * 100 if np.max(hn) != np.min(ln) else 50
        if i == n-1:
            k_vals[i] = 50; d_vals[i] = 50
        else:
            k_vals[i] = 2/3 * k_vals[i-1] + 1/3 * rsv
            d_vals[i] = 2/3 * d_vals[i-1] + 1/3 * k_vals[i]
    return k_vals, d_vals


def fetch_kline_us(code: str, num: int = 500) -> pd.DataFrame:
    """从 akshare 获取美股日K数据"""
    cache_key = f"us_{code}_{num}"
    if cache_key in _kline_cache_us:
        return _kline_cache_us[cache_key]
    try:
        import akshare as ak
        symbol = code.split('.')[-1].upper()
        df = ak.stock_us_daily(symbol=symbol)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.rename(columns={'date': 'time'})
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        for col in ('open','high','low','close','volume'):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                df[col] = 0.0
        if 'time' not in df.columns:
            df['time'] = pd.date_range(end=pd.Timestamp.now(), periods=len(df), freq='D')
        df = df[['time','open','high','low','close','volume']].dropna(subset=['close'])
        df = df[df['close'] > 0]
        if len(df) < 60:
            return pd.DataFrame()
        df = df.tail(num).reset_index(drop=True)
        _kline_cache_us[cache_key] = df
        return df
    except Exception as e:
        logger.warning(f"  akshare {code} 失败: {e}")
        return pd.DataFrame()


def compute_indicators_us(df: pd.DataFrame, code: str = "", ktype: str = "1d") -> IndicatorsUS:
    ind = IndicatorsUS(code=code, ktype=ktype, df=df)
    if df is None or df.empty or len(df) < 60:
        return ind
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    volume = df["volume"].values.astype(float)
    n = len(close)
    ind.last_close = float(close[-1])
    ind.prev_close = float(close[-2]) if n > 1 else 0.0
    ind.day_change_pct = (close[-1] - close[-2]) / close[-2] * 100 if n > 1 and close[-2] > 0 else 0.0
    ind.last_time = str(df.iloc[-1]["time"])[:10]
    for period, attr in [(5,"ma5"),(10,"ma10"),(20,"ma20"),(60,"ma60"),(120,"ma120"),(200,"ma200")]:
        setattr(ind, attr, float(np.mean(close[-period:])) if n >= period else float(np.mean(close)))
    if n >= 12:
        prev_ma5 = np.mean(close[-12:-2])
        prev_ma10 = np.mean(close[-12:-2])
        if prev_ma5 <= prev_ma10 and ind.ma5 > ind.ma10:
            ind.ma5_ma10_cross = "golden"
        elif prev_ma5 >= prev_ma10 and ind.ma5 < ind.ma10:
            ind.ma5_ma10_cross = "death"
    if n >= 35:
        e12 = _ema(close, 12); e26 = _ema(close, 26)
        dif = e12 - e26; dea = _ema(dif, 9)
        ind.macd_dif = float(dif[-1]); ind.macd_dea = float(dea[-1]); ind.macd_hist = float(dif[-1] - dea[-1])
        if n >= 36:
            if float(dif[-2]) <= float(dea[-2]) and ind.macd_dif > ind.macd_dea:
                ind.macd_dif_dea_cross = "golden"
            elif float(dif[-2]) >= float(dea[-2]) and ind.macd_dif < ind.macd_dea:
                ind.macd_dif_dea_cross = "death"
    for period in [6,12,14,24]:
        if n >= period + 1:
            delta = np.diff(close)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            rs = np.mean(gain[-period:]) / np.mean(loss[-period:]) if np.mean(loss[-period:]) > 0 else 100
            setattr(ind, f"rsi_{period}", float(100 - 100/(1+rs)))
        else:
            setattr(ind, f"rsi_{period}", 50.0)
    if n >= 10:
        k_vals, d_vals = _kdj_series(low, high, close, 9)
        ind.kdj_k = float(k_vals[-1]); ind.kdj_d = float(d_vals[-1]); ind.kdj_j = float(3*k_vals[-1] - 2*d_vals[-1])
    else:
        ind.kdj_k = ind.kdj_d = ind.kdj_j = 50.0
    if n >= 20:
        mid = np.mean(close[-20:]); std = np.std(close[-20:])
        ind.boll_mid = float(mid); ind.boll_upper = float(mid + 2*std); ind.boll_lower = float(mid - 2*std)
        ind.boll_width = float((ind.boll_upper - ind.boll_lower) / mid * 100) if mid > 0 else 0.0
    if n >= 15:
        tr = np.zeros(n)
        for i in range(n):
            if i == 0: tr[i] = high[i] - low[i]
            else: tr[i] = max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
        ind.atr_14 = float(np.mean(tr[-14:]))
    else:
        ind.atr_14 = ind.last_close * 0.02
    obv_v = 0.0
    for i in range(1, min(20, n)):
        if close[i] > close[i-1]: obv_v += volume[i]
        elif close[i] < close[i-1]: obv_v -= volume[i]
    ind.obv = float(obv_v)
    ind.obv_trend = "up" if obv_v > 0 else ("down" if obv_v < 0 else "flat")
    if n >= 6:
        avg_vol = np.mean(volume[-6:-1]) if np.mean(volume[-6:-1]) > 0 else 1.0
        ind.vol_ratio = float(volume[-1] / avg_vol)
    else:
        ind.vol_ratio = 1.0
    if ind.ma20 > 0: ind.price_vs_ma20 = (ind.last_close - ind.ma20) / ind.ma20 * 100
    if ind.ma60 > 0: ind.price_vs_ma60 = (ind.last_close - ind.ma60) / ind.ma60 * 100
    if ind.ma200 > 0: ind.price_vs_ma200 = (ind.last_close - ind.ma200) / ind.ma200 * 100
    if n >= 30:
        tr_arr = np.zeros(n)
        dm_plus = np.zeros(n); dm_minus = np.zeros(n)
        for i in range(1, n):
            tr_arr[i] = max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
            up = high[i] - high[i-1]; down = low[i-1] - low[i]
            dm_plus[i] = up if up > down and up > 0 else 0
            dm_minus[i] = down if down > up and down > 0 else 0
        atr_val = np.mean(tr_arr[-14:]) if n >= 14 else np.mean(tr_arr[1:])
        di_plus = 100 * np.mean(dm_plus[-14:]) / atr_val if atr_val > 0 else 0
        di_minus = 100 * np.mean(dm_minus[-14:]) / atr_val if atr_val > 0 else 0
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus) if (di_plus + di_minus) > 0 else 0
        ind.adx = float(dx); ind.plus_di = float(di_plus); ind.minus_di = float(di_minus)
    else:
        ind.adx = 25.0; ind.plus_di = 25.0; ind.minus_di = 25.0
    lookback = min(252, n)
    if lookback >= 20:
        ind.distance_from_52w_high = float((ind.last_close - np.max(high[-lookback:])) / np.max(high[-lookback:]) * 100)
        ind.distance_from_52w_low = float((ind.last_close - np.min(low[-lookback:])) / np.min(low[-lookback:]) * 100)
    if n >= 60:
        returns = np.diff(np.log(close[-60:]))
        vol_20d = float(np.std(returns) * np.sqrt(252) * 100)
        if vol_20d < 15: ind.vol_regime = "low"; ind.vol_regime_score = 30.0
        elif vol_20d > 30: ind.vol_regime = "high"; ind.vol_regime_score = 70.0
        else: ind.vol_regime = "normal"; ind.vol_regime_score = 50.0
    if n >= 10:
        bc = sc = 0
        for i in range(4, n):
            if close[i] < close[i-4]: bc += 1
            else: bc = 0
            if bc >= 9: ind.td_buy_setup = True; ind.td_buy_count = bc
            if close[i] > close[i-4]: sc += 1
            else: sc = 0
            if sc >= 9: ind.td_sell_setup = True; ind.td_sell_count = sc
        if ind.td_buy_setup and n >= 11 and close[-1] > close[-2]: ind.td_turn = "buy_turn"
        elif ind.td_sell_setup and n >= 11 and close[-1] < close[-2]: ind.td_turn = "sell_turn"
    if n >= 2:
        prev_c = close[-2]; curr_o = float(df.iloc[-1]["open"])
        ind.gap_pct = (curr_o - prev_c) / prev_c * 100 if prev_c > 0 else 0
        if ind.gap_pct > 1.5: ind.gap_type = "gap_up"
        elif ind.gap_pct < -1.5: ind.gap_type = "gap_down"
    return ind
