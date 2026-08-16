# -*- coding: utf-8 -*-
"""综合股票数据源模块 - 集成国内主流免费数据源"""
from __future__ import annotations
import logging
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("stock-signals")

# ========== 数据源状态 ==========
SINA_AVAILABLE = False
EDF_AVAILABLE = False
TX_AVAILABLE = False
AKSHARE_AVAILABLE = False
YFINANCE_AVAILABLE = False

try:
    import requests
    SINA_AVAILABLE = True
    EDF_AVAILABLE = True
    TX_AVAILABLE = True
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


@dataclass
class StockInfo:
    """股票信息"""
    code: str
    name: str
    market: str  # A, US, HK
    sector: str = ""
    desc: str = ""


# ========== 新浪数据源 ==========
def _get_from_sina(market: str) -> List[Tuple[str, str]]:
    """从新浪财经获取股票列表"""
    results = []
    try:
        if market == "A":
            # 获取全部A股
            for page in range(1, 20):
                url = f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={page}&num=100&sort=symbol&asc=1&node=hs_a&symbol=&_s_r_a=page"
                r = requests.get(url, timeout=10)
                data = json.loads(r.text)
                if not data:
                    break
                for item in data:
                    code = item.get("symbol", "")
                    name = item.get("name", "")
                    if code and name:
                        results.append((code, name))
                if len(data) < 100:
                    break
            logger.info(f"  新浪A股: {len(results)} 只")
        elif market == "US":
            # 美股主要股票
            us_stocks = [
                ("AAPL", "苹果公司"), ("MSFT", "微软"), ("GOOG", "谷歌"),
                ("AMZN", "亚马逊"), ("META", "Meta"), ("NVDA", "英伟达"),
                ("TSLA", "特斯拉"), ("BRK.B", "伯克希尔"), ("UNH", "联合健康"),
                ("JNJ", "强生"), ("V", "Visa"), ("XOM", "埃克森美孚"),
            ]
            results = us_stocks
            logger.info(f"  新浪美股: {len(results)} 只")
    except Exception as e:
        logger.warning(f"  新浪{market}失败: {e}")
    return results


# ========== 东方财富数据源 ==========
def _get_from_eastmoney(market: str) -> List[Tuple[str, str]]:
    """从东方财富获取股票列表"""
    results = []
    try:
        import requests
        if market == "A":
            # 沪深A股
            for secid in ["1.a", "0.a"]:  # 1=沪市, 0=深市
                for page in range(1, 20):
                    url = f"https://push2.eastmoney.com/api/qt/clist/get?pn={page}&pz=500&po=1&np=1&fltt=2&invt=2&fid=f3&fs={secid}&fields=f12,f14"
                    r = requests.get(url, timeout=10)
                    data = r.json()
                    if not data.get("data") or not data["data"].get("diff"):
                        break
                    for item in data["data"]["diff"]:
                        code = item.get("f12", "")
                        name = item.get("f14", "")
                        if code and name:
                            prefix = "SH" if secid.startswith("1") else "SZ"
                            results.append((f"{prefix}.{code}", name))
                    if len(data["data"]["diff"]) < 500:
                        break
            logger.info(f"  东财A股: {len(results)} 只")
        elif market == "HK":
            # 港股
            for page in range(1, 10):
                url = f"https://push2.eastmoney.com/api/qt/clist/get?pn={page}&pz=200&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:128+t:3,m:128+t:4,m:128+t:5,m:128+t:6&fields=f12,f14"
                r = requests.get(url, timeout=10)
                data = r.json()
                if not data.get("data") or not data["data"].get("diff"):
                    break
                for item in data["data"]["diff"]:
                    code = item.get("f12", "")
                    name = item.get("f14", "")
                    if code and name:
                        results.append((f"HK.{code.zfill(5)}", name))
                if len(data["data"]["diff"]) < 200:
                    break
            logger.info(f"  东财港股: {len(results)} 只")
    except Exception as e:
        logger.warning(f"  东财{market}失败: {e}")
    return results


