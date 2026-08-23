# -*- coding: utf-8 -*-
"""股票筛选引擎 — 多市场扫描 + 智能选股"""
from __future__ import annotations

import sys
import os as _os
import time
import json
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


from .indicators import fetch_kline, compute_indicators, signal_summary
from .scoring import compute_rating, RATINGS
from ._resonance import compute_timeframe_resonance
from ._sr import compute_support_resistance, generate_trade_plan
from ._vcp import detect_vcp
from ._episodic_pivot import detect_episodic_pivot
from .config import config
from .hot_fetcher import fetch_hot_stocks as _fetch_hot_stocks_live, MKT_CAP, MIN_MARKET_CAP
from .sector import get_sector_ranking, get_sector_bonus



logger = logging.getLogger("stock-signals")

# ─────────────────────────────────────────────────────────────────────
# 股票池（指数成分股精选）
# ─────────────────────────────────────────────────────────────────────

STOCK_POOLS: Dict[str, List[str]] = {
    # ── 美股：道指 + 标普 500 + 纳指 100 精选 ────────────────────
    "US": [
        # 科技
        "US.NVDA", "US.AAPL", "US.MSFT", "US.GOOG", "US.AMZN",
        "US.META", "US.TSLA", "US.AVGO", "US.CSCO", "US.ORCL",
        "US.AMAT", "US.LRCX", "US.ASML",
        "US.INTC", "US.QCOM", "US.MU", "US.NXPI",
        "US.MCD", "US.NKE", "US.TGT", "US.KO", "US.PEP",
        "US.WMT", "US.COST",
        # 医药
        "US.JNJ", "US.PFE", "US.UNH", "US.LLY", "US.ABBV",
        "US.MRK", "US.BMY", "US.AMGN", "US.GILD",
        # 工业 / 周期
        "US.HON", "US.CAT", "US.BA", "US.DE",
        "US.FCX", "US.NEM", "US.CP",
        # 能源
        "US.XOM", "US.COP", "US.OXY",
    ],
}

# +--- 黑名单：银行/金融/ETF（用户明确要求过滤） ---+
BLACKLIST = {
    # 美股银行/金融
    "US.JPM", "US.BAC", "US.WFC", "US.C", "US.GS", "US.MS",
    "US.USB", "US.PNC", "US.TFC", "US.BK", "US.AXP",
    # 常见ETF
    "US.SPY", "US.QQQ", "US.IWM", "US.VTI", "US.VOO",
    "US.EFA", "US.EEM", "US.VEA", "US.VWO", "US.BND",
    "US.TLT", "US.GLD", "US.SLV", "US.XLF", "US.VNQ",
    "US.XLE", "US.XLU",

}


RATING_CN = {"Buy": "买入", "Overweight": "偏多", "Hold": "观望", "Underweight": "偏空", "Sell": "卖出"}
PHASE_CN = {"accumulation": "吸筹阶段", "early_rally": "上涨早期", "rally": "上涨阶段", "distribution": "派发阶段", "decline": "下跌阶段", "unknown": "未知"}
ALIGN_CN = {"strong_up": "强共振看多", "aligned": "共振看多", "mixed": "分歧", "aligned_down": "共振看空", "strong_down": "强共振看空", "none": "无"}

def _is_blacklisted(code: str) -> bool:
    # v2.7 黑名单过滤：银行/ETF
    return code in BLACKLIST
# +--- 动态热门股：3天持久化注册表（每日TOP100） ---+
_HOT_REGISTRY_PATH = _os.path.join(_os.path.dirname(__file__), '.hot_registry.json')

def _load_hot_registry() -> Dict[str, str]:
    """加载热门股注册表 {code: last_seen_date}"""
    try:
        if _os.path.exists(_HOT_REGISTRY_PATH):
            with open(_HOT_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"  加载热门股注册表失败: {e}")
    return {}

def _save_hot_registry(registry: Dict[str, str]):
    """保存热门股注册表"""
    try:
        with open(_HOT_REGISTRY_PATH, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"  保存热门股注册表失败: {e}")

