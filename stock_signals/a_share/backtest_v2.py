# -*- coding: utf-8 -*-
import sys, os, json, urllib.request
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

START="2024-01-01"; END="2026-08-15"
CAPITAL=1000000; POS_PCT=0.20; MAX_HOLD=5
THRESHOLD=46; MIN_RR=1.5

def fetch(code):
    try:
        sym=code.split(".")[-1]; mk=code.split(".")[0].lower()
        url=f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={mk}{sym}&scale=240&ma=no&datalen=800"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Referer":"http://finance.sina.com.cn/"})
        df=pd.DataFrame(json.loads(urllib.request.urlopen(req,timeout=15).read().decode()))
        df["time_key"]=pd.to_datetime(df["day"])
        for c in ("open","high","low","close","volume"): df[c]=pd.to_numeric(df[c],errors="coerce")
        return df.dropna(subset=["close"])
    except: return None

def ema(d,p):
    if len(d)<p: return d
    m=2/(p+1); e=np.empty_like(d); e[0]=d[0]
    for i in range(1,len(d)): e[i]=(d[i]-d[i-1])*m+e[i-1]
    return e

def calc_ind(df,idx):
    if idx<60: return None
    c=df["close"].values[:idx+1].astype(float)
    h=df["high"].values[:idx+1].astype(float)
    l=df["low"].values[:idx+1].astype(float)
    v=df["volume"].values[:idx+1].astype(float)
    if len(c)<60: return None
    ma5=np.mean(c[-5:]); ma10=np.mean(c[-10:]); ma20=np.mean(c[-20:])
    close=c[-1]; chg=(c[-1]-c[-2])/c[-2]*100 if len(c)>1 else 0
    if len(c)>=15:
        d=np.diff(c); g=np.where(d>0,d,0); ls=np.where(d<0,-d,0)
        rs=np.mean(g[-14:])/np.mean(ls[-14:]) if np.mean(ls[-14:])>0 else 100
        rsi=100-(100/(1+rs))
    else: rsi=50
    if len(c)>=35:
        e12=ema(c,12); e26=ema(c,26); dif=e12-e26
        difv=float(dif[-1]); dea=float(ema(np.array(dif),9)[-1])
    else: difv=0; dea=0
    vr=float(v[-1]/np.mean(v[-6:-1])) if np.mean(v[-6:-1])>0 else 1.0
    pv20=(close-ma20)/ma20*100 if ma20>0 else 0
    if len(c)>=9:
        rsv=[]
        for i in range(8,idx+1):
            w=c[i-8:i+1]; wh=h[i-8:i+1]; wl=l[i-8:i+1]
            h9=float(np.max(wh)); l9=float(np.min(wl))
            rsv.append(50.0 if h9==l9 else (c[i]-l9)/(h9-l9)*100)
        if rsv:
            kvs=[rsv[0]]
            for i in range(1,len(rsv)): kvs.append(kvs[-1]*2/3+rsv[i]*1/3)
            dvs=[kvs[0]]
            for i in range(1,len(kvs)): dvs.append(dvs[-1]*2/3+kvs[i]*1/3)
            jv=3*kvs[-1]-2*dvs[-1]
        else: jv=50
    else: jv=50
    if len(h)>=15:
        tv=[max(h[i]-l[i],abs(h[i]-c[i-1]) if i>-len(c) else 0,abs(l[i]-c[i-1]) if i>-len(c) else 0) for i in range(-14,0)]
        atr=float(np.mean(tv))
    else: atr=1.5
    chg5=(c[-1]-c[-6])/c[-6]*100 if len(c)>=6 else 0
    return {"ma5":ma5,"ma10":ma10,"ma20":ma20,"close":close,"chg":chg,"rsi":rsi,
        "difv":difv,"dea":dea,"vr":vr,"pv20":pv20,"jv":jv,"atr":atr,"chg5":chg5,
        "lub":chg>=9.5,"ldb":chg<=-9.5,"tr":vr*3}

