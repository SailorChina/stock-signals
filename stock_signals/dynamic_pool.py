# -*- coding: utf-8 -*-
"""动态股票池管理 - 美股专用"""
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
                logger.info(f"  使用缓存: {market} {len(data.get(chr(99)+chr(111)+chr(100)+chr(101)+chr(115), []))} 只")
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

def get_us_constituents() -> List[str]:
    """获取美股成分股（使用静态池为主）"""
    return []
