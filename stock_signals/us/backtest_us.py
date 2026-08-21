# -*- coding: utf-8 -*-
"""
美股策略回测 - 独立策略
单仓位管理，不做空
"""
import sys, io, os, json, time, pickle
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
from stock_signals.us.scoring_us import compute_rating_us
from stock_signals.us.screener_us import US_POOL, _compute_trade_plan
from stock_signals.hot_fetcher import fetch_us_hot_stocks

# 动态热门股池：静态池 + 今日热门TOP300
_hot_codes = fetch_us_hot_stocks(top_n=300)
if _hot_codes and len(_hot_codes) >= 10:
    _us_hot_set = set(c.upper().replace('US.', '') for c in _hot_codes)
    _us_static_set = set(c.replace('US.', '') for c in US_POOL)
    _merged = list(dict.fromkeys(_hot_codes + [c for c in US_POOL if c.replace('US.', '') not in _us_static_set]))
    US_POOL = _merged
    print(f"US Pool: {len(US_POOL)} stocks (static: {len(US_POOL) - len(_hot_codes)} + hot: {len(_hot_codes)})")
else:
    print(f"US Pool: {len(US_POOL)} stocks (hot fetch returned {len(_hot_codes)}, using static pool)")


# ========== 回测参数 ==========
START = "2018-01-01"
END = "2026-08-15"
INITIAL_CAPITAL = 1_000_000
POS_PCT = 0.20        # 单仓位占总资产比例
MAX_HOLD = 10         # 最大持仓天数
MIN_SCORE = 50        # 最低评分门槛
MIN_RR = 1.5          # 最低盈亏比
STOP_ATR_MULT = 1.8   # ATR止损倍数 (optimized)
FEE_RATE = 0.001      # 交易费率(佣金+滑点)

print("US Stock Backtest: " + START + " ~ " + END)
print("Pool: " + str(len(US_POOL)) + " stocks")
print("=" * 60)

# 加载缓存
cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "us_data_cache.pkl")
if os.path.exists(cache_path):
    with open(cache_path, "rb") as f:
        raw_cache = pickle.load(f)
    print("Loaded cache: " + str(len(raw_cache)) + " stocks")
else:
    print("ERROR: us_data_cache.pkl not found")
    sys.exit(1)

# 构建数据框架
all_dates = set()
stock_dfs = {}
for code_sym, records in raw_cache.items():
    df = pd.DataFrame(records)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"]).copy()
    df["date_str"] = df["time"].dt.strftime("%Y-%m-%d")
    # Deduplicate: keep last occurrence of each date
    df = df.drop_duplicates(subset=["date_str"], keep="last")
    for date_str in df["date_str"]: all_dates.add(date_str)
    stock_dfs[code_sym] = df.set_index("date_str")
US_POOL = list(stock_dfs.keys())
valid_dates = sorted(d for d in all_dates if START <= d <= END)
print("Trading dates: " + str(len(valid_dates)) + " (" + valid_dates[0] + " ~ " + valid_dates[-1] + ")")

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
    dist_low = (close_a - low_252) / low_252 * 100
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
        ind.macd_hist = float(dif[j]-dea[j])
        ind.rsi_14 = float(rsi14[j])
        ind.atr_14 = float(atr14[j])
        ind.distance_from_52w_high = float(dist_high[j])
        ind.distance_from_52w_low = float(dist_low[j])
        ind.vol_ratio = float(vol_ratio[j])
        ind.obv_trend = "flat"
        ind.td_turn = "none"
        ind.td_buy_setup = False
        ind.td_sell_setup = False
        ind.adx = 25.0
        ind.plus_di = 25.0
        ind.minus_di = 25.0
        ind.boll_width = 0
        ind.vol_regime = "normal"
        ind.gap_type = "none"
        ind.gap_pct = 0
        ind.kdj_k = 50
        ind.kdj_d = 50
        ind.kdj_j = 50
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
print("  " + str(len(ind_cache)) + " indicators in " + str(round(time.time()-t0,1)) + "s")
print("=" * 60)
print("Running backtest...")

# ========== 回测主循环 ==========
bt_start = time.time()
trades = []
equity = INITIAL_CAPITAL
eq_history = []
pos = None
days_in_pos = 0
stocks_ok = len(stock_dfs)
trade_count = 0

