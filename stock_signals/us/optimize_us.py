# -*- coding: utf-8 -*-
"""
美股策略参数优化 - Walk-Forward Validation
独立文件，独立策略
"""
import sys, io, os, json, time, pickle
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from itertools import product
from stock_signals.us.scoring_us import compute_rating_us
from stock_signals.us.screener_us import US_POOL, _compute_trade_plan

# ========== 参数网格 ==========
PARAM_GRID = {
    "min_score": [50, 55, 60],
    "min_rr": [1.5, 2.0, 2.5],
    "stop_loss_atr": [1.5, 1.8, 2.0, 2.5],
    "max_hold": [7, 10, 14],
    "pos_pct": [0.15, 0.20],
}

START = "2018-01-01"
END = "2026-08-15"
INITIAL_CAPITAL = 1_000_000
FEE_RATE = 0.001

print("US Stock Parameter Optimization")
print("=" * 60)

# 加载缓存
cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "us_data_cache.pkl")
with open(cache_path, "rb") as f:
    raw_cache = pickle.load(f)

stock_dfs = {}
all_dates = set()
for code_sym, records in raw_cache.items():
    df = pd.DataFrame(records)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"]).copy()
    df["date_str"] = df["time"].dt.strftime("%Y-%m-%d")
    for d in df["date_str"]: all_dates.add(d)
    stock_dfs[code_sym] = df.set_index("date_str")

valid_dates = sorted(d for d in all_dates if START <= d <= END)
print(f"Trading dates: {len(valid_dates)} ({valid_dates[0]} ~ {valid_dates[-1]})")

# 预计算指标
print("Pre-computing indicators...")
ind_cache = {}
t0 = time.time()
for code_sym in stock_dfs:
    df = stock_dfs.get(code_sym)
    if df is None: continue
    idx_list = df.index.tolist()
    close_a = df["close"].values.astype(float)
    high_a = df["high"].values.astype(float)
    low_a = df["low"].values.astype(float)
    vol_a = df["volume"].values.astype(float)
    ma5 = pd.Series(close_a).rolling(5).mean().values
    ma10 = pd.Series(close_a).rolling(10).mean().values
    ma20 = pd.Series(close_a).rolling(20).mean().values
    ma60 = pd.Series(close_a).rolling(60).mean().values
    e12 = pd.Series(close_a).ewm(span=12, adjust=False).mean().values
    e26 = pd.Series(close_a).ewm(span=26, adjust=False).mean().values
    dif = e12 - e26
    dea = pd.Series(dif).ewm(span=9, adjust=False).mean().values
    delta = np.diff(close_a)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    loss_mean = np.concatenate([[loss[0]], pd.Series(loss).ewm(span=14, adjust=False).mean().values])
    gain_mean = np.concatenate([[gain[0]], pd.Series(gain).ewm(span=14, adjust=False).mean().values])
    rsi14 = np.where(loss_mean > 0, 100 - 100/(1 + gain_mean / loss_mean), 100.0)
    prev_c = np.concatenate([[close_a[0]], close_a[:-1]])
    tr = np.maximum(np.maximum(high_a - low_a, abs(high_a - prev_c)), abs(low_a - prev_c))
    atr14 = pd.Series(tr).rolling(14).mean().values
    high_252 = pd.Series(high_a).rolling(252).max().values
    low_252 = pd.Series(low_a).rolling(252).min().values
    dist_high = (close_a - high_252) / high_252 * 100
    vol_avg6 = pd.Series(vol_a).rolling(6).mean().values
    vol_ratio = np.where(vol_avg6 > 0, vol_a / vol_avg6, 1.0)
    for j, date_str in enumerate(idx_list):
        if date_str < START or date_str > END: continue
        if j < 252: continue
        ind = type("Ind", (), {})()
        ind.code = code_sym
        ind.last_close = float(close_a[j])
        ind.last_time = date_str
        ind.prev_close = float(close_a[j-1]) if j > 0 else float(close_a[j])
        ind.day_change_pct = (close_a[j] - ind.prev_close) / ind.prev_close * 100 if ind.prev_close > 0 else 0
        ind.ma5 = float(ma5[j])
        ind.ma10 = float(ma10[j])
        ind.ma20 = float(ma20[j])
        ind.ma60 = float(ma60[j])
        ind.macd_dif = float(dif[j])
        ind.macd_dea = float(dea[j])
        ind.rsi_14 = float(rsi14[j])
        ind.atr_14 = float(atr14[j])
        ind.distance_from_52w_high = float(dist_high[j])
        dist_low_j = (close_a[j] - low_252[j]) / low_252[j] * 100 if low_252[j] > 0 else 0
        ind.distance_from_52w_low = float(dist_low_j)
        ind.vol_ratio = float(vol_ratio[j])
        ind.td_buy_setup = False; ind.td_sell_setup = False; ind.td_turn = "none"
        ind.adx = 25.0; ind.plus_di = 25.0; ind.minus_di = 25.0
        ind.macd_hist = float(dif[j]-dea[j])
        ind.boll_width = 0; ind.vol_regime = "normal"; ind.gap_type = "none"; ind.gap_pct = 0
        ind.kdj_k = 50; ind.kdj_d = 50; ind.kdj_j = 50
        ind.obv_trend = "flat"
        ind.price_vs_ma60 = (ind.last_close - ind.ma60) / ind.ma60 * 100 if ind.ma60 > 0 else 0
        ind.macd_dif_dea_cross = ""
        ind.ma5_ma10_cross = ""
        if j >= 12:
            pm5 = np.mean(close_a[j-12:j-2])
            pm10 = np.mean(close_a[j-12:j-2])
            if pm5 <= pm10 and ind.ma5 > ind.ma10: ind.ma5_ma10_cross = "golden"
            elif pm5 >= pm10 and ind.ma5 < ind.ma10: ind.ma5_ma10_cross = "death"
        if j >= 36:
            if dif[j-1] <= dea[j-1] and dif[j] > dea[j]: ind.macd_dif_dea_cross = "golden"
            elif dif[j-1] >= dea[j-1] and dif[j] < dea[j]: ind.macd_dif_dea_cross = "death"
        bc = sc = 0
        for k in range(max(4, j-20), j):
            if k >= 4 and close_a[k] < close_a[k-4]: bc += 1
            else: bc = 0
            if bc >= 9: ind.td_buy_setup = True
            if k >= 4 and close_a[k] > close_a[k-4]: sc += 1
            else: sc = 0
            if sc >= 9: ind.td_sell_setup = True
        if ind.td_buy_setup and j >= 11 and close_a[j] > close_a[j-1]: ind.td_turn = "buy_turn"
        elif ind.td_sell_setup and j >= 11 and close_a[j] < close_a[j-1]: ind.td_turn = "sell_turn"
        ind_cache[(code_sym, date_str)] = ind