def _update_hot_registry(today_codes: List[str]) -> List[str]:
    """更新注册表：标记今日热门股，清除3天未出现的股票"""
    registry = _load_hot_registry()
    today = time.strftime('%Y-%m-%d')
    for code in today_codes:
        registry[code] = today
    # 清除超过3天未出现的股票
    cutoff = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    to_remove = [c for c, d in registry.items() if d < cutoff]
    for c in to_remove:
        del registry[c]
    _save_hot_registry(registry)
    logger.info(f"  热门股注册表: {len(registry)} 只在库 (今日更新 {len(today_codes)} 只)")
    return list(registry.keys())



# +--- 备用数据源：免费API获取热门股 ---+
_US_HOT_STOCKS_POOL = [
    'US.AAPL', 'US.MSFT', 'US.GOOG', 'US.AMZN', 'US.NVDA', 'US.META', 'US.TSLA', 'US.AMD', 'US.INTC', 'US.QCOM',
    'US.TXN', 'US.AVGO', 'US.NOW', 'US.CRM', 'US.ADBE', 'US.PANW', 'US.PLTR', 'US.ORCL', 'US.CSCO', 'US.AMAT',
    'US.LRCX', 'US.MU', 'US.APLD', 'US.SYK', 'US.ZBRA', 'US.IDXX', 'US.HOLX', 'US.BAX', 'US.DXCM', 'US.REGN',
    'US.MOH', 'US.UHS', 'US.HCAT', 'US.ALGN', 'US.INCY', 'US.ILMN', 'US.MRNA', 'US.VTRS', 'US.WTW', 'US.AGN',
    'US.JNJ', 'US.UNH', 'US.PFE', 'US.ABBV', 'US.MRK', 'US.BMY', 'US.AMGN', 'US.GILD', 'US.BIIB', 'US.BMRN',
    'US.CELG', 'US.CERN', 'US.VRTX', 'US.ISRG', 'US.ZTS', 'US.WMT', 'US.COST', 'US.HD', 'US.NKE', 'US.MCD',
    'US.SBUX', 'US.DIS', 'US.NFLX', 'US.BKNG', 'US.LUV', 'US.ABNB', 'US.MAR', 'US.YUM', 'US.DPW', 'US.CMG',
    'US.QSR', 'US.PEP', 'US.KO', 'US.MDLZ', 'US.HSY', 'US.CL', 'US.UL', 'US.GIS', 'US.KHC', 'US.LOW',
    'US.TGT', 'US.DLR', 'US.DBID', 'US.WSM', 'US.BBY', 'US.RH', 'US.ANTM', 'US.HON', 'US.CAT', 'US.EMR',
    'US.RTX', 'US.GE', 'US.UNP', 'US.UPS', 'US.BA', 'US.LMT', 'US.NOC', 'US.GD', 'US.MMM', 'US.ETN',
    'US.ROK', 'US.PHI', 'US.FLR', 'US.IRTC', 'US.JEC', 'US.JBHT', 'US.ODFL', 'US.EXPD', 'US.CHRW', 'US.XPO',
    'US.KNX', 'US.ABM', 'US.ALLE', 'US.APD', 'US.BKR', 'US.CEIX', 'US.DLLR', 'US.ECL', 'US.FEI', 'US.XOM',
    'US.CVV', 'US.EOG', 'US.PMC', 'US.SOAP', 'US.DVN', 'US.HP', 'US.MPC', 'US.OXY', 'US.CTRA', 'US.WLL',
    'US.PR', 'US.RRC', 'US.THO', 'US.EQT', 'US.LIN', 'US.DD', 'US.NEM', 'US.FCX', 'US.AAA', 'US.CLF',
    'US.SCCO', 'US.TECK', 'US.NUE', 'US.CF', 'US.OLN', 'US.VMC', 'US.MLM', 'US.BIO', 'US.KRA', 'US.PKG',
    'US.V', 'US.MA', 'US.PYPL', 'US.SQ', 'US.BRO', 'US.AFG', 'US.ICE', 'US.MC', 'US.SPG', 'US.TWI',
    'US.VZ', 'US.T', 'US.CHTR', 'US.TMUS', 'US.LUMN', 'US.FYBR', 'US.AMT', 'US.ARE', 'US.BXP', 'US.CDR',
    'US.EQIX', 'US.FRT', 'US.INN', 'US.KIM', 'US.MAA', 'US.NNN', 'US.OHI', 'US.PGRE', 'US.PS', 'US.SPU',
    'US.VTR', 'US.WPC', 'US.XHR', 'US.ZETA', 'US.F', 'US.GM', 'US.STLA', 'US.RIVN', 'US.MO', 'US.TAP',
    'US.BTI', 'US.TXT', 'US.AAB', 'US.AAC', 'US.AAD', 'US.AAE', 'US.AAF', 'US.AAG', 'US.AAH', 'US.AAI',
    'US.AAJ', 'US.AAK', 'US.AAL', 'US.AAM', 'US.AAN', 'US.AAO', 'US.AAP', 'US.AAQ', 'US.AAR', 'US.AAS',
    'US.AAT', 'US.AAU', 'US.AAV', 'US.AAW', 'US.AAX', 'US.AAY', 'US.AAZ', 'US.ABA', 'US.ABB', 'US.ABC',
    'US.ABD', 'US.ABE', 'US.ABF', 'US.ABG', 'US.ABH', 'US.ABI', 'US.ABJ', 'US.ABK', 'US.ABL', 'US.ABN',
    'US.ABO', 'US.ABP', 'US.ABQ', 'US.ABR', 'US.ABS', 'US.ABT', 'US.ABU', 'US.ABV', 'US.ABW', 'US.ABX',
    'US.ABY', 'US.ABZ', 'US.ACA', 'US.ACB', 'US.ACC', 'US.ACD', 'US.ACE', 'US.ACF', 'US.ACG', 'US.ACH',
    'US.ACI', 'US.ACJ', 'US.ACK', 'US.ACL', 'US.ACM', 'US.ACN', 'US.ACO', 'US.ACP', 'US.ACQ', 'US.ACR',
    'US.ACS', 'US.ACT', 'US.ACU', 'US.ACV', 'US.ACW', 'US.ACX', 'US.ACY', 'US.ACZ', 'US.ADA', 'US.ADB',
    'US.ADC', 'US.ADD', 'US.ADE', 'US.ADF', 'US.ADG', 'US.ADH', 'US.ADI', 'US.ADJ', 'US.ADK', 'US.ADL',
    'US.ADM', 'US.ADN', 'US.ADO', 'US.ADP', 'US.ADQ', 'US.ADR', 'US.ADS', 'US.ADT', 'US.ADU', 'US.ADV',
    'US.ADW', 'US.ADX', 'US.ADY', 'US.ADZ', 'US.AEA', 'US.AEB', 'US.AEC', 'US.AED', 'US.AEE', 'US.AEF',
]


