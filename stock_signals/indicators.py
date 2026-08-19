# -*- coding: utf-8 -*-
"""
股票技术指标分析模块
数据源: A股=Sina+akshare fallback, HK/US=akshare daily
"""
from __future__ import annotations
import sys, os, time, logging
from dataclasses import dataclass, field
from typing import List, Optional
import pandas as pd
import numpy as np
logger = logging.getLogger("stock-signals")
_kline_cache = {}
for _k in list(os.environ.keys()):
    if 'proxy' in _k.lower():
        os.environ.pop(_k, None)
os.environ.setdefault('no_proxy', '*')
os.environ.setdefault('NO_PROXY', '*')

KTYPE_MAP = {"1m":"1m","3m":"3m","5m":"5m","15m":"15m","30m":"30m","60m":"60m","1d":"1d","1w":"1w","1M":"1M"}

def _code_to_sina(symbol):
    parts = symbol.split('.')
    if len(parts) != 2: return ""
    p, n = parts[0].lower(), parts[1]
    if p in ('sh','sz','bj'): return p + n.lower()
    return ""

def _code_to_akshare(symbol, market):
    parts = symbol.split('.')
    if len(parts) != 2: return ""
    _, n = parts
    if market == 'HK': return n.zfill(5)
    elif market == 'US': return n.upper()
    return ""

def _fetch_sina_kline(sina_symbol, num=300):
    import urllib.request, json
    for attempt in range(3):
        try:
            url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_symbol}&scale=240&ma=no&datalen={num}"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)","Referer":"http://finance.sina.com.cn/"})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode())
            if not data or not isinstance(data, list):
                return pd.DataFrame()
            df = pd.DataFrame(data)
            df["time"] = df["day"]
            for col in ("open","high","low","close","volume"):
                df[col] = pd.to_numeric(df[col], errors="coerce")
            return df[["time","open","high","low","close","volume"]].sort_values("time").reset_index(drop=True)
        except urllib.error.HTTPError as e:
            if e.code == 456:
                logger.debug(f"  Sina 456 rate limit, retry {attempt+1}/3")
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
    return pd.DataFrame()

def _fetch_akshare_kline(symbol, market, num=300):
    import akshare as ak
    ak_code = _code_to_akshare(symbol, market)
    if not ak_code: return pd.DataFrame()
    try:
        if market == "HK":
            df = ak.stock_hk_daily(symbol=ak_code, adjust="qfq")
        elif market == "US":
            df = ak.stock_us_daily(symbol=ak_code, adjust="qfq")
        else:
            return pd.DataFrame()
        if df is None or df.empty:
            return pd.DataFrame()
        col_map = {}
        for c in df.columns:
            cl = str(c).lower().strip()
            if cl in ('date','datetime'): col_map[c] = 'time'
            elif cl == 'open' or cl == '开盘': col_map[c] = 'open'
            elif cl == 'high' or cl == '最高': col_map[c] = 'high'
            elif cl == 'low' or cl == '最低': col_map[c] = 'low'
            elif cl == 'close' or cl == '收盘': col_map[c] = 'close'
            elif cl == 'volume' or cl == '成交量': col_map[c] = 'volume'
        if col_map:
            df = df.rename(columns=col_map)
        for col in ('open','high','low','close','volume'):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                df[col] = 0.0
        if 'time' not in df.columns:
            df['time'] = df.index.astype(str)
        return df[["time","open","high","low","close","volume"]].sort_values("time").reset_index(drop=True)
    except Exception as e:
        logger.warning(f"  akshare {market} K-line failed {symbol}: {e}")
        return pd.DataFrame()