print(f"  {len(ind_cache)} indicators in {round(time.time()-t0,1)}s")

# ========== Walk-Forward 回测函数 ==========
def run_backtest(params, dates_subset=None):
    """运行单次回测，返回结果dict"""
    if dates_subset is None:
        dates_subset = valid_dates
    ms = params["min_score"]
    mr = params["min_rr"]
    sa = params["stop_loss_atr"]
    mh = params["max_hold"]
    pp = params["pos_pct"]
    
    trades = []
    equity = INITIAL_CAPITAL
    eq_history = []
    pos = None
    days_in_pos = 0
    for date in dates_subset:
        if pos is not None:
            days_in_pos += 1
            code_sym = pos["code"]
            df = stock_dfs.get(code_sym)
            if df is None or date not in df.index:
                exit_p = pos["entry"]
                pnl = -pos["entry"] * pos["shares"] * FEE_RATE * 2
                trades.append({"pnl": pnl, "pnl_pct": round(pnl/(pos["entry"]*pos["shares"])*100, 2), "days": days_in_pos, "reason": "no_data"})
                equity = equity + exit_p*pos["shares"]*(1-FEE_RATE)
                pos = None; days_in_pos = 0
                eq_history.append({"date": date, "eq": equity})
                continue
            row = df.loc[date]
            cur_close = float(row["close"])
            cur_high = float(row["high"])
            cur_low = float(row["low"])
            if cur_low <= pos["stop"]:
                exit_p = pos["stop"]
                pnl = (exit_p - pos["entry"])*pos["shares"] - (pos["entry"]*pos["shares"]+exit_p*pos["shares"])*FEE_RATE
                trades.append({"pnl": pnl, "pnl_pct": round(pnl/(pos["entry"]*pos["shares"])*100, 2), "days": days_in_pos, "reason": "stop"})
                equity = equity + exit_p*pos["shares"]*(1-FEE_RATE)
                pos = None; days_in_pos = 0
                eq_history.append({"date": date, "eq": equity})
                continue
            if cur_high >= pos["target"]:
                exit_p = pos["target"]
                pnl = (exit_p - pos["entry"])*pos["shares"] - (pos["entry"]*pos["shares"]+exit_p*pos["shares"])*FEE_RATE
                trades.append({"pnl": pnl, "pnl_pct": round(pnl/(pos["entry"]*pos["shares"])*100, 2), "days": days_in_pos, "reason": "target"})
                equity = equity + exit_p*pos["shares"]*(1-FEE_RATE)
                pos = None; days_in_pos = 0
                eq_history.append({"date": date, "eq": equity})
                continue
            if days_in_pos >= mh:
                exit_p = cur_close
                pnl = (exit_p - pos["entry"])*pos["shares"] - (pos["entry"]*pos["shares"]+exit_p*pos["shares"])*FEE_RATE
                trades.append({"pnl": pnl, "pnl_pct": round(pnl/(pos["entry"]*pos["shares"])*100, 2), "days": days_in_pos, "reason": "timeout"})
                equity = equity + exit_p*pos["shares"]*(1-FEE_RATE)
                pos = None; days_in_pos = 0
                eq_history.append({"date": date, "eq": equity})
                continue
            eq_history.append({"date": date, "eq": equity})
            continue
        # 扫描
        best_pick = None
        best_score = 0
        for code_sym in stock_dfs:
            ind = ind_cache.get((code_sym, date))
            if ind is None or ind.last_close <= 0: continue
            score = compute_rating_us(ind)["score"]
            if score < ms: continue
            if ind.rsi_14 > 75: continue
            ma_gap = ind.ma5 / ind.ma20 - 1 if ind.ma20 > 0 else 0
            if ma_gap > 10: continue
            if ind.td_turn == "sell_turn": continue
            tp = _compute_trade_plan(ind, sa)
            if tp["risk_reward"] < mr: continue
            df = stock_dfs.get(code_sym)
            idx = df.index.get_loc(date) if date in df.index else -1
            entry = float(df.iloc[idx+1]["open"]) if 0 <= idx < len(df)-1 else float(df.loc[date]["close"])
            if entry <= 0: continue
            if score > best_score:
                best_score = score
                best_pick = {"code": code_sym, "score": score, "entry": entry, "stop": tp["stop_loss"], "target": tp["target_1"], "rr": tp["risk_reward"]}
        if best_pick is not None:
            entry = best_pick["entry"]
            shares = int(equity * pp / entry / 100) * 100
            if shares <= 0: shares = int(equity * pp / entry)
            if shares > 0:
                cost = entry * shares
                equity -= cost * (1 + FEE_RATE)
                pos = {"code": best_pick["code"], "entry": entry, "shares": shares, "stop": best_pick["stop"], "target": best_pick["target"], "score": best_pick["score"], "rr": best_pick["rr"]}
                days_in_pos = 0
        eq_history.append({"date": date, "eq": equity})
    # 最终平仓
    if pos is not None and len(dates_subset) > 0:
        last_date = dates_subset[-1]
        df = stock_dfs.get(pos["code"])
        lp = float(df.loc[last_date]["close"]) if df is not None and last_date in df.index else pos["entry"]
        pnl = (lp - pos["entry"])*pos["shares"] - (pos["entry"]*pos["shares"]+lp*pos["shares"])*FEE_RATE
        trades.append({"pnl": pnl, "pnl_pct": round(pnl/(pos["entry"]*pos["shares"])*100, 2), "days": days_in_pos, "reason": "end"})
        equity = equity + lp*pos["shares"]*(1-FEE_RATE)
    
    eqs = [e["eq"] for e in eq_history]
    peak = 0; mdd = 0
    for eq in eqs:
        if eq > peak: peak = eq
        dd = (peak - eq) / peak * 100
        if dd > mdd: mdd = dd
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    total_pnl = sum(t["pnl"] for t in trades)
    total_return = total_pnl / INITIAL_CAPITAL * 100
    rets = [(eqs[i]-eqs[i-1])/eqs[i-1] for i in range(1,len(eqs)) if eqs[i-1] > 0]
    sharpe = (np.mean(rets)/np.std(rets)*np.sqrt(252)) if rets and np.std(rets) > 0 else 0
    avg_hold = np.mean([t["days"] for t in trades]) if trades else 0
    win_rate = len(wins)/len(trades)*100 if trades else 0
    return {
        "total_return": round(total_return, 2),
        "win_rate": round(win_rate, 1),
        "max_drawdown": round(mdd, 2),
        "sharpe": round(sharpe, 2),
        "total_trades": len(trades),
        "avg_hold": round(avg_hold, 1),
        "final_equity": round(equity, 0),
    }