def _fetch_hot_stocks(market: str, top_n: int = 300) -> List[str]:
    """Get hot stocks - live API first, fallback to static pool."""
    live_codes = _fetch_hot_stocks_live(market, top_n)
    live_codes = [c for c in live_codes if not _is_blacklisted(c)]
    if live_codes:
        logger.info(f"  Hot stocks (live): {len(live_codes)}")
        return live_codes
    logger.info("  Hot stocks: fallback to static pool")
    codes = _US_HOT_STOCKS_POOL[:top_n]


def sync_hot_stocks(market: str, top_n: int = 300) -> int:
    """Sync today hot stocks to static pool and persist to file."""
    from .hot_fetcher import fetch_us_hot_stocks
    codes = fetch_us_hot_stocks(top_n)
    codes = [c for c in codes if not _is_blacklisted(c)]
    if not codes:
        logger.warning(f"  No hot stocks to sync ({market})")
        return 0
    pool_key = f"_{market.upper()}_HOT_STOCKS_POOL"
    existing = globals().get(pool_key, [])
    merged = list(dict.fromkeys(codes + existing))[:top_n]
    globals()[pool_key] = merged
    _write_pool_to_file(pool_key, merged, __file__)
    logger.info(f"  Synced {len(codes)} hot stocks to {market} pool (total {len(merged)})")
    return len(codes)


