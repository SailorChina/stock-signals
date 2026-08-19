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
from .hot_fetcher import fetch_hot_stocks as _fetch_hot_stocks_live



logger = logging.getLogger("stock-signals")

# ─────────────────────────────────────────────────────────────────────
# 股票池（指数成分股精选）
# ─────────────────────────────────────────────────────────────────────

STOCK_POOLS: Dict[str, List[str]] = {
    # ── A 股：沪深 300 + 核心龙头 ─────────────────────────────────
    "SH": [
        # 消费
        "SH.600887", "SH.603288", "SH.603259", "SH.600085",
        "SH.603899", "SH.600104", "SH.603160",
        # 科技 / 半导体
        "SH.688981", "SH.688012", "SH.688396", "SH.688111",
        "SH.600584", "SH.603501", "SH.688256",
        # 新能源 / 光伏
        "SH.601012", "SH.601865", "SH.600438", "SH.600460",
        "SH.603010", "SH.688599",
        # 医药
        "SH.600276", "SH.600196", "SH.600572",
        # 周期 / 资源
        "SH.600028", "SH.600026", "SH.601088", "SH.601857",
        "SH.600309", "SH.600585",
        # 地产 / 基建
        "SH.600048", "SH.601155", "SH.600000",
    ],
    "SZ": [
        # 消费
        "SZ.000858", "SZ.002304", "SZ.002557", "SZ.002714",
        "SZ.000063", "SZ.002415", "SZ.002475",
        # 科技 / 电子
        "SZ.300750", "SZ.300014", "SZ.300124", "SZ.300308",
        "SZ.300408", "SZ.002371", "SZ.002439", "SZ.002236",
        # 新能源
        "SZ.002594", "SZ.002460", "SZ.002459",
        # 医药
        "SZ.300015", "SZ.000661", "SZ.300122", "SZ.002007",
        "SZ.300760",
        # 制造 / 工业
        "SZ.000333", "SZ.000651", "SZ.000725",
    ],
    # ── 港股：恒生指数 + 恒生科技 ────────────────────────────────
    "HK": [
        # 互联网 / 科技
        "HK.00700", "HK.09988", "HK.03690", "HK.09618",
        "HK.09888", "HK.02382", "HK.09999", "HK.09660",
        "HK.02015", "HK.02359",
        # 消费 / 餐饮
        "HK.00686", "HK.00291", "HK.00322", "HK.01071",
        "HK.09922",
        # 新能源 / 汽车
        "HK.09866", "HK.09961",
        # 地产 / 综合
        "HK.00012", "HK.00001", "HK.00003",
        # 电信 / 能源
        "HK.00006", "HK.00009", "HK.00883",
    ],
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
    # A股银行/金融
    # 港股银行
    # 美股银行/金融
    "US.JPM", "US.BAC", "US.WFC", "US.C", "US.GS", "US.MS",
    "US.USB", "US.PNC", "US.TFC", "US.BK", "US.AXP",
    # 常见ETF
    "US.SPY", "US.QQQ", "US.IWM", "US.VTI", "US.VOO",
    "US.EFA", "US.EEM", "US.VEA", "US.VWO", "US.BND",
    "US.TLT", "US.GLD", "US.SLV", "US.XLF", "US.VNQ",
    "US.XLE", "US.XLU",

    "SH.601398", "SH.601288", "SH.601166", "SH.600030", "SH.600036", "SH.601818", "SH.601881", "SH.600016", "SZ.000001", "SZ.000002", "SZ.002142", "SZ.000776", "SZ.002807", "SZ.001227", "HK.00005", "HK.02388", "HK.03968", "HK.00939", "HK.01288", "HK.03988", "HK.02888",}

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