for date in valid_dates:
    # --- 持仓检查：止损/止盈/超时 ---
    if pos is not None:
        days_in_pos += 1
        code_sym = pos["code"]
        df = stock_dfs.get(code_sym)
        if df is None or date not in df.index:
            exit_p = pos["entry"]
            pnl = -pos["entry"]*pos["shares"]*FEE_RATE - pos["entry"]*pos["shares"]*FEE_RATE
            trades.append({"code": code_sym, "entry": pos["entry"], "exit": exit_p,
                          "pnl": round(pnl, 2), "pnl_pct": round(-FEE_RATE*100, 2),
                          "days": days_in_pos, "reason": "no_data",
                          "score": pos["score"], "rr": pos["rr"]})
            equity = equity + exit_p*pos["shares"]*(1 - FEE_RATE)
            pos = None
            days_in_pos = 0
            eq_history.append({"date": date, "eq": equity})
            continue
        row = df.loc[date]
        cur_close = float(row["close"])
        cur_high = float(row["high"])
        cur_low = float(row["low"])
        # 止损
        if cur_low <= pos["stop"]:
            exit_p = pos["stop"]
            pnl = (exit_p - pos["entry"]) * pos["shares"]
            pnl -= (pos["entry"]*pos["shares"] + exit_p*pos["shares"]) * FEE_RATE
            trades.append({"code": code_sym, "entry": pos["entry"], "exit": exit_p,
                          "pnl": round(pnl, 2), "pnl_pct": round(pnl/(pos["entry"]*pos["shares"])*100, 2),
                          "days": days_in_pos, "reason": "stop",
                          "score": pos["score"], "rr": pos["rr"]})
            equity = equity + exit_p*pos["shares"]*(1 - FEE_RATE)
            pos = None
            days_in_pos = 0
            eq_history.append({"date": date, "eq": equity})
            continue
        # 止盈
        if cur_high >= pos["target"]:
            exit_p = pos["target"]
            pnl = (exit_p - pos["entry"]) * pos["shares"]
            pnl -= (pos["entry"]*pos["shares"] + exit_p*pos["shares"]) * FEE_RATE
            trades.append({"code": code_sym, "entry": pos["entry"], "exit": exit_p,
                          "pnl": round(pnl, 2), "pnl_pct": round(pnl/(pos["entry"]*pos["shares"])*100, 2),
                          "days": days_in_pos, "reason": "target",
                          "score": pos["score"], "rr": pos["rr"]})
            equity = equity + exit_p*pos["shares"]*(1 - FEE_RATE)
            pos = None
            days_in_pos = 0
            eq_history.append({"date": date, "eq": equity})
            continue
        # 超时
        if days_in_pos >= MAX_HOLD:
            exit_p = cur_close
            pnl = (exit_p - pos["entry"]) * pos["shares"]
            pnl -= (pos["entry"]*pos["shares"] + exit_p*pos["shares"]) * FEE_RATE
            trades.append({"code": code_sym, "entry": pos["entry"], "exit": exit_p,
                          "pnl": round(pnl, 2), "pnl_pct": round(pnl/(pos["entry"]*pos["shares"])*100, 2),
                          "days": days_in_pos, "reason": "timeout",
                          "score": pos["score"], "rr": pos["rr"]})
            equity = equity + exit_p*pos["shares"]*(1 - FEE_RATE)
            pos = None
            days_in_pos = 0
            eq_history.append({"date": date, "eq": equity})
            continue
        # 持有中
        eq_history.append({"date": date, "eq": equity})
        continue

    # --- 无持仓：扫描全池找最佳入场 ---
    best_pick = None
    best_score = 0
    for code_sym in stock_dfs:
        ind = ind_cache.get((code_sym, date))
        if ind is None or ind.last_close <= 0: continue
        score = compute_rating_us(ind)["score"]
        if score < MIN_SCORE: continue
        if ind.rsi_14 > 75: continue
        ma_gap = ind.ma5 / ind.ma20 - 1 if ind.ma20 > 0 else 0
        if ma_gap > 10: continue
        if ind.td_turn == "sell_turn": continue
        tp = _compute_trade_plan(ind, STOP_ATR_MULT)
        if tp["risk_reward"] < MIN_RR: continue
        df = stock_dfs.get(code_sym)
        idx = df.index.get_loc(date) if date in df.index else -1
        entry = float(df.iloc[idx+1]["open"]) if 0 <= idx < len(df)-1 else float(df.loc[date]["close"])
        if entry <= 0: continue
        if score > best_score:
            best_score = score
            best_pick = {"code": code_sym, "score": score, "entry": entry,
                        "stop": tp["stop_loss"], "target": tp["target_1"], "rr": tp["risk_reward"]}

    # 入场（修复：即使shares<=0也追加eq_history）
    if best_pick is not None:
        entry = best_pick["entry"]
        shares = int(equity * POS_PCT / entry / 100) * 100
        if shares <= 0: shares = int(equity * POS_PCT / entry)
        if shares > 0:
            cost = entry * shares
            equity -= cost + cost * FEE_RATE
            pos = {"code": best_pick["code"], "entry": entry, "shares": shares,
                   "stop": best_pick["stop"], "target": best_pick["target"],
                   "score": best_pick["score"], "rr": best_pick["rr"]}
            days_in_pos = 0
            trade_count += 1
            if trade_count <= 30:
                print("  BUY @" + str(round(entry,2)) + " " + best_pick["code"] +
                      " score=" + str(round(best_pick["score"],1)) +
                      " RR=" + str(round(best_pick["rr"],1)) + ":1")
    # 修复关键：无论是否入场，都追加eq_history
    eq_history.append({"date": date, "eq": equity})

