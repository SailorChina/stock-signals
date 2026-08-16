# -*- coding: utf-8 -*-
"""免费股票数据源模块

支持多种免费数据源，自动降级：
1. AkShare (A股/港股/美股，完全免费)
2. yfinance (美股为主，完全免费)
3. Tushare (A股为主，免费额度)
"""
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
        # 港股API不稳定，使用静态列表
        logger.info("  港股使用静态池")
        codes = ["HK.00700", "HK.09988", "HK.03690", "HK.09618", "HK.09888", 
                 "HK.02382", "HK.09999", "HK.09660", "HK.02015", "HK.02359"]
    
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
    elif market == "HK":
        hk_stocks = ["0700", "9988", "3690", "9618", "9888", "2382", "9999", "9660"]
        codes = [f"HK.{c}" for c in hk_stocks]
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