_A_HOT_STOCKS_POOL = [
    "SH.600519", "SH.601318", "SZ.000651", "SZ.002594", "SH.600887", "SZ.000858", "SH.600276", "SH.601919", "SZ.300059", "SZ.000333", "SZ.000725", "SH.601012", "SZ.300750", "SH.603288", "SZ.002415", "SZ.000895", "SH.600900", "SH.600585", "SZ.002304", "SZ.002714", "SZ.000568", "SH.603259", "SH.601088", "SH.600436", "SZ.300015", "SH.601888", "SH.600309", "SZ.002460", "SH.600009", "SZ.000661", "SZ.300274", "SZ.300760", "SZ.002027", "SH.601633", "SH.600763", "SZ.300142", "SH.600702", "SZ.002271", "SZ.300146", "SH.601155", "SZ.002230", "SH.601899", "SH.600196", "SZ.002024", "SH.600031", "SH.600660", "SZ.002466", "SH.600000", "SZ.000063", "SZ.000538", "SH.601988", "SZ.002241", "SZ.002475", "SH.600570", "SH.600089", "SH.600048", "SH.601668", "SZ.000625", "SZ.002508", "SH.600111", "SZ.300033", "SH.601939", "SZ.000423", "SH.601328", "SH.600150", "SZ.002372", "SH.600886", "SZ.000338", "SH.601766", "SH.688981", "SH.603019", "SH.600584", "SZ.000100", "SH.601857", "SH.600690", "SZ.002407", "SH.603986", "SH.601688", "SH.600566", "SZ.000977", "SZ.002340", "SZ.002352", "SZ.002129", "SH.600438", "SH.601127", "SH.600028", "SH.600703", "SH.600050", "SZ.002456", "SZ.000792", "SH.601933", "SZ.002007", "SZ.000768", "SH.600104", "SH.601600", "SH.600893", "SH.601006", "SH.603993", "SZ.300308", "SH.600010", "SH.600795", "SH.601390", "SH.601607", "SH.600118", "SZ.002049", "SZ.000963", "SH.601669", "SZ.002202", "SH.600332", "SZ.300014", "SZ.002312", "SZ.300251", "SH.600588", "SH.600298", "SH.600362", "SH.601777", "SH.600460", "SZ.002192", "SZ.000559", "SH.600905", "SH.600019", "SH.601138", "SZ.002050", "SH.600096", "SH.601009", "SZ.002677", "SZ.000799", "SH.601985", "SZ.300496", "SZ.000623", "SH.601727", "SH.600487", "SH.601788", "SH.600518", "SZ.300136", "SZ.300058", "SH.600316", "SZ.002371", "SH.603799", "SH.601998", "SH.600750", "SH.600809", "SH.600745", "SZ.002156", "SZ.002709", "SZ.002236", "SZ.002008", "SH.600522", "SH.600352", "SZ.002183", "SH.600391", "SH.601169", "SZ.000157", "SH.600446", "SZ.002038", "SH.601179", "SZ.300027", "SH.600267", "SZ.002555", "SZ.000876", "SH.600085", "SH.600418", "SZ.002074", "SZ.002223", "SZ.002463", "SZ.300377", "SH.600547", "SZ.300124", "SZ.002603", "SH.601800", "SZ.002405", "SH.600109", "SH.600221", "SZ.000831", "SH.600029", "SH.603501", "SZ.300999", "SH.601628", "SH.601225", "SZ.300017", "SZ.000938", "SH.601186", "SZ.002432", "SH.601336", "SH.601360", "SZ.002185", "SZ.300502", "SH.601168", "SZ.002507", "SZ.002261", "SH.688256", "SZ.002176", "SH.600895", "SZ.000997", "SZ.300433", "SH.600760", "SZ.300476", "SH.600999", "SH.600406", "SH.600489", "SZ.300144", "SZ.000988", "SH.600875", "SH.601106", "SH.601377", "SH.600143", "SZ.002030", "SZ.000723", "SH.600839", "SZ.002353", "SZ.002384", "SH.600256", "SZ.300024", "SH.600600", "SZ.002273", "SZ.000777", "SH.600771", "SH.600219", "SZ.300122", "SZ.000630", "SZ.300418", "SZ.002294", "SH.600938", "SH.603027", "SH.600516", "SZ.002281", "SZ.300450", "SH.600176", "SZ.000930", "SZ.300079", "SZ.000860", "SH.601901", "SZ.300339", "SH.603444", "SZ.002739", "SZ.300003", "SH.600340", "SZ.300347", "SH.600392", "SH.600315", "SH.600674", "SH.600183", "SZ.300529", "SZ.002422", "SH.600699", "SH.600015", "SH.600879", "SZ.300498", "SH.601000", "SZ.300223", "SH.600153", "SZ.300896", "SH.600100", "SH.600521", "SH.601872", "SH.601601", "SZ.002385", "SZ.000807", "SZ.300238", "SZ.000878", "SZ.000425", "SZ.000738", "SH.603866", "SZ.000066", "SH.600559", "SH.600188", "SZ.000039", "SZ.000069", "SH.601618", "SH.600158", "SZ.300676", "SH.600038", "SZ.000636", "SH.688825", "SH.601099", "SH.600536", "SZ.000410", "SZ.002032", "SH.600867", "SZ.002600", "SH.600021", "SZ.002624", "SH.600498", "SZ.002821", "SH.600941", "SH.600172", "SH.600066", "SH.600635", "SZ.002465", "SH.600001", "SH.600002", "SH.600003", "SH.600004", "SH.600005", "SH.600006", "SH.600007", "SH.600008", "SH.600011", "SH.600012", "SH.600013",
]

