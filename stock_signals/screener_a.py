# -*- coding: utf-8 -*-
"""A股专属筛选器"""
from __future__ import annotations
import logging, time, json
from dataclasses import dataclass, field
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("stock-signals")

@dataclass
class AScanResult:
    code: str; score: float; rating: str
    alignment: str = "none"; trend_phase: str = "unknown"
    entry: float = 0.0; stop_loss: float = 0.0; target_1: float = 0.0; target_2: float = 0.0
    risk_reward: float = 0.0; position_pct: float = 0.0; last_close: float = 0.0
    reasons: List[str] = field(default_factory=list)
    holding_period: str = ""; trade_plan: Optional[dict] = None
    rating_cn: str = ""; trend_phase_cn: str = ""; alignment_cn: str = ""; operable: str = ""

def get_a_trade_plan(ind, entry):
    atr = getattr(ind, 'atr_14', 1.5)
    stop = entry - 1.5 * atr if atr > 0 else entry * 0.95
    target_1 = max(entry * 1.08, entry + atr * 3) if atr > 0 else entry * 1.08
    target_2 = entry * 1.15
    risk = entry - stop; reward = target_1 - entry
    rr = reward / risk if risk > 0 else 0
    pos_pct = min(3.0, (risk / entry * 100) * 0.5) if risk > 0 else 1.0
    return {"entry_zone": round(entry, 2), "stop_loss": round(stop, 2), "target_1": round(target_1, 2), "target_2": round(target_2, 2), "risk_reward": round(rr, 2), "position_pct": round(pos_pct, 1)}

def compute_a_holding_period(ind, entry, target_1, stop, alignment, trend_phase):
    if entry <= 0 or ind.atr_14 <= 0: return "未知"
    risk = entry - stop if entry > stop else ind.atr_14 * 1.5
    reward = target_1 - entry if target_1 > entry else ind.atr_14 * 2
    rr = reward / risk if risk > 0 else 0
    trend_strength = 3 if ind.ma5 > ind.ma10 > ind.ma20 else (2 if ind.ma5 > ind.ma10 else (1 if ind.ma5 > ind.ma20 else 0))
    atr_pct = ind.atr_14 / entry * 100 if entry > 0 else 5
    vol_adj = min(2, max(-2, (10 - atr_pct)))
    j = getattr(ind, 'kdj_j', 50)
    kdj_adj = 1 if 30 < j < 70 else (2 if j < 20 else (-1 if j > 80 else 0))
    phase_map = {"early_rally": 1, "rally": 2, "accumulation": 0, "distribution": -1, "decline": -2, "unknown": 0}
    align_map = {"aligned": 1, "mixed": 0, "strong_up": 2, "none": -1}
    score = rr * 1.5 + trend_strength * 1.5 + vol_adj + kdj_adj + phase_map.get(trend_phase, 0) + align_map.get(alignment, 0)
    if score >= 9: return "波段(5-10天)"
    elif score >= 6: return "短线(3-5天)"
    elif score >= 3: return "超短(1-3天)"
    elif score >= 0: return "日内(1天)"
    else: return "观望"

def _analyze_one_a(code, delay=0.1):
    try:
        from .indicators import fetch_kline
        df = fetch_kline(code, "1d", num=120); time.sleep(delay)
        if df is None or df.empty or len(df) < 60: return None
        from .indicators_a import IndicatorsA
        ind = IndicatorsA(); ind.update(df, code)
        from .scoring_a import compute_a_rating
        rating_result = compute_a_rating(ind)
        score = rating_result["score"]; rating = rating_result["rating"]
        # P0: 涨跌停保护
        if getattr(ind, 'is_limit_up', False): return None
        if getattr(ind, 'is_limit_down', False): return None
        # P0: KDJ超买过滤
        if getattr(ind, 'kdj_j', 50) > 100: return None
        if ind.day_change_pct > 5: return None
        if ind.rsi_14 > 75: return None
        if ind.vol_ratio < 0.8: return None
        # P0: 改进入场价逻辑
        if ind.last_close < ind.ma5 * 1.02:
            entry = ind.ma5
        elif ind.last_close < ind.ma10 * 1.05:
            entry = ind.ma10
        else:
            entry = ind.last_close * 0.995
        # P0: 偏离MA20过大则跳过
        if getattr(ind, 'price_vs_ma20', 0) > 15: return None
        tp = get_a_trade_plan(ind, entry)
        if tp["risk_reward"] < 2.5: return None
        reasons = []
        if ind.ma5 > ind.ma10: reasons.append("MA5>MA10")
        if ind.macd_dif > ind.macd_dea: reasons.append("MACD金叉")
        if ind.vol_ratio > 1.5: reasons.append("放量")
        j_val = getattr(ind, 'kdj_j', 50)
        if j_val < 20: reasons.append(f"KDJ超卖(J={j_val:.0f})")
        elif j_val > 80: reasons.append(f"KDJ超买(J={j_val:.0f})")
        if getattr(ind, 'is_limit_up', False): reasons.append("涨停(不可追)")
        reasons.append(f"RR={tp['risk_reward']:.1f}:1")
        # P1: BOLL位置
        bb_pos = getattr(ind, "price_vs_bb", "middle")
        if bb_pos == "lower_half": reasons.append("布林下轨支撑")
        elif bb_pos == "above": reasons.append("突破上轨")
        # P1: 板块联动
        chg5 = getattr(ind, "change_pct_5d", 0)
        if 3 < chg5 < 8: reasons.append(f"5日涨{chg5:.1f}%板块联动")
        elif chg5 > 10: reasons.append(f"5日涨{chg5:.1f}%警惕追高")
        from ._sr import compute_trend_phase
        try: phase = compute_trend_phase(df, ind)
        except: phase = "unknown"
        alignment = "aligned" if score >= 60 else "mixed"
        # P1: 可操作标记
        j_val = getattr(ind, "kdj_j", 50)
        limit_up = getattr(ind, "is_limit_up", False)
        limit_down = getattr(ind, "is_limit_down", False)
        bb_pos = getattr(ind, "price_vs_bb", "middle")
        chg5 = getattr(ind, "change_pct_5d", 0)
        if limit_up:
            operable = "涨停不可入"
        elif limit_down:
            operable = "跌停有风险"
        elif j_val > 100:
            operable = "KDJ严重超买"
        elif j_val < 20 and chg5 < -5:
            operable = "KDJ超卖+超跌反弹"
        elif chg5 > 15:
            operable = "5日涨幅过大"
        elif bb_pos == "above" and j_val > 80:
            operable = "突破上轨+超买"
        else:
            operable = "可操作"
        holding_period = compute_a_holding_period(ind, tp["entry_zone"], tp["target_1"], tp["stop_loss"], alignment, phase)
        cn_r = {"Buy": "买入", "Overweight": "偏多", "Hold": "观望", "Underweight": "偏空", "Sell": "卖出"}.get(rating, rating)
        cn_p = {"accumulation": "吸筹阶段", "early_rally": "上涨早期", "rally": "上涨阶段", "distribution": "派发阶段", "decline": "下跌阶段", "unknown": "未知"}.get(phase, phase)
        cn_a = {"strong_up": "强共振看多", "aligned": "共振看多", "mixed": "分歧", "none": "无"}.get(alignment, alignment)
        return AScanResult(code=code, score=score, rating=rating, alignment=alignment, trend_phase=phase, entry=tp["entry_zone"], stop_loss=tp["stop_loss"], target_1=tp["target_1"], target_2=tp["target_2"], risk_reward=tp["risk_reward"], position_pct=tp["position_pct"], last_close=ind.last_close, reasons=reasons, holding_period=holding_period, trade_plan=tp, rating_cn=cn_r, trend_phase_cn=cn_p, alignment_cn=cn_a, operable=operable)
    except Exception as e:
        logger.warning(f"分析{code}失败: {e}"); return None

