# -*- coding: utf-8 -*-
"""动态获取指数成分股 - 混合方案D"""
from __future__ import annotations
import logging
import time
import json
import os
from typing import List, Optional

logger = logging.getLogger("stock-signals")
_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".pool_cache")
_CACHE_TTL = 86400
os.makedirs(_CACHE_DIR, exist_ok=True)

def _cache_path(market: str) -> str:
    return os.path.join(_CACHE_DIR, f"{market}_pool.json")

def _load_cache(market: str) -> Optional[List[str]]:
    path = _cache_path(market)
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if time.time() - data.get("time", 0) < _CACHE_TTL:
                logger.info(f"  使用缓存: {market} {len(data.get('codes', []))} 只")
                return data.get("codes", [])
    except Exception as ex:
        logger.warning(f"  加载缓存失败 {market}: {ex}")
    return None

def _save_cache(market: str, codes: List[str]):
    path = _cache_path(market)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"time": time.time(), "codes": codes}, f, ensure_ascii=False)
        logger.info(f"  缓存更新: {market} {len(codes)} 只")
    except Exception as ex:
        logger.warning(f"  保存缓存失败 {market}: {ex}")

def get_a_share_constituents() -> List[str]:
    """获取A股指数成分股（沪深300 + 中证500）"""
    cached = _load_cache("A")
    if cached:
        return cached
    codes: List[str] = []
    try:
        import akshare as ak
        try:
            df = ak.index_stock_cons_csindex(symbol="000300")
            sh = [f"SH.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("6")]
            sz = [f"SZ.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("0") or str(c).startswith("3")]
            codes.extend(sh + sz)
            logger.info(f"  AkShare沪深300: {len(sh)}沪 + {len(sz)}深")
        except Exception as e:
            logger.warning(f"  AkShare沪深300失败: {e}")
        try:
            df = ak.index_stock_cons_csindex(symbol="000905")
            sh = [f"SH.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("6")]
            sz = [f"SZ.{c}" for c in df["成分券代码"].tolist() if str(c).startswith("0") or str(c).startswith("3")]
            codes.extend(sh + sz)
            logger.info(f"  AkShare中证500: {len(sh)}沪 + {len(sz)}深")
        except Exception as e:
            logger.warning(f"  AkShare中证500失败: {e}")
    except ImportError:
        logger.warning("  AkShare未安装，跳过动态获取")
    return list(dict.fromkeys(codes))

def get_hk_constituents() -> List[str]:
    """获取港股指数成分股"""
    cached = _load_cache("HK")
    if cached:
        return cached
    codes: List[str] = []
    try:
        import akshare as ak
        try:
            df = ak.index_stock_cons_weight_hsgt(stock=["恒指"])
            codes.extend([f"HK.{c.zfill(5)}" for c in df["股票代码"].tolist()])
            logger.info(f"  AkShare恒生指数: {len(codes)} 只")
        except Exception as e:
            logger.warning(f"  AkShare恒生指数失败: {e}")
        try:
            df = ak.index_stock_cons_weight_hsgt(stock=["恒生科技"])
            codes.extend([f"HK.{c.zfill(5)}" for c in df["股票代码"].tolist()])
            logger.info(f"  AkShare恒生科技: +{len(codes)} 只")
        except Exception as e:
            logger.warning(f"  AkShare恒生科技失败: {e}")
    except ImportError:
        logger.warning("  AkShare未安装，跳过动态获取")
    return list(dict.fromkeys(codes))

def get_us_constituents() -> List[str]:
    """获取美股指数成分股（使用静态池为主）"""
    return []

def get_constituents(market: str) -> List[str]:
    """获取指定市场的成分股"""
    if market == "A":
        return get_a_share_constituents()
    elif market == "HK":
        return get_hk_constituents()
    elif market == "US":
        return get_us_constituents()
    return []