_HK_HOT_STOCKS_POOL = [
    'HK.00001', 'HK.00002', 'HK.00003', 'HK.00004', 'HK.00006', 'HK.00007', 'HK.00008', 'HK.00009', 'HK.00010', 'HK.00012',
    'HK.00013', 'HK.00014', 'HK.00015', 'HK.00016', 'HK.00017', 'HK.00018', 'HK.00019', 'HK.00020', 'HK.00021', 'HK.00022',
    'HK.00023', 'HK.00024', 'HK.00025', 'HK.00026', 'HK.00027', 'HK.00028', 'HK.00029', 'HK.00030', 'HK.00031', 'HK.00032',
    'HK.00033', 'HK.00034', 'HK.00035', 'HK.00036', 'HK.00037', 'HK.00038', 'HK.00039', 'HK.00040', 'HK.00041', 'HK.00042',
    'HK.00043', 'HK.00044', 'HK.00045', 'HK.00046', 'HK.00047', 'HK.00048', 'HK.00049', 'HK.00050', 'HK.00051', 'HK.00052',
    'HK.00053', 'HK.00054', 'HK.00055', 'HK.00056', 'HK.00057', 'HK.00058', 'HK.00059', 'HK.00060', 'HK.00061', 'HK.00062',
    'HK.00063', 'HK.00064', 'HK.00065', 'HK.00066', 'HK.00067', 'HK.00068', 'HK.00069', 'HK.00070', 'HK.00071', 'HK.00072',
    'HK.00073', 'HK.00074', 'HK.00075', 'HK.00076', 'HK.00077', 'HK.00078', 'HK.00079', 'HK.00080', 'HK.00081', 'HK.00082',
    'HK.00083', 'HK.00084', 'HK.00085', 'HK.00086', 'HK.00087', 'HK.00088', 'HK.00089', 'HK.00090', 'HK.00091', 'HK.00092',
    'HK.00093', 'HK.00094', 'HK.00095', 'HK.00096', 'HK.00097', 'HK.00098', 'HK.00099', 'HK.00100', 'HK.00101', 'HK.00102',
    'HK.00103', 'HK.00104', 'HK.00105', 'HK.00106', 'HK.00107', 'HK.00108', 'HK.00109', 'HK.00110', 'HK.00111', 'HK.00112',
    'HK.00113', 'HK.00114', 'HK.00115', 'HK.00116', 'HK.00117', 'HK.00118', 'HK.00119', 'HK.00120', 'HK.00121', 'HK.00122',
    'HK.00123', 'HK.00124', 'HK.00125', 'HK.00126', 'HK.00127', 'HK.00128', 'HK.00129', 'HK.00130', 'HK.00131', 'HK.00132',
    'HK.00133', 'HK.00134', 'HK.00135', 'HK.00136', 'HK.00137', 'HK.00138', 'HK.00139', 'HK.00140', 'HK.00141', 'HK.00142',
    'HK.00143', 'HK.00144', 'HK.00145', 'HK.00146', 'HK.00147', 'HK.00148', 'HK.00149', 'HK.00150', 'HK.00151', 'HK.00152',
    'HK.00153', 'HK.00154', 'HK.00155', 'HK.00156', 'HK.00157', 'HK.00158', 'HK.00159', 'HK.00160', 'HK.00161', 'HK.00162',
    'HK.00163', 'HK.00164', 'HK.00165', 'HK.00166', 'HK.00167', 'HK.00168', 'HK.00169', 'HK.00170', 'HK.00171', 'HK.00172',
    'HK.00173', 'HK.00174', 'HK.00175', 'HK.00176', 'HK.00177', 'HK.00178', 'HK.00179', 'HK.00180', 'HK.00181', 'HK.00182',
    'HK.00183', 'HK.00184', 'HK.00185', 'HK.00186', 'HK.00187', 'HK.00188', 'HK.00189', 'HK.00190', 'HK.00191', 'HK.00192',
    'HK.00193', 'HK.00194', 'HK.00195', 'HK.00196', 'HK.00197', 'HK.00198', 'HK.00199', 'HK.00200', 'HK.00201', 'HK.00202',
    'HK.00203', 'HK.00204', 'HK.00205', 'HK.00206', 'HK.00207', 'HK.00208', 'HK.00209', 'HK.00210', 'HK.00211', 'HK.00212',
    'HK.00213', 'HK.00214', 'HK.00215', 'HK.00216', 'HK.00217', 'HK.00218', 'HK.00219', 'HK.00220', 'HK.00221', 'HK.00222',
    'HK.00223', 'HK.00224', 'HK.00225', 'HK.00226', 'HK.00227', 'HK.00228', 'HK.00229', 'HK.00230', 'HK.00231', 'HK.00232',
    'HK.00233', 'HK.00234', 'HK.00235', 'HK.00236', 'HK.00237', 'HK.00238', 'HK.00239', 'HK.00240', 'HK.00241', 'HK.00242',
    'HK.00243', 'HK.00244', 'HK.00245', 'HK.00246', 'HK.00247', 'HK.00248', 'HK.00249', 'HK.00250', 'HK.00251', 'HK.00252',
    'HK.00253', 'HK.00254', 'HK.00255', 'HK.00256', 'HK.00257', 'HK.00258', 'HK.00259', 'HK.00260', 'HK.00261', 'HK.00262',
    'HK.00263', 'HK.00264', 'HK.00265', 'HK.00266', 'HK.00267', 'HK.00268', 'HK.00269', 'HK.00270', 'HK.00271', 'HK.00272',
    'HK.00273', 'HK.00274', 'HK.00275', 'HK.00276', 'HK.00277', 'HK.00278', 'HK.00279', 'HK.00280', 'HK.00281', 'HK.00282',
    'HK.00283', 'HK.00284', 'HK.00285', 'HK.00286', 'HK.00287', 'HK.00288', 'HK.00289', 'HK.00290', 'HK.00291', 'HK.00292',
    'HK.00293', 'HK.00294', 'HK.00295', 'HK.00296', 'HK.00297', 'HK.00298', 'HK.00299', 'HK.00300', 'HK.00301', 'HK.00302',
]

