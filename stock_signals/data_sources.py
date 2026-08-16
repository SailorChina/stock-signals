# -*- coding: utf-8 -*-
"""免费股票数据源模块"""
from __future__ import annotations
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("stock-signals")

# 数据源可用性
AKSHARE_AVAILABLE = False
YFINANCE_AVAILABLE = False
TUSHARE_AVAILABLE = False

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    pass

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    pass

try:
    import tushare as ts
    TUSHARE_AVAILABLE = True
except ImportError:
    pass


def get_stock_list(market: str) -> List[str]:
    """获取股票列表（自动降级）"""
    codes = []
    
    # 1. AkShare优先
    if AKSHARE_AVAILABLE:
        try:
            codes = _get_from_akshare(market)
            if codes:
                logger.info(f"  AkShare{market}: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  AkShare{market}失败: {e}")
    
    # 2. yfinance备用
    if YFINANCE_AVAILABLE and market in ["US", "HK"]:
        try:
            codes = _get_from_yfinance(market)
            if codes:
                logger.info(f"  yfinance{market}: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  yfinance{market}失败: {e}")
    
    # 3. Tushare备用
    if TUSHARE_AVAILABLE and market == "A":
        try:
            codes = _get_from_tushare(market)
            if codes:
                logger.info(f"  Tushare{market}: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  Tushare{market}失败: {e}")
    
    return []


def _get_from_akshare(market: str) -> List[str]:
    """AkShare获取股票列表"""
    import akshare as ak
    codes = []
    
    if market == "A":
        try:
            # 沪深300
            df = ak.index_stock_cons_csindex(symbol="000300")
            sh = [f"SH.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("6")]
            sz = [f"SZ.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("0") or str(c).startswith("3")]
            codes.extend(sh + sz)
            # 中证500
            df = ak.index_stock_cons_csindex(symbol="000905")
            sh = [f"SH.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("6")]
            sz = [f"SZ.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("0") or str(c).startswith("3")]
            codes.extend(sh + sz)
        except Exception as e:
            logger.warning(f"  AkShare A股失败: {e}")
    
    elif market == "HK":
        try:
            df = ak.hk_stock_spot_em()
            if df is not None and not df.empty:
                codes.extend([f"HK.{str(c).zfill(5)}" for c in df["代码"].tolist()[:100]])
        except Exception as e:
            logger.warning(f"  AkShare港股失败: {e}")
    
    return list(dict.fromkeys(codes))


def _get_from_yfinance(market: str) -> List[str]:
    """yfinance获取股票列表"""
    codes = []
    if market == "US":
        sp500 = ["AAPL", "MSFT", "GOOG", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
                 "BRK.B", "UNH", "JNJ", "V", "XOM", "JPM", "LLY", "WMT", "PG",
                 "MA", "AVGO", "HD", "CVX", "MRK", "COST", "ABBV", "PEP", "TMO",
                 "ABT", "ACN", "MCD", "NFLX", "AMD", "DIS", "DHR", "VZ", "CRM"]
        codes = [f"US.{t}" for t in sp500]
    return codes


def _get_from_tushare(market: str) -> List[str]:
    """Tushare获取股票列表"""
    import tushare as ts
    codes = []
    try:
        pro = ts.pro_api()
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                code = str(row['ts_code'])
                if code.startswith('0.') or code.startswith('3.'):
                    codes.append(f"SZ.{code.split('.')[0]}")
                elif code.startswith('6.'):
                    codes.append(f"SH.{code.split('.')[0]}")
    except Exception as e:
        logger.warning(f"  Tushare失败: {e}")
    return codes


def get_available_sources() -> Dict[str, bool]:
    """返回可用的数据源"""
    return {
        "akshare": AKSHARE_AVAILABLE,
        "yfinance": YFINANCE_AVAILABLE,
        "tushare": TUSHARE_AVAILABLE,
    }
