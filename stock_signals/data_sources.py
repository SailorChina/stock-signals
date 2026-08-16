# -*- coding: utf-8 -*-
"""综合股票数据源模块"""
from __future__ import annotations
import logging
import json
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger("stock-signals")

# 数据源状态
SINA_AVAILABLE = False
EDF_AVAILABLE = False
AKSHARE_AVAILABLE = False
YFINANCE_AVAILABLE = False

try:
    import requests
    SINA_AVAILABLE = True
    EDF_AVAILABLE = True
except ImportError:
    pass

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


def get_stock_list(market: str) -> List[str]:
    """获取股票列表（自动降级）"""
    # 1. 东方财富
    if EDF_AVAILABLE:
        try:
            codes = _get_from_eastmoney(market)
            if codes:
                logger.info(f"  东方财富{market}: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  东方财富{market}失败: {e}")
    
    # 2. 新浪
    if SINA_AVAILABLE:
        try:
            codes = _get_from_sina(market)
            if codes:
                logger.info(f"  新浪{market}: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  新浪{market}失败: {e}")
    
    # 3. AkShare
    if AKSHARE_AVAILABLE:
        try:
            codes = _get_from_akshare(market)
            if codes:
                logger.info(f"  AkShare{market}: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  AkShare{market}失败: {e}")
    
    # 4. yfinance
    if YFINANCE_AVAILABLE and market in ["US", "HK"]:
        try:
            codes = _get_from_yfinance(market)
            if codes:
                logger.info(f"  yfinance{market}: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  yfinance{market}失败: {e}")
    
    return []


def _get_from_eastmoney(market: str) -> List[str]:
    """东方财富获取股票列表"""
    import requests
    codes = []
    try:
        if market == "A":
            for secid in ["1.a", "0.a"]:
                for page in range(1, 15):
                    url = f"https://push2.eastmoney.com/api/qt/clist/get?pn={page}&pz=500&po=1&np=1&fltt=2&invt=2&fid=f3&fs={secid}&fields=f12,f14"
                    r = requests.get(url, timeout=10)
                    data = r.json()
                    if not data.get("data") or not data["data"].get("diff"):
                        break
                    for item in data["data"]["diff"]:
                        code = item.get("f12", "")
                        if code:
                            prefix = "SH" if secid.startswith("1") else "SZ"
                            codes.append(f"{prefix}.{code}")
                    if len(data["data"]["diff"]) < 500:
                        break
        elif market == "HK":
            for page in range(1, 10):
                url = f"https://push2.eastmoney.com/api/qt/clist/get?pn={page}&pz=200&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:128+t:3,m:128+t:4,m:128+t:5,m:128+t:6&fields=f12,f14"
                r = requests.get(url, timeout=10)
                data = r.json()
                if not data.get("data") or not data["data"].get("diff"):
                    break
                for item in data["data"]["diff"]:
                    code = item.get("f12", "")
                    if code:
                        codes.append(f"HK.{code.zfill(5)}")
                if len(data["data"]["diff"]) < 200:
                    break
    except Exception as e:
        logger.warning(f"  东财{market}失败: {e}")
    return list(dict.fromkeys(codes))


def _get_from_sina(market: str) -> List[str]:
    """新浪财经获取股票列表"""
    import requests
    codes = []
    try:
        if market == "A":
            for page in range(1, 20):
                url = f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num=100&sort=symbol&asc=1&node=hs_a"
                r = requests.get(url, timeout=10)
                data = json.loads(r.text)
                if not data:
                    break
                for item in data:
                    code = item.get("symbol", "")
                    if code:
                        # 判断沪市/深市
                        if code.startswith("6"):
                            codes.append(f"SH.{code}")
                        elif code.startswith("0") or code.startswith("3"):
                            codes.append(f"SZ.{code}")
                if len(data) < 100:
                    break
    except Exception as e:
        logger.warning(f"  新浪{market}失败: {e}")
    return list(dict.fromkeys(codes))


def _get_from_akshare(market: str) -> List[str]:
    """AkShare获取股票列表"""
    import akshare as ak
    codes = []
    try:
        if market == "A":
            # 沪深300
            df = ak.index_stock_cons_csindex(symbol="000300")
            for c in df["成分券代码"].tolist():
                c = str(c)
                if c.startswith("6"):
                    codes.append(f"SH.{c}")
                elif c.startswith("0") or c.startswith("3"):
                    codes.append(f"SZ.{c}")
            # 中证500
            df = ak.index_stock_cons_csindex(symbol="000905")
            for c in df["成分券代码"].tolist():
                c = str(c)
                if c.startswith("6"):
                    codes.append(f"SH.{c}")
                elif c.startswith("0") or c.startswith("3"):
                    codes.append(f"SZ.{c}")
    except Exception as e:
        logger.warning(f"  AkShare{market}失败: {e}")
    return list(dict.fromkeys(codes))


def _get_from_yfinance(market: str) -> List[str]:
    """yfinance获取股票列表"""
    codes = []
    if market == "US":
        sp500 = ["AAPL", "MSFT", "GOOG", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
                 "BRK.B", "UNH", "JNJ", "V", "XOM", "JPM", "LLY", "WMT", "PG",
                 "MA", "AVGO", "HD", "CVX", "MRK", "COST", "ABBV", "PEP", "TMO"]
        codes = [f"US.{t}" for t in sp500]
    elif market == "HK":
        hk_stocks = ["0700", "9988", "3690", "9618", "9888", "2382", "9999", "9660"]
        codes = [f"HK.{c}" for c in hk_stocks]
    return codes


def get_available_sources() -> Dict[str, bool]:
    """返回可用的数据源"""
    return {
        "eastmoney": EDF_AVAILABLE,
        "sina": SINA_AVAILABLE,
        "akshare": AKSHARE_AVAILABLE,
        "yfinance": YFINANCE_AVAILABLE,
    }
