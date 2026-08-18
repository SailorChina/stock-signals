# -*- coding: utf-8 -*-
"""Akshare 数据获取层 — 免费、无速率限制的K线数据源
优先级: akshare(Sina源) > Sina直连 > baostock(备选)
"""
from __future__ import annotations

import sys
import time
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger("stock-signals")

# ─────────────────────────────────────────────────────────────────────
# 代码格式转换
# ─────────────────────────────────────────────────────────────────────

def _code_to_akshare(code: str) -> tuple[str, str]:
    """将 US.SH.SZ.HK 代码转为 akshare 格式，返回 (ak_code, market)"""
    if code.startswith("US."):
        return code[3:], "us"
    elif code.startswith("SH."):
        return "sh" + code[3:], "a"
    elif code.startswith("SZ."):
        return "sz" + code[3:], "a"
    elif code.startswith("HK."):
        return code[3:], "hk"
    return code, "unknown"


# ─────────────────────────────────────────────────────────────────────
# 单只股票数据获取 — akshare Sina源 (主)
# ─────────────────────────────────────────────────────────────────────

def _fetch_us_daily(code: str, adjust: str = "qfq") -> Optional[pd.DataFrame]:
    """获取美股日线数据 (akshare stock_us_daily, Sina源)"""
    try:
        import akshare as ak
        df = ak.stock_us_daily(symbol=code, adjust=adjust)
        if df is not None and not df.empty:
            df = df.rename(columns={
                "date": "time_key", "open": "open", "high": "high",
                "low": "low", "close": "close", "volume": "volume",
            })
            df["time_key"] = pd.to_datetime(df["time_key"])
            return df.sort_values("time_key").reset_index(drop=True)
    except Exception as e:
        logger.warning(f"akshare US数据获取失败 {code}: {e}")
    return None


def _fetch_a_daily(code: str, adjust: str = "qfq") -> Optional[pd.DataFrame]:
    """获取A股日线数据 (akshare stock_zh_a_daily, Sina源)"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_daily(symbol=code, adjust=adjust)
        if df is not None and not df.empty:
            df = df.rename(columns={
                "date": "time_key", "open": "open", "high": "high",
                "low": "low", "close": "close", "volume": "volume",
            })
            df["time_key"] = pd.to_datetime(df["time_key"])
            return df.sort_values("time_key").reset_index(drop=True)
    except Exception as e:
        logger.warning(f"akshare A股数据获取失败 {code}: {e}")
    return None


def _fetch_hk_daily(code: str, adjust: str = "qfq") -> Optional[pd.DataFrame]:
    """获取港股日线数据 (akshare stock_hk_daily, Sina源)"""
    try:
        import akshare as ak
        df = ak.stock_hk_daily(symbol=code, adjust=adjust)
        if df is not None and not df.empty:
            df = df.rename(columns={
                "date": "time_key", "open": "open", "high": "high",
                "low": "low", "close": "close", "volume": "volume",
            })
            df["time_key"] = pd.to_datetime(df["time_key"])
            return df.sort_values("time_key").reset_index(drop=True)
    except Exception as e:
        logger.warning(f"akshare HK数据获取失败 {code}: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────
# Sina 直连备选 (当akshare失败时)
# ─────────────────────────────────────────────────────────────────────

def _fetch_sina_direct(code: str, ktype: str = "1d") -> Optional[pd.DataFrame]:
    """Sina直连K线API (备选)"""
    try:
        import urllib.request
        # 确定symbol格式
        if code.startswith("sh") or code.startswith("sz"):
            sina_code = code  # sh600519, sz000001
        elif code.startswith("us") or code.startswith("US"):
            # Sina不直接提供美股K线，返回None
            return None
        else:
            return None
        
        scale = "240" if ktype == "1d" else "10080"
        url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sina_code}&scale={scale}&ma=no&datalen=500"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = __import__("json").loads(resp.read().decode())
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        df["time_key"] = pd.to_datetime(df["day"])
        df = df.rename(columns={"open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"})
        df = df[["time_key", "open", "high", "low", "close", "volume"]]
        df = df.sort_values("time_key").reset_index(drop=True)
        return df
    except Exception as e:
        logger.warning(f"Sina直连失败 {code}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────
# 统一入口
# ─────────────────────────────────────────────────────────────────────

def fetch_kline(code: str, ktype: str = "1d", num: int = 300) -> Optional[pd.DataFrame]:
    """
    获取K线数据 — 优先使用 akshare（免费无限制），Sina直连作备选
    ktype: "1d"=日线, "1w"=周线, "1M"=月线
    周线/月线从日线 resample 派生
    """
    ak_code, market = _code_to_akshare(code)
    if market == "unknown":
        return None

    # 1. 优先使用 akshare Sina源
    if market == "us":
        df = _fetch_us_daily(ak_code)
    elif market == "a":
        df = _fetch_a_daily(ak_code)
    elif market == "hk":
        df = _fetch_hk_daily(ak_code)
    else:
        return None

    # 2. akshare失败时尝试Sina直连
    if df is None or df.empty or len(df) < 10:
        if market in ("a", "us"):
            df = _fetch_sina_direct(ak_code, ktype)

    if df is None or df.empty or len(df) < 10:
        return None

    # 3. 周线/月线派生
    if ktype in ("1w", "1M"):
        df = df.copy()
        df["time_key"] = pd.to_datetime(df["time_key"])
        df = df.set_index("time_key")
        freq = "W" if ktype == "1w" else "ME"
        df_resampled = df.resample(freq).agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum",
        }).dropna().reset_index()
        df = df_resampled

    # 4. 限制返回条数
    if len(df) > num:
        df = df.tail(num).reset_index(drop=True)

    return df



def fetch_kline_akshare(code: str, ktype: str = "1d", num: int = 300) -> Optional[pd.DataFrame]:
    """Alias for fetch_kline"""
    return fetch_kline(code, ktype, num)