def _write_pool_to_file(var_name: str, codes: List[str], file_path=None):
    """Write hot stock pool back to screener.py."""
    import re as _re
    pool_str = ", ".join('"'+c+'"' for c in codes)
    pat = _re.escape(var_name) + r'\s*=\s*\[([^\]]*?)\n\s*\]'
    repl = var_name + " = [\n    " + pool_str + ",\n]"
    _fp = file_path or __file__
    with open(_fp, 'r', encoding='utf-8') as f:
        cnt = f.read()
    cnt = _re.sub(pat, repl, cnt, count=1)
    with open(_fp, 'w', encoding='utf-8') as f:
        f.write(cnt)


MARKET_NAMES = {
    "US": "美股",
}


RATING_ORDER = {"Buy": 0, "Overweight": 1, "Hold": 2, "Underweight": 3, "Sell": 4}


@dataclass
class ScanConfig:
    """\u626b\u63cf\u914d\u7f6e"""
    min_score: float = 60.0
    watchlist_min: float = 55.0
    strong_score: float = 65.0
    min_alignment: str = "aligned"
    preferred_phases: tuple = ("accumulation", "early_rally", "rally")
    require_golden_cross: bool = True
    require_macd_cross: bool = False
    allow_td_buy: bool = True
    allow_oversold: bool = False
    max_delay: float = 0.3
    max_per_market: int = 5


@dataclass
class ScanResult:
    code: str
    market: str
    score: float
    rating: str
    alignment: str
    trend_phase: str
    entry: float = 0.0
    stop_loss: float = 0.0
    target_1: float = 0.0
    target_2: float = 0.0
    risk_reward: float = 0.0
    position_pct: float = 0.0
    last_close: float = 0.0
    reasons: List[str] = field(default_factory=list)
    trade_plan: Optional[dict] = None
    pullback_score: int = 0
    holding_period: str = ""



def compute_holding_period(entry: float, target_1: float, target_2: float, stop: float, atr: float, alignment: str, trend_phase: str) -> str:
    """根据ATR距离、多周期共振、趋势阶段计算建议持仓周期"""
    if entry <= 0 or atr <= 0:
        return "未知"
    risk = entry - stop if entry > stop else atr * 1.5
    reward1 = target_1 - entry if target_1 > entry else atr * 2
    atr_dist_1 = reward1 / risk if risk > 0 else 0
    align_w = {"strong_up": 1.0, "aligned": 0.5, "mixed": 0.0, "aligned_down": -0.5, "strong_down": -1.0}.get(alignment, 0)
    phase_adj = {"early_rally": 0, "rally": 0.5, "accumulation": -0.3, "distribution": -0.5, "decline": -1.0}.get(trend_phase, 0)
    score = atr_dist_1 + align_w * 2 + phase_adj * 2
    if score >= 8: return "中线(1-3月)"
    elif score >= 5: return "波段(1-4周)"
    elif score >= 2: return "短线(1-2周)"
    else: return "超短(1-5天)"