def calc_score(ind):
    s=0
    t=50
    if ind["ma5"]>ind["ma10"]>ind["ma20"]: t+=15
    elif ind["ma5"]>ind["ma10"]: t+=8
    if ind["close"]>ind["ma20"]: t+=10
    if 50<ind["rsi"]<65: t+=10
    elif ind["rsi"]>=65: t-=5
    s+=t*0.09
    m=50
    if ind["difv"]>ind["dea"]: m+=15
    if ind["chg"]>0: m+=10
    if ind["rsi"]>50: m+=5
    s+=m*0.09
    v=50
    if ind["vr"]>1.5: v+=20
    elif ind["vr"]>1.2: v+=10
    elif ind["vr"]<0.8: v-=10
    s+=v*0.09
    tr=50; tr2=ind.get("tr",3)
    if 3<tr2<8: tr+=20
    elif 8<=tr2<15: tr+=10
    elif tr2>=15: tr-=10
    s+=tr*0.06
    k=50; j=ind.get("jv",50)
    if j>100: k-=20
    elif j>80: k-=10
    elif j<0: k+=20
    elif j<20: k+=10
    s+=k*0.10
    lp=50
    if ind["lub"]: lp-=30
    elif ind["ldb"]: lp-=20
    if ind["chg5"]>15: lp-=15
    elif ind["chg5"]>10: lp-=8
    elif ind["chg5"]<-10: lp+=5
    s+=lp*0.10
    sec=50
    if 3<ind["chg5"]<10 and ind["pv20"]<10: sec+=15
    elif ind["chg5"]<0 and ind["pv20"]<-5: sec+=5
    elif ind["chg5"]>15: sec-=10
    s+=sec*0.10
    s+=50*0.17
    return round(s,1)

codes=["SH.600519","SH.601318","SH.600036","SH.601398","SH.601288",
       "SH.600028","SH.600030","SH.600048","SH.601166","SH.601328",
       "SH.600276","SH.600887","SH.601012","SH.601088","SH.601857",
       "SH.600585","SH.600089","SH.600309","SH.600900","SH.600009",
       "SZ.000858","SZ.000333","SZ.002594","SZ.002415","SZ.002475",
       "SZ.000001","SZ.000002","SZ.000063","SZ.002460","SZ.002714",
       "SZ.300750","SZ.300059","SZ.300015","SZ.300124","SZ.300122",
       "SH.688981","SH.688012","SH.688396","SH.688111","SH.688256",
       "SH.603288","SH.603259","SH.603899","SH.600104","SH.603160"]

print(f"回测开始: {len(codes)}只, {START}~{END}")
trades=[]; equity=CAPITAL; eq_hist=[]; pos=None; tdays=0; stocks_ok=0
for code in codes:
    df=fetch(code)
    if df is None or len(df)<120: continue
    stocks_ok+=1
    print(f"  {code}: {len(df)}条")
    for i in range(60,len(df)-1):
        cur_date=str(df.iloc[i]["time_key"])[:10]
        if cur_date<START or cur_date>END: continue
        cur_close=float(df.iloc[i]["close"]); cur_high=float(df.iloc[i]["high"]); cur_low=float(df.iloc[i]["low"])
        ind=calc_ind(df,i)
        if ind is None: continue
        sc=calc_score(ind)
        if pos is not None:
            tdays+=1
            if cur_low<=pos["stop"]:
                pnl=(pos["stop"]-pos["entry"])*pos["shares"]
                trades.append({"code":pos["code"],"entry":pos["entry"],"exit":pos["stop"],"pnl":pnl,"pnl_pct":round(pnl/(pos["entry"]*pos["shares"])*100,2),"days":tdays,"reason":"止损"})
                equity+=pos["entry"]*pos["shares"]+pnl; pos=None; tdays=0; eq_hist.append({"date":cur_date,"eq":equity}); continue
            if cur_high>=pos["target"]:
                pnl=(pos["target"]-pos["entry"])*pos["shares"]
                trades.append({"code":pos["code"],"entry":pos["entry"],"exit":pos["target"],"pnl":pnl,"pnl_pct":round(pnl/(pos["entry"]*pos["shares"])*100,2),"days":tdays,"reason":"目标"})
                equity+=pos["entry"]*pos["shares"]+pnl; pos=None; tdays=0; eq_hist.append({"date":cur_date,"eq":equity}); continue
            if tdays>=MAX_HOLD:
                pnl=(cur_close-pos["entry"])*pos["shares"]
                trades.append({"code":pos["code"],"entry":pos["entry"],"exit":cur_close,"pnl":pnl,"pnl_pct":round(pnl/(pos["entry"]*pos["shares"])*100,2),"days":tdays,"reason":"到期"})
                equity+=pos["entry"]*pos["shares"]+pnl; pos=None; tdays=0; eq_hist.append({"date":cur_date,"eq":equity}); continue
            eq_hist.append({"date":cur_date,"eq":equity}); continue
        if sc>=THRESHOLD and not ind["lub"] and not ind["ldb"]:
            if ind["jv"]>100: continue
            if ind["chg"]>5: continue
            if ind["rsi"]>75: continue
            if ind["vr"]<0.8: continue
            if ind["pv20"]>15: continue
            entry=float(df.iloc[i+1]["open"]) if i+1<len(df) else cur_close
            if entry<=0: continue
            atr=ind["atr"]; stop=entry-1.2*atr if atr>0 else entry*0.95
            target=max(entry*1.08,entry+atr*3) if atr>0 else entry*1.08
            risk=entry-stop; reward=target-entry; rr=reward/risk if risk>0 else 0
            if rr<MIN_RR: continue
            shares=int(equity*POS_PCT/entry/100)*100
            if shares<=0: continue
            pos={"code":code,"entry":entry,"shares":shares,"stop":stop,"target":target,"score":sc,"rr":rr}
            equity-=entry*shares; tdays=0
            print(f"    买入 @{entry:.2f} score={sc:.1f} RR={rr:.2f}")
        eq_hist.append({"date":cur_date,"eq":equity})
    if pos is not None:
        lp=float(df.iloc[-1]["close"]); pnl=(lp-pos["entry"])*pos["shares"]
        trades.append({"code":pos["code"],"entry":pos["entry"],"exit":lp,"pnl":pnl,"pnl_pct":round(pnl/(pos["entry"]*pos["shares"])*100,2),"days":tdays,"reason":"结束"})