def fetch_kline(code, ktype="1d", num=300):
    cache_key = f"{code}_{num}"
    if cache_key in _kline_cache:
        return _kline_cache[cache_key]
    parts = code.split('.')
    if len(parts) != 2:
        return pd.DataFrame()
    market, num_str = parts[0].upper(), parts[1]
    try:
        if market in ("SH", "SZ", "BJ", "A"):
            sina_sym = _code_to_sina(code)
            if sina_sym:
                df = _fetch_sina_kline(sina_sym, num)
                if not df.empty:
                    _kline_cache[cache_key] = df
                    return df
            # Fallback to akshare
            try:
                import akshare as ak
                t0 = time.time()
                df = ak.stock_zh_a_daily(symbol=sina_sym or code.replace('.',''), adjust='qfq')
                dt = time.time() - t0
                if df is not None and not df.empty:
                    col_map = {}
                    for c in df.columns:
                        cl = str(c).lower().strip()
                        if cl in ('date','datetime'): col_map[c] = 'time'
                        elif cl in ('open','开盘'): col_map[c] = 'open'
                        elif cl in ('high','最高'): col_map[c] = 'high'
                        elif cl in ('low','最低'): col_map[c] = 'low'
                        elif cl in ('close','收盘'): col_map[c] = 'close'
                        elif cl in ('volume','成交量'): col_map[c] = 'volume'
                    if col_map: df = df.rename(columns=col_map)
                    for col in ('open','high','low','close','volume'):
                        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
                        else: df[col] = 0.0
                    if 'time' not in df.columns: df['time'] = df.index.astype(str)
                    df = df[["time","open","high","low","close","volume"]].sort_values("time").reset_index(drop=True)
                    _kline_cache[cache_key] = df
                    return df
            except Exception as e2:
                logger.debug(f"  akshare A fallback failed {code}: {e2}")
        elif market == "HK":
            df = _fetch_akshare_kline(code, "HK", num)
            _kline_cache[cache_key] = df
            if not df.empty: return df
        elif market == "US":
            df = _fetch_akshare_kline(code, "US", num)
            _kline_cache[cache_key] = df
            if not df.empty: return df
    except Exception as e:
        logger.error(f"[ERROR] K线获取失败 {code}: {e}")
    return pd.DataFrame()

def fetch_realtime(code):
    parts = code.split('.')
    if len(parts) != 2: return {}
    market, num = parts[0].upper(), parts[1]
    try:
        if market in ("SH","SZ","BJ","A"):
            sina_sym = _code_to_sina(code)
            if sina_sym:
                import urllib.request
                url = f"https://hq.sinajs.cn/list={sina_sym}"
                req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
                resp = urllib.request.urlopen(req, timeout=5)
                data = resp.read().decode('gbk')
                if '=' in data and '"' in data:
                    vals = data.split('="')[-1].strip().rstrip(';"').split(',')
                    if len(vals) > 3:
                        return {"code":code,"name":vals[0],"price":float(vals[3]) if vals[3] else 0}
        elif market == "HK":
            import urllib.request
            hk_sym = num.zfill(5)
            url = f"https://qt.gtimg.cn/q=hk{hk_sym}"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=5)
            data = resp.read().decode('gbk')
            if '~' in data and 'none_match' not in data:
                parts_d = data.split('=')[-1].strip('\"').split('~')
                if len(parts_d) > 3:
                    return {"code":code,"name":parts_d[1],"price":float(parts_d[3]) if parts_d[3] else 0}
        elif market == "US":
            import urllib.request
            us_sym = num.lower()
            url = f"https://qt.gtimg.cn/q=us_{us_sym}"
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=5)
            data = resp.read().decode('gbk')
            if '~' in data and 'none_match' not in data:
                parts_d = data.split('=')[-1].strip('\"').split('~')
                if len(parts_d) > 3:
                    return {"code":code,"name":parts_d[1],"price":float(parts_d[3]) if parts_d[3] else 0}
    except Exception as e:
        logger.debug(f"  实时行情失败 {code}: {e}")
    return {}

def _ema(series, period):
    if len(series) < period: return series
    alpha = 2.0 / (period + 1.0)
    result = np.zeros_like(series)
    result[0] = series[0]
    for i in range(1, len(series)):
        result[i] = series[i] * alpha + result[i-1] * (1 - alpha)
    return result

