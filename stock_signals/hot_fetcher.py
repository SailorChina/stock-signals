# -*- coding: utf-8 -*-
"""热门股获取模块 - 多 API fallback 方案"""
from __future__ import annotations
import logging, time, os, urllib.request, json
from typing import List
import pandas as pd
logger = logging.getLogger("stock-signals")
for _k in list(os.environ.keys()):
    if 'proxy' in _k.lower(): os.environ.pop(_k, None)
os.environ.setdefault('no_proxy', '*')
os.environ.setdefault('NO_PROXY', '*')

def _parse_a_code(raw):
    if len(raw) < 3: return ""
    prefix = raw[:2].upper(); num = raw[2:]
    if prefix in ("SH", "SZ", "BJ"): return f"{prefix}.{num}"
    return ""

def fetch_a_hot_stocks(top_n=300):
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
    # Try 东方财富热股榜 as fallback
    try:
        t2 = time.time()
        url2 = "http://qt.gtimg.cn/q/sh600519"  # Test if API works
        req2 = urllib.request.Request(url2, headers={"User-Agent":"Mozilla/5.0"})
        resp2 = urllib.request.urlopen(req2, timeout=5)
        # Get hot stocks from eastmoney
        url3 = "http://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=200&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14,f2,f3"
        req3 = urllib.request.Request(url3, headers={"User-Agent":"Mozilla/5.0","Referer":"http://quote.eastmoney.com/"})
        resp3 = urllib.request.urlopen(req3, timeout=8)
        data3 = json.loads(resp3.read().decode('utf-8'))
        if data3.get('data') and data3['data'].get('diff'):
            for item in data3['data']['diff'][:top_n]:
                code_str = item.get('f12','')
                parsed = _parse_a_code(code_str)
                if parsed and parsed not in codes:
                    codes.append(parsed)
            logger.info(f"  A股热门(东财): {len(codes)}只 ({time.time()-t2:.1f}s)")
            return codes
    except Exception as e3:
        logger.warning(f"  东财热股获取失败: {e3}")
    logger.warning("  A股热门获取失败,使用静态池")
    return codes

def fetch_hk_hot_stocks(top_n=300):
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
        for line in data.strip().split(chr(10)):
            if '~' in line and 'none_match' not in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    vals = parts[-1].strip('"').split('~')
                    if len(vals) > 2 and vals[2]:
                        valid.append(f"HK.{vals[2].zfill(5)}")
        codes = valid[:top_n]
        logger.info(f"  港股热门(Tencent验证): {len(codes)}只 ({time.time()-t:.1f}s)")
        if codes: return codes
    except Exception as e:
        logger.warning(f"  腾讯港股验证失败: {e}")
    logger.info("  港股: 使用静态池")
    return static_pool[:top_n]