# 结束未平仓
if pos is not None and len(valid_dates) > 0:
    last_date = valid_dates[-1]
    df = stock_dfs.get(pos["code"])
    lp = float(df.loc[last_date]["close"]) if df is not None and last_date in df.index else pos["entry"]
    pnl = (lp - pos["entry"]) * pos["shares"]
    exit_p = lp
    pnl -= (pos["entry"]*pos["shares"] + exit_p*pos["shares"]) * FEE_RATE
    trades.append({"code": pos["code"], "entry": pos["entry"], "exit": lp,
                  "pnl": round(pnl, 2), "pnl_pct": round(pnl/(pos["entry"]*pos["shares"])*100, 2),
                  "days": days_in_pos, "reason": "end",
                  "score": pos["score"], "rr": pos["rr"]})
    equity = equity + lp*pos["shares"]*(1 - FEE_RATE)

# ========== 报告 ==========
print("=" * 60)
print("  US Stock Backtest Report (" + START + " ~ " + END + ")")
print("=" * 60)
if not trades:
    print("  No trades executed!")
else:
    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    total_pnl = sum(t["pnl"] for t in trades)
    final_eq = INITIAL_CAPITAL + total_pnl
    total_return = (final_eq - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    eqs = [e["eq"] for e in eq_history]
    peak = 0
    mdd = 0
    for eq in eqs:
        if eq > peak: peak = eq
        dd = (peak - eq) / peak * 100
        if dd > mdd: mdd = dd
    rets = [(eqs[i]-eqs[i-1])/eqs[i-1] for i in range(1,len(eqs)) if eqs[i-1] > 0]
    sharpe = (np.mean(rets)/np.std(rets)*np.sqrt(252)) if rets and np.std(rets) > 0 else 0
    print("  Stocks: " + str(len(US_POOL)) + " (with data: " + str(stocks_ok) + ")")
    print("  Capital: $" + str(INITIAL_CAPITAL) + " -> $" + str(round(final_eq,0)))
    print("  Trades: " + str(len(trades)) + "  Win:" + str(len(wins)) + "  Lose:" + str(len(losses)))
    print("  Win rate: " + str(round(len(wins)/len(trades)*100, 1)) + "%")
    if wins: print("  Avg win: " + str(round(np.mean([t["pnl_pct"] for t in wins]), 2)) + "%")
    if losses: print("  Avg loss: " + str(round(np.mean([t["pnl_pct"] for t in losses]), 2)) + "%")
    print("  Avg hold: " + str(round(np.mean([t["days"] for t in trades]), 1)) + " days")
    print("  Total return: " + str(round(total_return, 2)) + "%")
    print("  Max drawdown: " + str(round(mdd, 2)) + "%")
    print("  Sharpe ratio: " + str(round(sharpe, 2)))
    print("=" * 60)
    st = sorted(trades, key=lambda x: x["pnl"], reverse=True)
    print(""); print("Top 5 profits:")
    for t in st[:5]:
        print("  " + t["code"] + " @ " + str(round(t["entry"],2)) + " -> " +
              str(round(t["exit"],2)) + " PnL $" + str(round(t["pnl"],0)) +
              " (" + str(round(t["pnl_pct"],1)) + "%) " + str(t["days"]) + "d [" + t["reason"] + "]")
    print(""); print("Top 5 losses:")
    for t in st[-5:]:
        print("  " + t["code"] + " @ " + str(round(t["entry"],2)) + " -> " +
              str(round(t["exit"],2)) + " PnL -$" + str(round(abs(t["pnl"]),0)) +
              " (" + str(round(t["pnl_pct"],1)) + "%) " + str(t["days"]) + "d [" + t["reason"] + "]")
    result = {"period": START + "~" + END, "stocks": len(stock_dfs),
              "stocks_with_data": stocks_ok, "trades": trades,
              "total_return": round(total_return, 2),
              "win_rate": round(len(wins)/len(trades)*100, 1),
              "max_drawdown": round(mdd, 2), "sharpe": round(sharpe, 2),
              "total_trades": len(trades), "win_trades": len(wins),
              "lose_trades": len(losses),
              "avg_hold": round(np.mean([t["days"] for t in trades]), 1),
              "avg_win": round(np.mean([t["pnl_pct"] for t in wins]), 2) if wins else 0,
              "avg_loss": round(np.mean([t["pnl_pct"] for t in losses]), 2) if losses else 0,
              "final_equity": round(final_eq, 0), "eq_history": eq_history,
              "params": {"min_score": MIN_SCORE, "min_rr": MIN_RR,
                         "stop_loss_atr": STOP_ATR_MULT, "max_hold": MAX_HOLD,
                         "pos_pct": POS_PCT, "fee_rate": FEE_RATE}}
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_result_us.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(""); print("Saved to backtest_result_us.json")
print("Eq history entries: " + str(len(eq_history)))
print("Backtest completed in " + str(round(time.time()-bt_start, 1)) + "s")