def _kdj_full_series(low, high, close, n=9, m1=3, m2=3):
    k_vals = np.zeros(len(close))
    d_vals = np.zeros(len(close))
    for i in range(n-1, len(close)):
        hn = high[i-n+1:i+1]
        ln = low[i-n+1:i+1]
        rsv = (close[i] - np.min(ln)) / (np.max(hn) - np.min(ln)) * 100 if np.max(hn) != np.min(ln) else 50
        if i == n-1:
            k_vals[i] = 50
            d_vals[i] = 50
        else:
            k_vals[i] = 2/3 * k_vals[i-1] + 1/3 * rsv
            d_vals[i] = 2/3 * d_vals[i-1] + 1/3 * k_vals[i]
    return k_vals, d_vals

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
    ma5_ma10_cross: str = ""
    macd_dif_dea_cross: str = ""
    price_vs_ma20: float = 0.0
    price_vs_ma60: float = 0.0
    price_vs_ma200: float = 0.0
    adx: float = 0.0
    plus_di: float = 0.0
    minus_di: float = 0.0
    macd_divergence: str = "none"
    rsi_divergence: str = "none"
    candle_pattern: str = "none"
    candle_pattern_name: str = ""
    gap_pct: float = 0.0
    gap_type: str = "none"
    gap_filled: bool = False
    vol_regime: str = "normal"
    vol_regime_score: float = 50.0
    td_buy_setup: bool = False
    td_sell_setup: bool = False
    td_buy_count: int = 0
    td_sell_count: int = 0
    td_turn: str = "none"
    vcp_detected: bool = False
    vcp_contractions: int = 0
    vcp_pivot_point: float = 0.0
    vcp_pattern_width: float = 0.0
    vcp_volume_drying: bool = False
    vcp_quality: str = "none"
    rs_rating: int = 0
    rs_percentile: float = 0.0
    distance_from_52w_high: float = 0.0
    distance_from_52w_low: float = 0.0
    trend_template_pass: bool = False
    ep_detected: bool = False
    ep_gap_up_pct: float = 0.0
    ep_volume_spike: float = 0.0
    ep_catalyst_score: float = 0.0
    ep_quality: str = "none"