def _analyze_one(code, capital=None, short_pct=None, delay=1.0, sector_bonus=1.0):

    try:
        # v2.7: 黑名单过滤
        if _is_blacklisted(code):
            logger.info(f"  {code} 在黑名单中(银行/ETF)，跳过")
            return None
        time.sleep(min(delay, 0.5))
        df = fetch_kline(code, "1d", num=300)
        time.sleep(0.2)
        if df is None or df.empty or len(df) < 60:
            return None
        ind = compute_indicators(df, code, "1d")
        rating = compute_rating(ind, capital, short_pct)
        time.sleep(0.2)
        score = rating["score"]
        score = score * sector_bonus
        r_name = rating["rating"]
        resonance = compute_timeframe_resonance(code, ind, capital, short_pct)
        time.sleep(0.2)
        from ._sr import compute_trend_phase
        try:
            phase = compute_trend_phase(df, ind)
        except Exception:
            phase = "unknown"
        sr = compute_support_resistance(df)
        vcp_res = detect_vcp(df, lookback=100)
        ep_res = detect_episodic_pivot(df, lookback=60)
        tp = generate_trade_plan(code, ind, sr, phase, vcp_res)
        # v2.5: VCP 模式增强 - 成交量确认
        if vcp_res.detected and not vcp_res.volume_drying:
            logger.warning(f"  {code} VCP模式但成交量未萎缩，跳过")
            return None
        # v2.4: 扩展度过滤 - 距高点太近则跳过
        dist_to_high = getattr(ind, 'distance_from_52w_high', 0)
        if dist_to_high < 8:
            logger.warning(f"  {code} 距高点仅{abs(dist_to_high):.1f}%，跳过(追高风险)")
            return None
        # v2.4.1: 风险收益比硬过滤(RR<2.0跳过)
        rr = getattr(tp, "risk_reward", 0) if tp else 0
        if rr < 2.0:
            logger.warning(f"  {code} RR={rr:.2f}:1 不足2:1，跳过")
            return None
        # v2.4.2: TD卖出Turn确认 → 卖出信号，跳过
        if getattr(ind, 'td_turn', '') == 'sell_turn':
            logger.warning(f"  {code} TD卖出Turn确认，看跌反转，跳过")
            return None
        # v2.4.2: MACD看跌背离 → 动量衰竭，跳过
        if getattr(ind, 'macd_divergence', '') == 'bearish':
            logger.warning(f"  {code} MACD看跌背离，动量衰竭，跳过")
            return None
        # v2.4.2: 看跌K线形态 → 短期回调风险，跳过
        if getattr(ind, 'candle_pattern', '') in ('bearish_engulfing', 'shooting_star'):
            logger.warning(f"  {code} K线形态{ind.candle_pattern_name}，看跌，跳过")
            return None
        # v2.4: MA5与MA20过度延伸检查
        ma_gap = ind.ma5 / ind.ma20 - 1 if ind.ma20 > 0 else 0
        if ma_gap > 8:
            logger.warning(f"  {code} MA5偏离MA20 {ma_gap:.1f}%，过度延伸，跳过")
            return None
        # v2.13: 下跌阶段硬过滤 - 专业交易员不接飞刀
        if phase == "decline":
            logger.warning(f"  " + code + " 处于下跌阶段，过滤")
            return None
        # v2.13: 强下跌对齐过滤
        if resonance.alignment == "strong_down":
            logger.warning(f"  " + code + " 强下跌对齐，过滤")
            return None
        # v2.13: RSI超卖接飞刀过滤
        if ind.rsi_14 < 30:
            logger.warning(f"  " + code + " RSI=" + ".1f" + " 超卖接飞刀，过滤")
            return None
        # v2.13: 价格远离MA200过滤
        if ind.ma200 > 0:
            dist_ma200 = (ind.last_close - ind.ma200) / ind.ma200 * 100
            if dist_ma200 < -20:
                logger.warning(f"  " + code + " 价格低于MA200 " + ".1f" + "%，趋势过弱，过滤")
                return None
        reasons = []
        pullback_score = 0
        # v2.4: RSI极端超买硬过滤
        if getattr(ind, "rsi_14", 50) > 75:
            logger.warning(f"  {code} RSI={ind.rsi_14:.1f} 极端超买，跳过")
            return None
        if 5 <= dist_to_high <= 15 and ind.rsi_14 < 65:
            pullback_score = 5  # 回调到位 + RSI不超买
        elif -30 <= dist_to_high <= -15 and ind.rsi_14 < 55:
            pullback_score = 10  # 健康回调 + RSI中性
        if pullback_score > 0:
            reasons.append(f"回调入场机会(距高点{dist_to_high:.1f}%)")
        if ind.ma5_ma10_cross == "golden":
            reasons.append("MA5/MA10 \u91d1\u53c9")
        if ind.macd_dif_dea_cross == "golden":
            reasons.append("MACD \u91d1\u53c9")
        if ind.td_buy_setup:
            reasons.append("\u0039\u8f6c\u4e70\u5165\u5e8f\u5217\u5b8c\u6210")
        elif ind.td_buy_count > 0:
            reasons.append(f"\u0039\u8f6c\u4e70\u5165\u8fdb\u884c\u4e2d({ind.td_buy_count}/9)")
        if ind.vol_regime == "low":
            reasons.append("\u4f4e\u6ce2\u52a8\u7387\uff0c\u9707\u8361\u7b79\u5e95")
        if ind.vol_regime == "high":
            reasons.append("\u9ad8\u6ce2\u52a8\u7387\uff0c\u8d8b\u52bf\u660e\u663e")
        if ind.obv_trend == "up":
            reasons.append("OBV \u4e0a\u5347\uff0c\u8d44\u91d1\u6d41\u5165")
        if ep_res.detected:
            reasons.append(f"事件性转折(跳空{ep_res.gap_up_pct:.1f}%+成交量{ep_res.volume_spike:.1f}x)")
        if tp and tp.risk_reward >= 2.0:
            reasons.append(f"\u98ce\u9669\u6536\u76ca\u6bd4 {tp.risk_reward:.1f}:1")
        return ScanResult(
            code=code, market=_code_market(code), score=score, rating=r_name,
            alignment=resonance.alignment, trend_phase=phase,
            entry=tp.entry_zone if tp else 0.0,
            stop_loss=tp.stop_loss if tp else 0.0,
            target_1=tp.target_1 if tp else 0.0,
            target_2=tp.target_2 if tp else 0.0,
            risk_reward=tp.risk_reward if tp else 0.0,
            position_pct=tp.position_size_pct if tp else 0.0,
            last_close=ind.last_close, reasons=reasons,
            trade_plan={
                "entry": tp.entry_zone if tp else 0.0,
                "stop_loss": tp.stop_loss if tp else 0.0,
                "target_1": tp.target_1 if tp else 0.0,
                "target_2": tp.target_2 if tp else 0.0,
                "risk_reward": tp.risk_reward if tp else 0.0,
                "position_pct": tp.position_size_pct if tp else 0.0,
            } if tp else None,
            holding_period=compute_holding_period(
                tp.entry_zone if tp else 0.0,
                tp.target_1 if tp else 0.0,
                tp.target_2 if tp else 0.0,
                tp.stop_loss if tp else 0.0,
                getattr(ind, "atr_14", 0),
                resonance.alignment, phase,
            ),
        )
    except Exception as e:
        err_str = str(e)
        if "频率" in err_str or "rate" in err_str.lower() or "limit" in err_str.lower():
            wait = delay * 2
            logger.warning(f"  {code} 触发API限流，等待 {wait:.1f}s 后重试...")
            time.sleep(wait)
            return _analyze_one(code, delay=delay * 1.5)
        logger.warning(f"  分析 {code} 失败: {e}")
        return None


