# -*- coding: utf-8 -*-
"""热门股获取模块 - 多 API fallback 方案"""
from __future__ import annotations
import logging, time, os, urllib.request, json
from typing import List
logger = logging.getLogger("stock-signals")
for _k in list(os.environ.keys()):
    if 'proxy' in _k.lower(): os.environ.pop(_k, None)
os.environ.setdefault('no_proxy', '*')
os.environ.setdefault('NO_PROXY', '*')

def _parse_a_code(raw):
    """将 SH600519 -> SH.600519, SZ000858 -> SZ.000858"""
    if len(raw) < 3: return ""
    prefix = raw[:2].upper(); num = raw[2:]
    if prefix in ("SH", "SZ", "BJ"): return f"{prefix}.{num}"
    return ""

def fetch_a_hot_stocks(top_n=300):
    """获取A股热门股 - akshare雪球热度榜"""
    codes = []
    try:
        import akshare as ak
        t = time.time()
        df = ak.stock_hot_follow_xq()
        for raw_code in df['股票代码'].head(top_n).astype(str):
            parsed = _parse_a_code(raw_code.strip())
            if parsed and parsed not in codes:
                codes.append(parsed)
        logger.info(f"  A股热门(雪球): {len(codes)}只 ({time.time()-t:.1f}s)")
        return codes
    except Exception as e:
        logger.warning(f"  雪球热门获取失败: {e}")
        # Fallback to Sina
        try:
            t = time.time()
            all_items = []
            for p in range(1, 4):
                url = f"http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page={p}&num=100&sort=changepercent&asc=0&node=hs_a"
                req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0","Referer":"http://finance.sina.com.cn/"})
                resp = urllib.request.urlopen(req, timeout=5)
                items = json.loads(resp.read().decode())
                all_items.extend(items)
                if len(items) < 100: break
            for item in all_items:
                sym = item.get("symbol","")
                if sym:
                    parsed = _parse_a_code(sym)
                    if parsed and parsed not in codes: codes.append(parsed)
            codes = codes[:top_n]
            logger.info(f"  A股热门(Sina): {len(codes)}只 ({time.time()-t:.1f}s)")
            return codes
        except Exception as e2:
            logger.warning(f"  Sina排行也失败: {e2}")
    logger.warning("  A股热门获取失败,使用静态池")
    return codes

def fetch_hk_hot_stocks(top_n=300):
    """港股热门股 - 使用Tencent实时行情验证静态池"""
    static_pool = [
        "HK.00700", "HK.09988", "HK.00001", "HK.02382", "HK.03690",
        "HK.09888", "HK.02015", "HK.02359", "HK.00686", "HK.00291",
        "HK.00322", "HK.01071", "HK.09922", "HK.09866", "HK.09961",
        "HK.00012", "HK.00003", "HK.00006", "HK.00009", "HK.00883",
    ]
    try:
        t = time.time()
        codes_str = ','.join(['hk'+c.split('.')[1] for c in static_pool[:30]])
        url = f"https://qt.gtimg.cn/q={codes_str}"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('gbk')
        valid = []
        for line in data.strip().split('\n'):
            if '~' in line and 'none_match' not in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    vals = parts[-1].strip('\"').split('~')
                    if len(vals) > 2 and vals[2]:
                        valid.append(f"HK.{vals[2].zfill(5)}")
        codes = valid[:top_n]
        logger.info(f"  港股热门(Tencent验证): {len(codes)}只 ({time.time()-t:.1f}s)")
        if codes: return codes
    except Exception as e:
        logger.warning(f"  腾讯港股验证失败: {e}")
    logger.info("  港股: 使用静态池")
    return static_pool[:top_n]

def fetch_us_hot_stocks(top_n=300):
    """美股热门股 - 使用静态池"""
    static_pool = [
        "US.AAPL", "US.MSFT", "US.GOOGL", "US.TSLA", "US.AMZN",
        "US.NVDA", "US.META", "US.NFLX", "US.AMD", "US.INTC",
        "US.JNJ", "US.PFE", "US.UNH", "US.LLY", "US.ABBV",
        "US.MRK", "US.BMY", "US.AMGN", "US.GILD", "US.HON",
        "US.CAT", "US.BA", "US.FCX", "US.XOM", "US.COP",
    ]
    logger.info(f"  美股热门: 静态池 {len(static_pool)}只")
    return static_pool[:top_n]

def fetch_hot_stocks(market, top_n=300):
    """统一入口"""
    if market == "A": return fetch_a_hot_stocks(top_n)
    elif market == "HK": return fetch_hk_hot_stocks(top_n)
    elif market == "US": return fetch_us_hot_stocks(top_n)
    return []