def compute_indicators(df, code="", ktype="1d"):
    if df is None or df.empty or len(df) < 1:
        return Indicators(code=code, ktype=ktype)
    ind = Indicators(code=code, ktype=ktype, df=df)
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    volume = df["volume"].values.astype(float)
    # 过滤负价格脏数据（akshare美股数据有时含拆股调整导致的负值）
    valid = (close > 0) & (high > 0) & (low > 0) & (volume >= 0)
    if not valid.all():
        close = close[valid]; high = high[valid]; low = low[valid]; volume = volume[valid]
        n = len(close)
        if n < 60:
            return Indicators(code=code, ktype=ktype)
    n = len(close)
    last = n - 1
    ind.last_close = float(close[last])
    ind.last_time = str(df["time"].iloc[last])
    ind.prev_close = float(close[last-1]) if last > 0 else ind.last_close
    ind.day_change_pct = (close[last] - ind.prev_close) / ind.prev_close * 100 if ind.prev_close > 0 else 0.0
    for period, attr in [(5,"ma5"),(10,"ma10"),(20,"ma20"),(60,"ma60"),(120,"ma120"),(200,"ma200")]:
        val = float(np.mean(close[-period:])) if n >= period else (float(np.mean(close)) if n > 0 else 0.0)
        setattr(ind, attr, val)
    for ma_attr, pct_attr in [("ma20","price_vs_ma20"),("ma60","price_vs_ma60"),("ma200","price_vs_ma200")]:
        ma_val = getattr(ind, ma_attr)
        setattr(ind, pct_attr, (ind.last_close - ma_val) / ma_val * 100 if ma_val > 0 else 0.0)
    if n >= 26:
        ema12 = _ema(close, 12); ema26 = _ema(close, 26)
        dif_series = ema12 - ema26; dea_series = _ema(dif_series, 9)
        ind.macd_dif = float(dif_series[-1]); ind.macd_dea = float(dea_series[-1])
        ind.macd_hist = float(2 * (dif_series[-1] - dea_series[-1]))
        for i in range(max(0,n-10), n-1):
            if dif_series[i] <= dea_series[i] and dif_series[i+1] > dea_series[i+1]:
                ind.macd_dif_dea_cross = "golden"; break
            if dif_series[i] >= dea_series[i] and dif_series[i+1] < dea_series[i+1]:
                ind.macd_dif_dea_cross = "death"; break
    else:
        ind.macd_dif = ind.macd_dea = ind.macd_hist = 0.0
        ind.macd_dif_dea_cross = "none"
    deltas = np.diff(close)
    for period, attr in [(6,"rsi_6"),(12,"rsi_12"),(14,"rsi_14"),(24,"rsi_24")]:
        if len(deltas) < period:
            setattr(ind, attr, 50.0); continue
        gains = np.where(deltas[-period:] > 0, deltas[-period:], 0.0)
        losses = np.where(deltas[-period:] < 0, -deltas[-period:], 0.0)
        avg_gain = float(np.mean(gains)); avg_loss = float(np.mean(losses))
        if avg_loss == 0:
            rsi = 50.0 if bool(np.all(deltas[-period:] == 0)) else 100.0
        else:
            rsi = 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))
        setattr(ind, attr, rsi)
    if n >= 9:
        k_vals, d_vals = _kdj_full_series(low, high, close, 9, 3, 3)
        ind.kdj_k = float(k_vals[-1]); ind.kdj_d = float(d_vals[-1])
        ind.kdj_j = float(3.0 * k_vals[-1] - 2.0 * d_vals[-1])
    if n >= 20:
        mid = float(np.mean(close[-20:])); std = float(np.std(close[-20:], ddof=1))
        ind.boll_mid = mid; ind.boll_upper = mid + 2*std; ind.boll_lower = mid - 2*std
        ind.boll_width = (ind.boll_upper - ind.boll_lower) / mid * 100 if mid != 0 else 0.0
    else:
        ind.boll_mid = ind.last_close; ind.boll_upper = ind.last_close*1.05
        ind.boll_lower = ind.last_close*0.95; ind.boll_width = 10.0
    if n >= 15:
        tr = np.zeros(n); tr[0] = high[0]-low[0]
        for i in range(1,n):
            tr[i] = max(high[i]-low[i], abs(high[i]-close[i-1]), abs(low[i]-close[i-1]))
        ind.atr_14 = float(_ema(tr,14)[-1]) if len(_ema(tr,14)) > 0 else 0.0
    else:
        ind.atr_14 = float(np.mean(high-low)) if n > 0 else 0.0
    if n >= 2:
        obv_vals = [0.0]
        for i in range(1,n):
            if close[i] > close[i-1]: obv_vals.append(obv_vals[-1]+volume[i])
            elif close[i] < close[i-1]: obv_vals.append(obv_vals[-1]-volume[i])
            else: obv_vals.append(obv_vals[-1])
        ind.obv = obv_vals[-1]
        if len(obv_vals) >= 5:
            if obv_vals[-1] > obv_vals[-5]*1.05: ind.obv_trend = "up"
            elif obv_vals[-1] < obv_vals[-5]*0.95: ind.obv_trend = "down"
            else: ind.obv_trend = "flat"
    if n >= 20:
        vol_sum = float(np.sum(volume[-20:])); pv_sum = float(np.sum(close[-20:]*volume[-20:]))
        ind.vwma_20 = pv_sum/vol_sum if vol_sum != 0 else ind.last_close
    else:
        ind.vwma_20 = ind.last_close
    if n >= 5:
        avg_vol_5 = float(np.mean(volume[-5:]))
        ind.vol_ratio = volume[last]/avg_vol_5 if avg_vol_5 != 0 else 1.0
    else:
        ind.vol_ratio = 1.0
    if n >= 11:
        ma5_vals = []; ma10_vals = []
        for i in range(n):
            ma5_vals.append(float(np.mean(close[max(0,i-4):i+1])))
            ma10_vals.append(float(np.mean(close[max(0,i-9):i+1])))
        for i in range(max(0,n-10), n-1):
            if ma5_vals[i] <= ma10_vals[i] and ma5_vals[i+1] > ma10_vals[i+1]:
                ind.ma5_ma10_cross = "golden"; break
            if ma5_vals[i] >= ma10_vals[i] and ma5_vals[i+1] < ma10_vals[i+1]:
                ind.ma5_ma10_cross = "death"; break
    if n >= 2:
        gap = (close[last] - high[last-1]) / high[last-1] * 100 if high[last-1] > 0 else 0
        ind.gap_pct = gap
        ind.gap_type = "gap_up" if gap > 1.0 else ("gap_down" if gap < -1.0 else "none")
    if n >= 252:
        high_52w = float(np.max(high[-252:])); low_52w = float(np.min(low[-252:]))
        ind.distance_from_52w_high = (high_52w - ind.last_close) / high_52w * 100 if high_52w > 0 else 0
        ind.distance_from_52w_low = (ind.last_close - low_52w) / low_52w * 100 if low_52w > 0 else 0
    elif n > 0:
        high_52w = float(np.max(high)); low_52w = float(np.min(low))
        ind.distance_from_52w_high = (high_52w - ind.last_close) / high_52w * 100 if high_52w > 0 else 0
        ind.distance_from_52w_low = (ind.last_close - low_52w) / low_52w * 100 if low_52w > 0 else 0
    # 相对强度 (RS) 评分
    _52w = min(252, n)
    if n >= 20:
        _recent_high = float(np.max(high[-_52w:]))
        _recent_low = float(np.min(low[-_52w:]))
        if _recent_high > 0:
            ind.distance_from_52w_high = round((_recent_high - ind.last_close) / _recent_high * 100, 2)
            ind.distance_from_52w_low = round((ind.last_close - _recent_low) / _recent_low * 100, 2) if _recent_low > 0 else 0
            ind.rs_percentile = round((ind.last_close - _recent_low) / (_recent_high - _recent_low) * 100, 1) if _recent_high > _recent_low else 50.0
            ind.rs_rating = int(ind.rs_percentile)
    # Trend Template 验证 (Minervini 8点模板)
    _passed = True
    if ind.ma200 > 0:
        if ind.last_close <= ind.ma20: _passed = False
        if ind.last_close <= ind.ma60: _passed = False
        if ind.last_close <= ind.ma200: _passed = False
        if ind.ma60 <= ind.ma200: _passed = False
        if n >= 200:
            _ma200_prev = float(np.mean(close[-201:-1]))
            if ind.ma200 <= _ma200_prev: _passed = False
    ind.trend_template_pass = _passed
    return ind