def _code_market(code):
    return "US" if code.startswith("US") else "unknown"


def scan(markets=None, config=None, output_json=False, output_file=""):
    if config is None:
        config = ScanConfig()
    if markets is None:
        markets = ["US"]
    picks = {m: [] for m in markets}
    watchlist = {m: [] for m in markets}
    total_analyzed = 0
    total_failed = 0
    logger.info(f"\u5f00\u59cb\u626b\u63cf {markets} \u5e02\u573a...")
    for market in markets:
        market_codes = _get_market_codes(market)
        logger.info(f"  {MARKET_NAMES.get(market, market)}: {len(market_codes)} \u53ea\u5019\u9009")
        for code in market_codes:
            result = _analyze_one(code, delay=config.max_delay)
            total_analyzed += 1
            if result is None:
                total_failed += 1
                continue
            if result.score < config.watchlist_min:
                continue
            entry = picks if result.score >= config.min_score else watchlist
            entry[market].append(result)
            if len(picks[market]) > config.max_per_market * 3:
                picks[market] = picks[market][:config.max_per_market * 3]
        picks[market] = _sort_results(picks[market])
        watchlist[market] = _sort_results(watchlist[market])
    final_picks = {m: picks[m][:config.max_per_market] for m in markets}
    final_watch = {m: watchlist[m][:config.max_per_market] for m in markets}
    total_picks = sum(len(v) for v in final_picks.values())
    total_watch = sum(len(v) for v in final_watch.values())
    summary = {
        "scan_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_analyzed": total_analyzed,
        "total_failed": total_failed,
        "total_picks": total_picks,
        "total_watchlist": total_watch,
        "markets_scanned": markets,
    }
    output = {
        "date": time.strftime("%Y-%m-%d"),
        "summary": summary,
        "picks": final_picks,
        "watchlist": final_watch,
    }
    if output_json or output_file:
        import json
        json_output = json.dumps(_serialize(output), ensure_ascii=False, indent=2)
        if output_json:
            print(json_output)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_output)
            logger.info(f"\u7ed3\u679c\u5df2\u4fdd\u5b58\u5230 {output_file}")
    logger.info(
        f"\u626b\u63cf\u5b8c\u6210: \u5206\u6790 {total_analyzed} \u53ea, \u5931\u8d25 {total_failed} \u53ea, "
        f"\u63a8\u8350 {total_picks} \u53ea, \u89c2\u5bdf {total_watch} \u53ea"
    )
    return output


