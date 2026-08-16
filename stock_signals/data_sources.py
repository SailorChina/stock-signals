# -*- coding: utf-8 -*-
"""免费股票数据源模块

支持多种免费数据源，自动降级：
1. AkShare (A股/港股/美股，完全免费)
2. yfinance (美股为主，完全免费)
3. Tushare (A股为主，免费额度)
4. pandas_datareader (美股，完全免费)
"""
from __future__ import annotations
import logging
import time
from typing import List, Dict, Optional, Union
import pandas as pd

logger = logging.getLogger("stock-signals")

# ========== 数据源配置 ==========
DATA_SOURCES = {
    "akshare": {"name": "AkShare", "priority": 1, "markets": ["A", "HK", "US"]},
    "yfinance": {"name": "yfinance", "priority": 2, "markets": ["US", "HK"]},
    "tushare": {"name": "Tushare", "priority": 3, "markets": ["A"]},
    "pdr": {"name": "pandas_datareader", "priority": 4, "markets": ["US"]},
}

# ========== 数据获取函数 ==========

def get_stock_list_source(source: str, market: str) -> List[str]:
    """从指定数据源获取股票列表"""
    try:
        if source == "akshare":
            return _get_from_akshare(market)
        elif source == "yfinance":
            return _get_from_yfinance(market)
        elif source == "tushare":
            return _get_from_tushare(market)
        elif source == "pdr":
            return _get_from_pdr(market)
    except Exception as e:
        logger.warning(f"  {source}获取{market}股票列表失败: {e}")
    return []

def _get_from_akshare(market: str) -> List[str]:
    """AkShare数据源"""
    import akshare as ak
    codes = []
    if market == "A":
        try:
            # 沪深300
            df = ak.index_stock_cons_csindex(symbol="000300")
            codes.extend([f"SH.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("6")])
            codes.extend([f"SZ.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("0") or str(c).startswith("3")])
            # 中证500
            df = ak.index_stock_cons_csindex(symbol="000905")
            codes.extend([f"SH.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("6")])
            codes.extend([f"SZ.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("0") or str(c).startswith("3")])
        except Exception as e:
            logger.warning(f"  AkShare A股成分股失败: {e}")
    elif market == "HK":
        try:
            # 恒生指数成分股
            df = ak.hk_stock_spot_em()
            if df is not None and not df.empty:
                codes.extend([f"HK.{str(c).zfill(5)}" for c in df["代码"].tolist()[:100]])
        except Exception as e:
            logger.warning(f"  AkShare港股失败: {e}")
    return list(dict.fromkeys(codes))

def _get_from_yfinance(market: str) -> List[str]:
    """yfinance数据源"""
    import yfinance as yf
    codes = []
    if market == "US":
        try:
            # 标普500成分股（手动维护列表，因为yfinance不直接提供）
            sp500 = [
                "AAPL", "MSFT", "GOOG", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
                "BRK.B", "UNH", "JNJ", "V", "XOM", "JPM", "LLY", "WMT", "PG",
                "MA", "AVGO", "HD", "CVX", "MRK", "COST", "ABBV", "PEP", "TMO",
                "MRNA", "ABT", "ACN", "MCD", "NFLX", "AMD", "DIS", "DHR", "VZ",
                "CRM", "NEE", "RTX", "BMY", "LIN", "UNP", "T", "KO", "NKE",
            ]
            codes = [f"US.{t}" for t in sp500]
        except Exception as e:
            logger.warning(f"  yfinance美股失败: {e}")
    return codes

def _get_from_tushare(market: str) -> List[str]:
    """Tushare数据源（需要token）"""
    try:
        import tushare as ts
        # 注意: Tushare需要注册获取token，免费额度有限
        # 这里作为备用方案
        logger.info("  Tushare需要配置token，跳过")
        return []
    except ImportError:
        logger.warning("  Tushare未安装")
        return []
    except Exception as e:
        logger.warning(f"  Tushare失败: {e}")
        return []

def _get_from_pdr(market: str) -> List[str]:
    """pandas_datareader数据源"""
    try:
        import pandas_datareader as pdr
        # pdr主要用于获取历史数据，不直接提供股票列表
        logger.info("  pandas_datareader用于历史数据，不获取股票列表")
        return []
    except ImportError:
        logger.warning("  pandas_datareader未安装")
        return []
    except Exception as e:
        logger.warning(f"  pandas_datareader失败: {e}")
        return []

def get_stock_list(market: str, sources: List[str] = None) -> List[str]:
    """获取股票列表（自动降级）"""
    if sources is None:
        sources = list(DATA_SOURCES.keys())
    
    for source in sources:
        if source not in DATA_SOURCES:
            continue
        config = DATA_SOURCES[source]
        if market not in config["markets"]:
            continue
        
        logger.info(f"  尝试 {config['name']} 获取{market}股票列表...")
        codes = get_stock_list_source(source, market)
        if codes:
            logger.info(f"  {config['name']}成功: {len(codes)} 只")
            return codes
    
    logger.warning(f"  所有数据源获取{market}股票列表失败")
    return []

def get_stock_info(source: str, code: str) -> Optional[Dict]:
    """获取股票基本信息"""
    try:
        if source == "akshare":
            return _get_info_akshare(code)
        elif source == "yfinance":
            return _get_info_yfinance(code)
    except Exception as e:
        logger.warning(f"  {source}获取股票信息失败: {e}")
    return None

def _get_info_akshare(code: str) -> Optional[Dict]:
    """AkShare获取股票信息"""
    try:
        import akshare as ak
        # 简化实现，实际需要根据代码格式解析
        return {"name": code, "sector": "未知"}
    except Exception as e:
        return None

def _get_info_yfinance(code: str) -> Optional[Dict]:
    """yfinance获取股票信息"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(code.replace("US.", ""))
        info = ticker.info
        return {
            "name": info.get("shortName", code),
            "sector": info.get("sector", "未知"),
            "desc": info.get("businessSummary", "")[:100] if info.get("businessSummary") else "",
        }
    except Exception as e:
        return None