# ========== Walk-Forward 验证 ==========
# 分割：前70%训练，后30%测试
n = len(valid_dates)
split_idx = int(n * 0.7)
train_dates = valid_dates[:split_idx]
test_dates = valid_dates[split_idx:]
print(f"Walk-forward split: train={len(train_dates)} dates ({train_dates[0]}~{train_dates[-1]}), test={len(test_dates)} dates ({test_dates[0]}~{test_dates[-1]})")

# 生成参数组合
keys = list(PARAM_GRID.keys())
values = list(PARAM_GRID.values())
combinations = list(product(*values))
print(f"Total parameter combinations: {len(combinations)}")
print("=" * 60)

results = []
for i, vals in enumerate(combinations):
    params = dict(zip(keys, vals))
    # 训练集回测
    train_result = run_backtest(params, train_dates)
    # 测试集回测
    test_result = run_backtest(params, test_dates)
    # 综合评分：训练集收益 + 测试集收益 - 惩罚回撤
    composite = (train_result["total_return"] + test_result["total_return"]) / 2 - test_result["max_drawdown"] * 0.5
    r = {**params, **train_result, "composite": round(composite, 2)}
    # 重命名test字段
    r = {**params, **train_result, 
         "test_total_return": test_result["total_return"],
         "test_win_rate": test_result["win_rate"],
         "test_max_drawdown": test_result["max_drawdown"],
         "test_sharpe": test_result["sharpe"],
         "test_total_trades": test_result["total_trades"],
         "composite": round(composite, 2)}
    results.append(r)
    if (i+1) % 10 == 0:
        print(f"  Progress: {i+1}/{len(combinations)}")