# ========== 腾讯数据源 ==========
def _get_from_tencent(market: str) -> List[Tuple[str, str]]:
    """从腾讯财经获取股票列表"""
    results = []
    try:
        import requests
        if market == "A":
            # 腾讯A股实时行情
            # 先获取沪市A股
            url = "https://qt.gtimg.cn/q=" + ",".join([f"sh60{i:06d}" for i in range(000001, 600000, 1000)])
            r = requests.get(url, timeout=10)
            lines = r.text.strip().split(";")
            for line in lines:
                if "~" in line:
                    parts = line.split("~")
                    if len(parts) > 1:
                        code = parts[1]
                        name = parts[2]
                        if code and name:
                            results.append((f"SH.{code}", name))
            logger.info(f"  腾讯A股: {len(results)} 只")
    except Exception as e:
        logger.warning(f"  腾讯{market}失败: {e}")
    return results


# ========== 统一接口 ==========
def get_stock_list(market: str) -> List[str]:
    """获取股票列表（自动降级）"""
    codes = []
    
    # 1. 东方财富优先（数据最全）
    if EDF_AVAILABLE:
        try:
            pairs = _get_from_eastmoney(market)
            if pairs:
                codes = [p[0] for p in pairs]
                logger.info(f"  东方财富{market}: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  东方财富{market}失败: {e}")
    
    # 2. 新浪财经备用
    if SINA_AVAILABLE:
        try:
            pairs = _get_from_sina(market)
            if pairs:
                codes = [p[0] for p in pairs]
                logger.info(f"  新浪财经{market}: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  新浪{market}失败: {e}")
    
    # 3. AkShare备用
    if AKSHARE_AVAILABLE:
        try:
            import akshare as ak
            if market == "A":
                df = ak.index_stock_cons_csindex(symbol="000300")
                codes = []
                for c in df["成分券代码"].tolist():
                    c = str(c)
                    if c.startswith("6"):
                        codes.append(f"SH.{c}")
                    elif c.startswith("0") or c.startswith("3"):
                        codes.append(f"SZ.{c}")
                logger.info(f"  AkShare A股: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  AkShare{market}失败: {e}")
    
    # 4. yfinance备用（美股/港股）
    if YFINANCE_AVAILABLE and market in ["US", "HK"]:
        try:
            import yfinance as yf
            if market == "US":
                sp500 = ["AAPL", "MSFT", "GOOG", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]
                codes = [f"US.{t}" for t in sp500]
                logger.info(f"  yfinance美股: {len(codes)} 只")
                return codes
        except Exception as e:
            logger.warning(f"  yfinance{market}失败: {e}")
    
    logger.warning(f"  所有数据源获取{market}股票列表失败")
    return []


def get_stock_info(code: str) -> Optional[Dict]:
    """获取股票信息"""
    # 尝试东方财富
    if EDF_AVAILABLE:
        try:
            import requests
            # 根据代码判断市场
            if code.startswith("SH") or code.startswith("SZ"):
                secid = f"1.{code[2:]}" if code.startswith("SH") else f"0.{code[2:]}"
                url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60"
                r = requests.get(url, timeout=10)
                data = r.json()
                if data.get("data"):
                    d = data["data"]
                    return {
                        "name": d.get("f57", ""),
                        "sector": d.get("f58", ""),
                        "price": d.get("f43", 0),
                    }
        except Exception as e:
            logger.debug(f"  东财获取{code}信息失败: {e}")
    
    # 尝试yfinance
    if YFINANCE_AVAILABLE and code.startswith("US."):
        try:
            import yfinance as yf
            ticker = yf.Ticker(code[3:])
            info = ticker.info
            return {
                "name": info.get("shortName", ""),
                "sector": info.get("sector", ""),
                "price": info.get("currentPrice", 0),
            }
        except Exception as e:
            logger.debug(f"  yfinance获取{code}信息失败: {e}")
    
    return None


def get_available_sources() -> Dict[str, bool]:
    """返回可用的数据源"""
    return {
        "eastmoney": EDF_AVAILABLE,
        "sina": SINA_AVAILABLE,
        "tencent": TX_AVAILABLE,
        "akshare": AKSHARE_AVAILABLE,
        "yfinance": YFINANCE_AVAILABLE,
    }