def signal_summary(ind):
    signals = []
    if ind.ma5_ma10_cross == "golden": signals.append("MA5/10金叉")
    elif ind.ma5_ma10_cross == "death": signals.append("MA5/10死叉")
    if ind.macd_dif_dea_cross == "golden": signals.append("MACD金叉")
    elif ind.macd_dif_dea_cross == "death": signals.append("MACD死叉")
    if ind.price_vs_ma20 > 5: signals.append(f"价格高于MA20 {ind.price_vs_ma20:.1f}%")
    elif ind.price_vs_ma20 < -5: signals.append(f"价格低于MA20 {abs(ind.price_vs_ma20):.1f}%")
    if ind.price_vs_ma60 > 10: signals.append(f"价格高于MA60 {ind.price_vs_ma60:.1f}%")
    elif ind.price_vs_ma60 < -10: signals.append(f"价格低于MA60 {abs(ind.price_vs_ma60):.1f}%")
    if ind.rsi_14 > 70: signals.append(f"RSI超买({ind.rsi_14:.1f})")
    elif ind.rsi_14 < 30: signals.append(f"RSI超卖({ind.rsi_14:.1f})")
    if ind.kdj_k < 20 and ind.kdj_d < 20: signals.append("KDJ超卖")
    elif ind.kdj_k > 80 and ind.kdj_d > 80: signals.append("KDJ超买")
    if ind.last_close > ind.boll_upper: signals.append("价格突破布林上轨")
    elif ind.last_close < ind.boll_lower: signals.append("价格跌破布林下轨")
    if ind.obv_trend == "up": signals.append("OBV上升")
    elif ind.obv_trend == "down": signals.append("OBV下降")
    if ind.gap_type == "gap_up": signals.append(f"跳空高开 {ind.gap_pct:.1f}%")
    elif ind.gap_type == "gap_down": signals.append(f"跳空低开 {ind.gap_pct:.1f}%")
    return {"code":ind.code,"price":ind.last_close,"change_pct":ind.day_change_pct,"signals":signals,"signal_count":len(signals)}