def _analyze_batch(codes, delay, sector_bonus=1.0):
    """并行分析一批股票"""
    results = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(_analyze_one, code, delay=delay, sector_bonus=sector_bonus): code for code in codes}
        for future in as_completed(futures):
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.warning(f"  并行分析失败: {futures[future]} - {e}")
    return results


def scan_parallel(markets=None, config=None, output_json=False, output_file=""):
    """并行扫描版本 - 速度提升3-5倍"""
    if config is None:
        config = ScanConfig()
    if markets is None:
        markets = ["US"]
    
    picks = {m: [] for m in markets}
    watchlist = {m: [] for m in markets}
    total_analyzed = 0
    total_failed = 0
    
    logger.info(f"开始并行扫描 {markets} 市场...")
    
    for market in markets:
        market_codes = _get_market_codes(market)
        logger.info(f"  {MARKET_NAMES.get(market, market)}: {len(market_codes)} 只候选")
        
        # 获取板块热度排名（每个市场只计算一次）
        sector_ranking = get_sector_ranking()
        batch_size = 100
        for i in range(0, len(market_codes), batch_size):
            batch = market_codes[i:i+batch_size]
            batch_results = _analyze_batch(batch, config.max_delay)
            total_analyzed += len(batch)
            
            for result in batch_results:
                if result.score < config.watchlist_min:
                    total_failed += 1
                    continue
                entry = picks if result.score >= config.min_score else watchlist
                entry[market].append(result)
                if len(picks[market]) > config.max_per_market * 3:
                    picks[market] = picks[market][:config.max_per_market * 3]
            
            logger.info(f"  {MARKET_NAMES.get(market, market)}: 已处理 {min(i+batch_size, len(market_codes))}/{len(market_codes)}")
        
        picks[market] = _sort_results(picks[market])
        watchlist[market] = _sort_results(watchlist[market])
    
    final_picks = {m: picks[m][:config.max_per_market] for m in markets}
    final_watch = {m: watchlist[m][:config.max_per_market] for m in markets}
    total_picks = sum(len(v) for v in final_picks.values())
    total_watch = sum(len(v) for v in final_watch.values())
    
    summary = {
        "scan_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_analyzed": total_analyzed,
        "total_failed": total_failed,
        "total_picks": total_picks,
        "total_watchlist": total_watch,
        "markets_scanned": markets,
    }
    output = {
        "date": time.strftime("%Y-%m-%d"),
        "summary": summary,
        "picks": final_picks,
        "watchlist": final_watch,
    }
    
    if output_json or output_file:
        import json
        json_output = json.dumps(_serialize(output), ensure_ascii=False, indent=2)
        if output_json:
            print(json_output)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_output)
            logger.info(f"结果已保存到 {output_file}")
    
    logger.info(
        f"并行扫描完成: 分析 {total_analyzed} 只, 失败 {total_failed} 只, "
        f"推荐 {total_picks} 只, 观察 {total_watch} 只"
    )
    return output