def _fetch_hot_stocks(market: str, top_n: int = 300) -> List[str]:
    """Get hot stocks - live API first, fallback to static pool."""
    live_codes = _fetch_hot_stocks_live(market, top_n)
    live_codes = [c for c in live_codes if not _is_blacklisted(c)]
    if live_codes:
        logger.info(f"  Hot stocks (live): {len(live_codes)}")
        return live_codes
    logger.info("  Hot stocks: fallback to static pool")
    if market == "A":
        codes = _A_HOT_STOCKS_POOL[:top_n]
    elif market == "HK":
        codes = _HK_HOT_STOCKS_POOL[:top_n]
    elif market == "US":
        codes = _US_HOT_STOCKS_POOL[:top_n]
    else:
        codes = []
    return [c for c in codes if not _is_blacklisted(c)]


def sync_hot_stocks(market: str, top_n: int = 300) -> int:
    """Sync today hot stocks to static pool and persist to file."""
    from .hot_fetcher import fetch_a_hot_stocks, fetch_hk_hot_stocks, fetch_us_hot_stocks
    if market == "A":
        codes = fetch_a_hot_stocks(top_n)
    elif market == "HK":
        codes = fetch_hk_hot_stocks(top_n)
    elif market == "US":
        codes = fetch_us_hot_stocks(top_n)
    else:
        return 0
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
    "SH": "A股\u30fb\u6caa", "SZ": "A股\u30fb\u6df1",
    "HK": "\u9999\u6e2f", "US": "\u7f8e\u80a1", "A": "A\u80a1",
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


def _analyze_one(code, capital=None, short_pct=None, delay=1.0):

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
        tp = generate_trade_plan(ind, sr, phase, vcp_res)
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
    if code.startswith("SH") or code.startswith("SZ"):
        return "A"
    elif code.startswith("HK"):
        return "HK"
    elif code.startswith("US"):
        return "US"
    return "unknown"


def scan(markets=None, config=None, output_json=False, output_file=""):
    if config is None:
        config = ScanConfig()
    if markets is None:
        markets = ["A", "HK", "US"]
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


def _analyze_batch(codes, delay):
    """并行分析一批股票"""
    results = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(_analyze_one, code, delay=delay): code for code in codes}
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
        markets = ["A", "HK", "US"]
    
    picks = {m: [] for m in markets}
    watchlist = {m: [] for m in markets}
    total_analyzed = 0
    total_failed = 0
    
    logger.info(f"开始并行扫描 {markets} 市场...")
    
    for market in markets:
        market_codes = _get_market_codes(market)
        logger.info(f"  {MARKET_NAMES.get(market, market)}: {len(market_codes)} 只候选")
        
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
    if market == "A":
        codes = []
        for prefix in ("SH", "SZ"):
            codes.extend(STOCK_POOLS.get(prefix, []))
    else:
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
        }
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj
