import sys,time,json,logging
logging.basicConfig(level=logging.WARNING)
sys.path.insert(0,r'D:\\Backup\\Documents\\ChatGPT\\AI\\stock-signals')
from stock_signals.indicators import fetch_kline,compute_indicators
from stock_signals.scoring import compute_rating
from stock_signals._sr import compute_support_resistance,generate_trade_plan,compute_trend_phase
from stock_signals._vcp import detect_vcp
RATING_CN={'Buy':'买入','Overweight':'偏多','Hold':'观望','Underweight':'偏空','Sell':'卖出'}
PHASE_CN={'accumulation':'吸筹阶段','early_rally':'上涨早期','rally':'上涨阶段','distribution':'派发阶段','decline':'下跌阶段','unknown':'未知'}
codes=["US.SGMO","US.INTC","US.NVDA","US.AAL","US.NKE","US.AAPL","US.RIG","US.HL","US.MU","US.GRAB","US.PFE","US.NFLX","US.TSLA","US.AMZN","US.META","US.PLTR","US.RIVN","US.AMD","US.CDE","US.NIO","US.ORCL","US.AVGO","US.NOW","US.MSFT","US.WMT","US.JBLU","US.GOOGL","US.DVN","US.XOM","US.UBER"]
results=[]
t=time.time()
for code in codes:
    try:
        df=fetch_kline(code,'1d',num=300)
        if df is None or df.empty or len(df)<60: continue
        ind=compute_indicators(df,code,'1d')
        rating=compute_rating(ind)
        score=rating['score'];r_name=rating['rating']
        sr=compute_support_resistance(df)
        vcp_res=detect_vcp(df,lookback=100)
        try: phase=compute_trend_phase(df,ind)
        except: phase='unknown'
        tp=generate_trade_plan(ind,sr,phase,vcp_res)
        dist=getattr(ind,'distance_from_52w_high',0)
        if dist<8: continue
        rr=getattr(tp,'risk_reward',0) if tp else 0
        if rr<2.0: continue
        if getattr(ind,'rsi_14',50)>75: continue
        if getattr(ind,'td_turn','')=='sell_turn': continue
        results.append({'code':code,'rating':r_name,'rating_cn':RATING_CN.get(r_name,r_name),'score':score,'risk_reward':round(rr,2),'trend_phase':phase,'trend_phase_cn':PHASE_CN.get(phase,phase),'entry':tp.entry_zone if tp else 0,'stop_loss':tp.stop_loss if tp else 0,'target_1':tp.target_1 if tp else 0,'target_2':tp.target_2 if tp else 0,'last_close':ind.last_close})
    except: pass
results.sort(key=lambda x:x['score'],reverse=True)
out={'date':'2026-08-19','summary':{'scan_time':time.strftime('%Y-%m-%d %H:%M:%S'),'total_analyzed':len(codes),'total_picks':len(results)},'picks':{'US':results}}
with open(r'D:\Backup\Documents\ChatGPT\AI\stock-signals\scan_result.json','w',encoding='utf-8') as f:
    json.dump(out,f,indent=2,ensure_ascii=False)
print(f'Done: {len(codes)} scanned {len(results)} picks')
for i,r in enumerate(results[:5],1):
    print(f"  {i}. {r['code']} {r['rating_cn']}({r['rating']}) score={r['score']} RR={r['risk_reward']}:1 {r['trend_phase_cn']}({r['trend_phase']}) price={r['last_close']:.2f} entry={r['entry']:.2f} SL={r['stop_loss']:.2f}")