# 美股静态池 300+只，覆盖SP500主流标的
_US_STATIC_POOL = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOG","GOOGL","TSLA","AVGO","CSCO",
    "ORCL","AMD","INTC","QCOM","MU","NXPI","AMAT","LRCX","ASML","TXN",
    "NOW","CRM","ADBE","PANW","PLTR","SNPS","CDNS","MCHP","IDXX",
    "ZBRA","HOLX","DXCM","ILMN","MRNA","VTRS","REGN","BIIB","BMRN",
    "CELG","CERN","VRTX","ISRG","ZTS","AMGN","GILD","LLY","ABBV","JNJ",
    "MRK","PFE","BMY","UNH","HUM","CVS","SYK","BSX","TMO","DHR","ABT",
    "JPM","BAC","WFC","C","GS","MS","BK","PNC","USB","TFC","COF","AXP",
    "BRK-B","V","MA","PYPL","SQ","FIS","FISV","GPN","STT","NTRS",
    "CBOE","ICE","MCO","SPGI","AON","AJG","TRV","HIG","ALL","AIG",
    "PGR","CINF","L","BLK","SCHW","MMC","WTW","SLP","FHN","SWK","RF",
    "WMT","COST","TGT","HD","LOW","TJX","BKNG","MCD","NKE","LULU",
    "SBUX","DIS","NFLX","CMCSA","PARA","WBD","YUM","QSR","CMG","DPW",
    "DCH","MDLZ","HSY","CL","UL","GIS","KHC","K","SYZ","HST",
    "ANN","AHT","DRH","RHP","PEAK","VTR","PSA","ESS","AMT","EXR",
    "HON","CAT","DE","BA","GE","UNP","UPS","LMT","NOC","GD","ETN",
    "PHI","ROK","IID","JEC","JBHT","ODFL","CHRW","XPO","KNX","APD",
    "BKR","EMR","RTX","FCX","NEM","COP","XOM","OXY","DVN","EOG",
    "PXD","MPC","VLO","TSO","CTRA","WLL","PR","RRC","THO","EQT",
    "LIN","DD","NUE","STLD","CLF","CVV","RS","PKG","VMC","ML","AA","X","SM",
    "JNJ","PFE","UNH","LLY","ABBV","MRK","BMY","AMGN","GILD","BIIB",
    "BMRN","ILMN","MRNA","VTRS","REGN","VRTX","ISRG","ZTS","AMGN","SYK",
    "BSX","TMO","DHR","ABT","BAX","DXCM","HOLX","IDXX","ZBRA","ALGN",
    "MOH","UHS","HCAT","ALGN","INCY","MRVI","SRPT","NBIX","SGMO","BNTX",
    "NVAX","SRNE","SRRK","KPTI","ACAD","CRSP","EDIT","BEAM","NTLA","VERV",
    "MO","PM","BTI","MDLZ","HSY","GIS","K","CPB","CAG","KHC",
    "PEP","KO","MCD","YUM","QSR","CMG","SBUX","MDLZ","HSY","CLX",
    "KMB","ADM","BG","TSN","HPQ","DE","CAT","FCX","NEM","AA",
    "NUE","STLD","CLF","X","CMC","PKG","VMC","MLM","BHI","RIG",
    "SLB","OXY","DVN","EOG","PXD","MPC","VLO","PSX","HES","FANG",
    "COP","XOM","OXY","DVN","EOG","PXD","MPC","VLO","PSX","HES",
    "FANG","MRO","APA","RRC","SWN","CNX","EQT","AR","GPOR","PARR",
    "HAL","BKR","FTI","NOV","SLB","OII","CHX","PII","RIG","VAL",
    "HP","NE","CTRA","OVV","PR","MUR","WTI","SWN","RNG","AR",
    "CHK","RRC","PRT","MGY","CRK","LGP","FANG","CNQ","TCM","NLP",
    "BTO","WEP","MEG","TGNA","CVCO","GMS","MGC","NAT","TGP","PAA",
    "WMB","EQT","NBL","AR","LPL","MTDR","SWN","RRC","CTRA","WPX",
    "RPTX","GPOR","GEL","NBR","SM","CNP","ET","LNG","MPLX","PAGP",
    "WES","OKE","TECK","FCX","WPM","AEM","KGE","GLDG","AU","NEM",
    "GOLD","FNV","WPM","AU","KGE","GLDG","HL","CDE","AG","MAG",
    "SAND","PAAS","EXK","SLRC","EPRT","REI","CDZI","MAG","SAND","PAAS",
    "GLAD","CARS","FRO","EURN","TORM","INSW","STNG","FAL","NAVG","NMM",
    "SBLK","CMCGK","DHT","GRIM","LPG","TGP","PAGP","GATX","JJSF","SAIA",
    "EXPD","CHRW","XPO","LSTR","KNX","ODFL","JBHT","ARCB","WERN","SAIC",
    "UI","HTLD","IMII","CRUK","MRTN","PCAR","SANM","WAB","GT","ALK",
    "LUV","DAL","AAL","UAL","SKYW","JBLU","HA","SAVE","MESA","AIR",
    "MAR","HLT","IHG","H", "WH","RHP","PEAK","DRH","APLE","XHR","RIVN",
    "LCID","NIO","XPEV","LI","FSR","GOEV","RIDE","WKHS","BLNK","CHPT",
    "EVGO","SPCC","HTHP","FIVN","GRAB","DASH","UBER","LYFT","ABNB","BKNG",
    "EXPE","TCOM","MMYT","TRIP","EXPD","CHRW","XPO","LSTR","KNX","ODFL",
    "JBHT","ARCB","WERN","SAIC","UI","HTLD","IMII","CRUK","MRTN","PCAR",
    "SANM","WAB","GT","ALK","LUV","DAL","AAL","UAL","SKYW","JBLU",
    "HA","SAVE","MESA","AIR","MAR","HLT","IHG","H","WH","RHP",
    "PEAK","DRH","APLE","XHR","RIVN","LCID","NIO","XPEV","LI","FSR",
]