def scan_a(markets=None, config=None, output_json=False, output_file=""): 
    from .screener import ScanConfig 
    from .hot_fetcher import fetch_a_hot_stocks 
    if config is None: config = ScanConfig() 
    codes = fetch_a_hot_stocks(300) 
    logger.info(f"A股预选: {len(codes)}只") 
    picks, watchlist, total_analyzed = [], [], 0 
    batch_size = 30 
    for i in range(0, len(codes), batch_size): 
        batch = codes[i:i+batch_size] 
        batch_results = [] 
        with ThreadPoolExecutor(max_workers=4) as executor: 
            futures = {executor.submit(_analyze_one_a, code, delay=0.05): code for code in batch} 
            for future in as_completed(futures): 
                try: 
                    r = future.result(); total_analyzed += 1 
                    if r is not None: batch_results.append(r) 
                except Exception as e: 
                    logger.warning(f"并行分析失败: {futures[future]} - {e}") 
        for result in batch_results: 
            if result.score >= 55: picks.append(result) 
            elif result.score >= 45: watchlist.append(result) 
        if len(picks) > config.max_per_market * 3: picks = picks[:config.max_per_market * 3] 
        logger.info(f"A股: 已处理 {min(i+batch_size, len(codes))}/{len(codes)}") 
    picks.sort(key=lambda x: x.score, reverse=True) 
    watchlist.sort(key=lambda x: x.score, reverse=True) 
    final_picks = picks[:config.max_per_market]; final_watch = watchlist[:config.max_per_market] 
    summary = {"scan_time": time.strftime("%Y-%m-%d %H:%M:%S"), "total_analyzed": total_analyzed, "total_picks": len(final_picks), "total_watchlist": len(final_watch), "markets_scanned": ["A"]} 
    output = {"date": time.strftime("%Y-%m-%d"), "summary": summary, "picks": {"A": [{"code": p.code, "score": p.score, "rating": p.rating, "rating_cn": p.rating_cn, "trend_phase": p.trend_phase, "trend_phase_cn": p.trend_phase_cn, "alignment": p.alignment, "alignment_cn": p.alignment_cn, "entry": p.entry, "stop_loss": p.stop_loss, "target_1": p.target_1, "target_2": p.target_2, "risk_reward": p.risk_reward, "position_pct": p.position_pct, "reasons": list(p.reasons) if p.reasons else [], "holding_period": p.holding_period, "last_close": p.last_close} for p in final_picks]}, "watchlist": {"A": [{"code": w.code, "score": w.score, "rating": w.rating, "rating_cn": w.rating_cn, "trend_phase": w.trend_phase, "trend_phase_cn": w.trend_phase_cn, "alignment": w.alignment, "alignment_cn": w.alignment_cn, "entry": w.entry, "stop_loss": w.stop_loss, "target_1": w.target_1, "target_2": w.target_2, "risk_reward": w.risk_reward, "position_pct": w.position_pct, "reasons": list(w.reasons) if w.reasons else [], "holding_period": w.holding_period, "last_close": w.last_close} for w in final_watch]}} 
    if output_json or output_file: 
        json_output = json.dumps(output, ensure_ascii=False, indent=2) 
        if output_json: print(json_output) 
        if output_file: 
            with open(output_file, "w", encoding="utf-8") as f: f.write(json_output) 
    logger.info(f"A股扫描完成: 分析{total_analyzed}只, 推荐{len(final_picks)}只, 观察{len(final_watch)}只") 
    return output 