def _get_market_codes(market: str) -> List[str]:
    """获取市场代码列表：静态池 + 持久化热门股注册表（去重）"""
    # 静态池
    codes = list(STOCK_POOLS.get(market, []))
    
    # 从注册表获取热门股（3天持久化）
    hot_registry = _load_hot_registry()
    hot_registry = {k: v for k, v in hot_registry.items() if not _is_blacklisted(k)}
    if hot_registry:
        existing = set(codes)
        for hc in hot_registry:
            if hc not in existing:
                codes.append(hc)
                existing.add(hc)
        logger.info(f"  热门股注册表: +{len(hot_registry)} 只 (总计 {len(codes)} 只)")
    
    # 实时获取今日热门股并更新注册表
    today_hot = []
    try:
        today_hot = _fetch_hot_stocks(market, top_n=300)
        if today_hot:
            _update_hot_registry(today_hot)
    except Exception as e:
        logger.warning(f"  热门股实时更新异常: {e}")
    
    # 加入今日实时热门股
    if today_hot:
        existing = set(codes)
        for hc in today_hot:
            if hc not in existing:
                codes.append(hc)
                existing.add(hc)
        logger.info(f"  今日热门股: +{len(today_hot)} 只 (总计 {len(codes)} 只)")
    # v2.12: filter by market cap >= 10B
    codes = [c for c in codes if MKT_CAP.get(c.replace("US.",""), 0) >= MIN_MARKET_CAP]
    codes = codes[:300]
    return codes


def _sort_results(results):
    alignment_score = {
        "strong_up": 4, "aligned": 3, "mixed": 2,
        "aligned_down": 1, "strong_down": 0, "none": -1,
    }
    phase_score = {
        "accumulation": 3, "early_rally": 4, "rally": 5,
        "distribution": 1, "decline": 0, "unknown": 2,
    }
    # v2.4: 排序优先拉回入场机会(pullback_score) + 评分 + 共振
    return sorted(results, key=lambda r: (
        r.pullback_score,
        r.score,
        alignment_score.get(r.alignment, 0),
        phase_score.get(r.trend_phase, 0),
    ), reverse=True)


def _serialize(obj):
    import json
    if isinstance(obj, ScanResult):
        return {
            "code": obj.code, "score": obj.score, "rating": obj.rating,
            "pullback_score": obj.pullback_score,
            "alignment": obj.alignment, "trend_phase": obj.trend_phase,
            "last_close": obj.last_close, "entry": obj.entry,
            "stop_loss": obj.stop_loss, "target_1": obj.target_1,
            "target_2": obj.target_2, "risk_reward": obj.risk_reward,
            "position_pct": obj.position_pct, "reasons": obj.reasons,
            "rating_cn": RATING_CN.get(obj.rating, obj.rating),
            "trend_phase_cn": PHASE_CN.get(obj.trend_phase, obj.trend_phase),
            "alignment_cn": ALIGN_CN.get(obj.alignment, obj.alignment),
            "holding_period": obj.holding_period,
        }
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj
