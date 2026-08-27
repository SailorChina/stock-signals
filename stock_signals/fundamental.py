# -*- coding: utf-8 -*-
"""
基本面数据获取与过滤
"""
import logging
from dataclasses import dataclass
from typing import Optional, Dict

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

logger = logging.getLogger("tech-signal-FUTU-skill")

# 基本面过滤阈值（宽松版）
MIN_GROSS_MARGIN = 20.0
MIN_NET_MARGIN = 5.0
MIN_REVENUE_GROWTH = -10.0

_fundamental_cache: Dict[str, "FundamentalData"] = {}

@dataclass
class FundamentalData:
    gross_margin: float
    net_margin: float
    revenue_growth: float
    pe_ratio: Optional[float] = None

def fetch_fundamental(symbol: str) -> Optional[FundamentalData]:
    if not HAS_AKSHARE:
        return None
    if symbol in _fundamental_cache:
        return _fundamental_cache[symbol]
    try:
        raw = symbol.replace("US.","").replace(".","")
        df = ak.stock_financial_us_analysis_indicator_em(symbol=raw)
        if df is None or len(df) == 0:
            return None
        row = df.iloc[0]
        gross = row.get("GROSS_PROFIT_RATIO", 0)
        net = row.get("NET_PROFIT_RATIO", 0)
        rev_growth = row.get("OPERATE_INCOME_YOY", 0)

        data = FundamentalData(
            gross_margin=float(gross) if gross else 0,
            net_margin=float(net) if net else 0,
            revenue_growth=float(rev_growth) if rev_growth else 0
        )
        _fundamental_cache[symbol] = data
        return data
    except Exception as e:
        logger.debug(f"  获取 {symbol} 基本面数据失败: {e}")
        return None

def check_fundamental(symbol: str) -> tuple:
    data = fetch_fundamental(symbol)
    if data is None:
        return True, "基本面数据不可用，跳过"
    if data.gross_margin > 0 and data.gross_margin < MIN_GROSS_MARGIN:
        return False, f"毛利率{data.gross_margin:.1f}%<{MIN_GROSS_MARGIN}%"
    if data.net_margin > 0 and data.net_margin < MIN_NET_MARGIN:
        return False, f"净利率{data.net_margin:.1f}%<{MIN_NET_MARGIN}%"
    if data.revenue_growth < MIN_REVENUE_GROWTH:
        return False, f"营收增长{data.revenue_growth:.1f}%<{MIN_REVENUE_GROWTH}%"
    return True, f"Gross={data.gross_margin:.1f}%,Net={data.net_margin:.1f}%,Growth={data.revenue_growth:.1f}%"