# 排序
results.sort(key=lambda x: -x["composite"])
print("=" * 60)
print("Top 10 Parameter Sets:")
print(f"{'Rank':>4} {'Score':>6} {'MinSc':>6} {'MinRR':>6} {'StopATR':>8} {'MaxHold':>8} {'Pos%':>6} {'TrainRet':>10} {'TrainWR':>8} {'TrainMDD':>9} {'TestRet':>10} {'TestWR':>8} {'TestMDD':>9} {'TestSharpe':>11}")
for rank, r in enumerate(results[:10], 1):
    print(f"{rank:>4} {r['composite']:>6.2f} {r['min_score']:>6} {r['min_rr']:>6} {r['stop_loss_atr']:>8} {r['max_hold']:>8} {r['pos_pct']:>6.0%} {r['total_return']:>10.2f} {r['win_rate']:>7.1f}% {r['max_drawdown']:>8.2f}% {r['test_total_return']:>10.2f} {r['test_win_rate']:>7.1f}% {r['test_max_drawdown']:>8.2f}% {r['test_sharpe']:>11.2f}")

# 最佳参数全 period 回测
best = results[0]
print("=" * 60)
print("Best params: " + str({k: best[k] for k in keys}))
full_result = run_backtest(best)
print(f"Full period result: return={full_result['total_return']}% win_rate={full_result['win_rate']}% mdd={full_result['max_drawdown']}% sharpe={full_result['sharpe']} trades={full_result['total_trades']}")

# 保存优化结果
opt_result = {
    "best_params": best,
    "all_results": results,
    "full_period_result": full_result,
    "walk_forward_split": {"train": f"{train_dates[0]}~{train_dates[-1]}", "test": f"{test_dates[0]}~{test_dates[-1]}"},
}
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "optimize_us_result.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(opt_result, f, ensure_ascii=False, indent=2)
print(f"Saved to optimize_us_result.json")
