# -*- coding: utf-8 -*-
"""股票基本信息库：中文名、板块、简介"""
from __future__ import annotations

STOCK_INFO: dict[str, dict] = {
    # ═══════════════════════════════════════════════════════════
    # 美股 US
    # ═══════════════════════════════════════════════════════════
    "US.NVDA": {"name": "英伟达", "sector": "半导体", "desc": "AI芯片龙头，GPU算力核心供应商"},
    "US.AAPL": {"name": "苹果公司", "sector": "消费电子", "desc": "全球最大科技公司，iPhone/Mac生态"},
    "US.MSFT": {"name": "微软", "sector": "软件/云计算", "desc": "Azure云+Office+Copilot AI三驾马车"},
    "US.GOOG": {"name": "谷歌", "sector": "互联网", "desc": "搜索广告+YouTube+云+AI布局全面"},
    "US.AMZN": {"name": "亚马逊", "sector": "电商/云", "desc": "全球最大电商+AWS云双线龙头"},
    "US.META": {"name": "Meta", "sector": "社交/AI", "desc": "Facebook/Instagram母公司，元宇宙+AI投入"},
    "US.TSLA": {"name": "特斯拉", "sector": "新能源汽车", "desc": "电动车龙头，FSD自动驾驶+机器人"},
    "US.AVGO": {"name": "博通", "sector": "半导体", "desc": "网络芯片+定制AI芯片(谷歌TPU)"},
    "US.CSCO": {"name": "思科", "sector": "网络设备", "desc": "企业网络基础设施龙头"},
    "US.ORCL": {"name": "甲骨文", "sector": "软件/云", "desc": "企业数据库+云计算，AI推理芯片布局"},
    "US.AMAT": {"name": "应用材料", "sector": "半导体设备", "desc": "晶圆制造设备全球龙头"},
    "US.LRCX": {"name": "拉姆研究", "sector": "半导体设备", "desc": "刻蚀/薄膜沉积设备，先进制程核心"},
    "US.ASML": {"name": "阿斯麦", "sector": "半导体设备", "desc": "EUV光刻机独家供应商，芯片制造命脉"},
    "US.INTC": {"name": "英特尔", "sector": "半导体", "desc": "传统CPU龙头，转型代工+AI芯片"},
    "US.QCOM": {"name": "高通", "sector": "半导体/手机", "desc": "手机基带芯片龙头，AI手机受益"},
    "US.MU": {"name": "美光科技", "sector": "存储芯片", "desc": "DRAM/NAND存储芯片龙头，AI服务器HBM需求爆发"},
    "US.NXPI": {"name": "恩智浦", "sector": "半导体/汽车", "desc": "汽车芯片+工业控制，自动驾驶核心供应商"},
    "US.MCD": {"name": "麦当劳", "sector": "餐饮消费", "desc": "全球最大连锁餐饮，品牌护城河深"},
    "US.NKE": {"name": "耐克", "sector": "运动消费", "desc": "全球最大运动品牌，DTC转型中"},
    "US.TGT": {"name": "塔吉特", "sector": "零售", "desc": "美国第二大连锁零售商，性价比定位"},
    "US.KO": {"name": "可口可乐", "sector": "饮料消费", "desc": "全球饮料霸主，稳定现金流"},
    "US.PEP": {"name": "百事可乐", "sector": "饮料消费", "desc": "饮料+零食双轮驱动，防御性消费"},
    "US.WMT": {"name": "沃尔玛", "sector": "零售", "desc": "全球最大零售商，电商+物流持续扩张"},
    "US.COST": {"name": "Costco", "sector": "零售", "desc": "会员制仓储超市，高复购高粘性"},
    "US.JNJ": {"name": "强生", "sector": "医药", "desc": "多元化医药+器械，拆分后聚焦制药"},
    "US.PFE": {"name": "辉瑞", "sector": "医药", "desc": "大型制药，新冠疫苗+肿瘤管线"},
    "US.UNH": {"name": "联合健康", "sector": "医疗保险", "desc": "美国最大商业医保，Optum健康服务龙头"},
    "US.LLY": {"name": "礼来", "sector": "医药", "desc": "减肥药Eziciga龙头，阿尔茨海默新药"},
    "US.ABBV": {"name": "艾伯维", "sector": "医药", "desc": "免疫领域龙头，Humira仿制药接力"},
    "US.MRK": {"name": "默克", "sector": "医药", "desc": "Keytruda抗癌药全球销冠"},
    "US.BMY": {"name": "百时美施贵宝", "sector": "医药", "desc": "肿瘤+免疫药物，Cardoxan管线推进中"},
    "US.AMGN": {"name": "安进", "sector": "医药/生物", "desc": "老牌生物制药，骨健康+肿瘤管线"},
    "US.GILD": {"name": "吉利德", "sector": "医药", "desc": "抗病毒药物龙头，HIV+新冠管线"},
    "US.HON": {"name": "霍尼韦尔", "sector": "工业/航空", "desc": "多元化工业集团，航空+自动化+建筑"},
    "US.CAT": {"name": "卡特彼勒", "sector": "工程机械", "desc": "全球最大工程机械制造商"},
    "US.FCX": {"name": "自由港", "sector": "采矿/铜", "desc": "全球最大铜矿商，新能源需求受益"},
    "US.NEM": {"name": "纽蒙特", "sector": "黄金开采", "desc": "全球最大黄金生产商"},
    "US.CP": {"name": "加拿大太平洋铁路", "sector": "交通运输", "desc": "北美货运铁路，工业命脉"},
    "US.XOM": {"name": "埃克森美孚", "sector": "能源", "desc": "全球最大综合石油公司"},
    "US.COP": {"name": "菲利普斯66", "sector": "能源/炼油", "desc": "大型炼油+上游一体化"},
    "US.OXY": {"name": "西方石油", "sector": "能源", "desc": "页岩油龙头，巴菲特重仓"},
    "US.BA": {"name": "波音", "sector": "航空航天", "desc": "商用飞机双寡头之一，质量整改中"},
    "US.DE": {"name": "德事隆", "sector": "工业/航空", "desc": "公务机+直升机+无人机综合集团"},

    # ═══════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════

}
def get_stock_info(code: str) -> dict:
    """查询股票信息，返回 {name, sector, desc}，找不到返回空dict"""
    info = STOCK_INFO.get(code, {})
    if info:
        return info
    # 尝试不带前缀的匹配（如 NVDA -> US.NVDA）
    parts = code.split(".")
    if len(parts) == 2:
        market, ticker = parts
        alt = f"{market}.{ticker}"
        return STOCK_INFO.get(alt, {})
    return {}