if not trades:
    print("\n无交易!")
else:
    wins=[t for t in trades if t["pnl"]>0]; losses=[t for t in trades if t["pnl"]<=0]
    total_pnl=sum(t["pnl"] for t in trades); final_eq=CAPITAL+total_pnl
    tr=(final_eq-CAPITAL)/CAPITAL*100
    eqs=[e["eq"] for e in eq_hist]; peak=0; mdd=0
    for eq in eqs:
        if eq>peak: peak=eq
        dd=(peak-eq)/peak*100
        if dd>mdd: mdd=dd
    rets=[(eqs[i]-eqs[i-1])/eqs[i-1] for i in range(1,len(eqs)) if eqs[i-1]>0]
    sharpe=(np.mean(rets)/np.std(rets)*np.sqrt(252)) if rets and np.std(rets)>0 else 0
    print("\n"+"="*60)
    print(f"  A股策略回测报告 ({START}~{END})")
    print("="*60)
    print(f"  股票: {len(codes)}只 (有数据: {stocks_ok})")
    print(f"  资金: RMB{CAPITAL:,} -> ¥{final_eq:,.0f}")
    print(f"  交易: {len(trades)}次  盈:{len(wins)} 亏:{len(losses)}")
    print(f"  胜率: {len(wins)/len(trades)*100:.1f}%")
    print(f"  平均盈: {np.mean([t['pnl_pct'] for t in wins]):.2f}%  平均亏: {np.mean([t['pnl_pct'] for t in losses]):.2f}%")
    print(f"  平均持仓: {np.mean([t['days'] for t in trades]):.1f}天")
    print(f"  总收益: {tr:.2f}%")
    print(f"  最大回撤: {mdd:.2f}%")
    print(f"  夏普比率: {sharpe:.2f}")
    print("="*60)
    st=sorted(trades,key=lambda x: x["pnl"],reverse=True)
    print("\n盈利Top 5:")
    for t in st[:5]: print(f"  {t['code']} @ {t['entry']:.2f} -> {t['exit']:.2f} 盈{t['pnl']:.0f}({t['pnl_pct']:.1f}%) {t['days']}天 [{t['reason']}]")
    print("\n亏损Top 5:")
    for t in st[-5:]: print(f"  {t['code']} @ {t['entry']:.2f} -> {t['exit']:.2f} 亏{abs(t['pnl']):.0f}({t['pnl_pct']:.1f}%) {t['days']}天 [{t['reason']}]")
    with open("backtest_result.json","w",encoding="utf-8") as f:
        json.dump({"period":f"{START}~{END}","stocks":len(codes),"trades":trades,
            "total_return":round(tr,2),"win_rate":round(len(wins)/len(trades)*100,1),
            "max_drawdown":round(mdd,2),"sharpe":round(sharpe,2),
            "total_trades":len(trades),"win_trades":len(wins),"lose_trades":len(losses),
            "avg_hold":round(np.mean([t['days'] for t in trades]),1),
            "avg_win":round(np.mean([t['pnl_pct'] for t in wins]),2),
            "avg_loss":round(np.mean([t['pnl_pct'] for t in losses]),2),
            "final_equity":round(final_eq,0)},f,ensure_ascii=False,indent=2)
    print("\n已保存到 backtest_result.json")