def _fetch_us_quotes_from_sina(ticker_list, batch_size=80):
    """通过Sina GB接口批量获取美股实时报价"""
    all_stocks = []
    for i in range(0, len(ticker_list), batch_size):
        batch = ticker_list[i:i+batch_size]
        tickers = ','.join([f'gb_{t.lower()}' for t in batch])
        url = f'http://hq.sinajs.cn/list={tickers}'
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer':'http://finance.sina.com.cn/'
            })
            resp = urllib.request.urlopen(req, timeout=10)
            data = resp.read().decode('gbk', errors='replace')
            for line in data.strip().split(chr(10)):
                if 'hq_str_gb_' not in line:
                    continue
                parts = line.split('="')
                if len(parts) < 2:
                    continue
                ticker = parts[0].replace('var hq_str_gb_','').strip().upper()
                vals = parts[1].split(',')
                if len(vals) < 11:
                    continue
                try:
                    price = float(vals[1])
                    vol = int(float(vals[10])) if vals[10] else 0
                    if price > 0 and vol > 0:
                        all_stocks.append({'ticker': ticker, 'price': price, 'volume': vol})
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"  Sina批次请求失败: {e}")
    return all_stocks

def fetch_us_hot_stocks(top_n=300):
    """美股热门股 - 基于Sina实时报价按成交量排序"""
    pool = list(dict.fromkeys(_US_STATIC_POOL))
    logger.info(f"  美股静态池: {len(pool)}只")
    try:
        t = time.time()
        quotes = _fetch_us_quotes_from_sina(pool)
        if quotes:
            quotes.sort(key=lambda x: x['volume'], reverse=True)
            codes = ['US.' + s['ticker'] for s in quotes[:top_n]]
            logger.info(f"  美股热门(成交量排序): {len(codes)}只 ({time.time()-t:.1f}s)")
            return codes
        else:
            logger.warning("  Sina报价无有效数据")
    except Exception as e:
        logger.warning(f"  美股热门获取失败: {e}")
    logger.info("  美股: 使用静态池")
    return ['US.' + t for t in pool[:top_n]]

def fetch_hot_stocks(market, top_n=300):
    """统一入口"""
    if market == "A": return fetch_a_hot_stocks(top_n)
    elif market == "HK": return fetch_hk_hot_stocks(top_n)
    elif market == "US": return fetch_us_hot_stocks(top_n)
    return []


def fetch_longhubang(top_n=50):
    try:
        import akshare as ak
        t = time.time()
        df = ak.stock_lhb_detail_em(start_date=time.strftime("%Y%m%d"), end_date=time.strftime("%Y%m%d"))
        if df is not None and not df.empty:
            result = {}
            for _, row in df.head(top_n).iterrows():
                code = str(row.get("code", ""))
                if len(code) == 6:
                    prefix = "SH" if code.startswith(("6", "9")) else "SZ"
                    result[f"{prefix}.{code}"] = {"name": str(row.get("name", "")), "net_amount": float(row.get("net", 0)) if pd.notna(row.get("net")) else 0}
            logger.info(f"  龙虎榜: {len(result)}只 ({time.time()-t:.1f}s)")
            return result
        return {}
    except Exception as e:
        logger.warning(f"  龙虎榜获取失败: {e}")
        return {}

def fetch_sector_heat(top_n=20):
    try:
        import akshare as ak
        t = time.time()
        df = ak.stock_board_industry_name_em()
        if df is not None and not df.empty:
            result = {}
            for _, row in df.head(top_n).iterrows():
                name = str(row.get("sector_name", ""))
                change = float(row.get("change_pct", 0)) if pd.notna(row.get("change_pct")) else 0
                result[name] = {"change": change, "rank": len(result) + 1}
            logger.info(f"  板块热度: {len(result)}个 ({time.time()-t:.1f}s)")
            return result
        return {}
    except Exception as e:
        logger.warning(f"  板块热度获取失败: {e}")
        return {}

def fetch_north_flow():
    try:
        import akshare as ak
        t = time.time()
        df = ak.stock_hsgt_hist_em(symbol="north")
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return {"date": str(latest.get("date", "")), "north_flow": float(latest.get("north_flow", 0)) if pd.notna(latest.get("north_flow")) else 0}
        return {}
    except Exception as e:
        logger.warning(f"  北向资金获取失败: {e}")
        return {}
