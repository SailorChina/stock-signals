# -*- coding: utf-8 -*-
from __future__ import annotations
import logging, urllib.request, time
from dataclasses import dataclass
from typing import Dict, List, Optional
logger = logging.getLogger('tech-signal-skill')
SECTOR_ETFS = [('XLK','Technology','Tech'),('VGT','Technology Vanguard','Tech'),('QQQ','Nasdaq 100','Tech'),('TQQQ','Nasdaq 100 Leveraged','Tech'),('SMH','Semiconductors','Semi'),('SOXX','Semiconductors PHLX','Semi'),('IBB','Biotechnology','Biotech'),('XBI','Biotech SPDR','Biotech'),('VHT','Healthcare','Healthcare'),('XLV','Health Care','Healthcare'),('XLE','Energy','Energy'),('XOP','Oil and Gas E and P','Energy'),('XME','Materials SPDR','Materials'),('XLF','Financial','Financial'),('XLY','Consumer Discretionary','Consumer'),('XLP','Consumer Staples','Consumer'),('XLU','Utilities','Utilities'),('ARKK','Innovation','Innovation'),('UNG','Natural Gas','Gas'),('SPY','S P 500','SPY'),('IWM','Russell 2000','IWM')]
_STOCK_SECTOR_MAP: Dict[str,str] = {
'US.AAPL':'Tech','US.MSFT':'Tech','US.GOOG':'Tech','US.AMZN':'Tech',
'US.META':'Tech','US.NVDA':'Semi','US.AVGO':'Semi','US.AMD':'Semi',
'US.INTC':'Semi','US.QCOM':'Semi','US.MU':'Semi','US.NXPI':'Semi',
'US.AMAT':'Semi','US.LRCX':'Semi','US.ASML':'Semi','US.TXN':'Semi',
'US.NOW':'Tech','US.CRM':'Tech','US.ADBE':'Tech','US.PANW':'Tech',
'US.PLTR':'Tech','US.SNPS':'Tech','US.CDNS':'Tech','US.MCHP':'Tech',
'US.CSCO':'Tech','US.ORCL':'Tech',
'US.JNJ':'Healthcare','US.PFE':'Healthcare','US.UNH':'Healthcare',
'US.LLY':'Healthcare','US.ABBV':'Healthcare','US.MRK':'Healthcare',
'US.BMY':'Healthcare','US.AMGN':'Healthcare','US.GILD':'Healthcare',
'US.BIIB':'Biotech','US.BMRN':'Biotech','US.CELG':'Biotech',
'US.CERN':'Biotech','US.INCY':'Biotech','US.IRVN':'Biotech',
'US.MRVI':'Biotech','US.NBIX':'Biotech','US.SGMO':'Biotech',
'US.SRPT':'Biotech','US.VRTX':'Biotech','US.ISRG':'Biotech',
'US.HOLX':'Biotech','US.DXCM':'Biotech','US.ZBRA':'Biotech',
'US.VTRS':'Biotech','US.ILMN':'Biotech','US.MRNA':'Biotech',
'US.NVAX':'Biotech','US.BNTX':'Biotech','US.SRNE':'Biotech',
'US.SRRK':'Biotech','US.KPTI':'Biotech','US.ACAD':'Biotech',
'US.CRSP':'Biotech','US.EDIT':'Biotech','US.BEAM':'Biotech',
'US.NTLA':'Biotech','US.VERV':'Biotech','US.ALGN':'Healthcare',
'US.BAX':'Healthcare','US.MOH':'Healthcare','US.UHS':'Healthcare',
'US.HCAT':'Healthcare','US.SYK':'Healthcare','US.BSX':'Healthcare',
'US.TMO':'Healthcare','US.DHR':'Healthcare','US.ABT':'Healthcare',
'US.JPM':'Financial','US.BAC':'Financial','US.WFC':'Financial',
'US.C':'Financial','US.GS':'Financial','US.MS':'Financial',
'US.AXP':'Financial','US.V':'Financial','US.MA':'Financial',
'US.PYPL':'Financial','US.BK':'Financial','US.PNC':'Financial',
'US.USB':'Financial','US.TFC':'Financial','US.COF':'Financial',
'US.BLK':'Financial','US.SCHW':'Financial','US.SPGI':'Financial',
'US.MCO':'Financial','US.AON':'Financial','US.AJG':'Financial',
'US.TRV':'Financial','US.HIG':'Financial','US.ALL':'Financial',
'US.AIG':'Financial','US.PGR':'Financial','US.CINF':'Financial',
'US.L':'Financial','US.MMC':'Financial','US.WTW':'Financial',
'US.STT':'Financial','US.NTRS':'Financial','US.CBOE':'Financial',
'US.ICE':'Financial','US.GPN':'Financial','US.FIS':'Financial',
'US.FISV':'Financial',
'US.XOM':'Energy','US.COP':'Energy','US.OXY':'Energy',
'US.DVN':'Energy','US.EOG':'Energy','US.PXD':'Energy',
'US.MPC':'Energy','US.VLO':'Energy','US.TSO':'Energy',
'US.CTRA':'Energy','US.HES':'Energy','US.FANG':'Energy',
'US.MRO':'Energy','US.APA':'Energy','US.SWN':'Energy',
'US.CNP':'Energy','US.ET':'Energy','US.LNG':'Energy',
'US.MPLX':'Energy','US.WMB':'Energy','US.OKE':'Energy',
'US.EQT':'Energy','US.PARR':'Energy','US.HAL':'Energy',
'US.FTI':'Energy','US.NOV':'Energy','US.BKR':'Energy',
'US.RIG':'Energy','US.SLB':'Energy','US.PSX':'Energy',
'US.NBL':'Energy','US.LPL':'Energy','US.MTDR':'Energy',
'US.WPX':'Energy','US.RPTX':'Energy','US.GEL':'Energy',
'US.NBR':'Energy','US.PRI':'Energy','US.RRC':'Energy','US.TH':'Energy',
'US.FCX':'Materials','US.NEM':'Materials','US.CP':'Materials',
'US.LIN':'Materials','US.DD':'Materials','US.NUE':'Materials',
'US.STLD':'Materials','US.CLF':'Materials','US.CVV':'Materials',
'US.RS':'Materials','US.PKG':'Materials','US.VMC':'Materials',
'US.ML':'Materials','US.AA':'Materials','US.X':'Materials',
'US.WPM':'Materials','US.AEM':'Materials','US.AU':'Materials',
'US.GOLD':'Materials','US.FNV':'Materials','US.HL':'Materials',
'US.CDE':'Materials','US.AG':'Materials','US.MAG':'Materials',
'US.SAND':'Materials','US.PAAS':'Materials','US.EXK':'Materials',
'US.HON':'Industrial','US.CAT':'Industrial','US.BA':'Industrial',
'US.DE':'Industrial','US.UNP':'Industrial','US.UPS':'Industrial',
'US.LMT':'Industrial','US.NOC':'Industrial','US.GD':'Industrial',
'US.ETN':'Industrial','US.PHI':'Industrial','US.ROK':'Industrial',
'US.JEC':'Industrial','US.JBHT':'Industrial','US.ODFL':'Industrial',
'US.CHRW':'Industrial','US.XPO':'Industrial','US.KNX':'Industrial',
'US.APD':'Industrial','US.EMR':'Industrial','US.RTX':'Industrial',
'US.BHI':'Industrial','US.CMC':'Industrial','US.MLM':'Industrial',
'US.SWK':'Industrial','US.HPQ':'Industrial',
'US.MCD':'Consumer','US.NKE':'Consumer','US.TGT':'Consumer',
'US.WMT':'Consumer','US.COST':'Consumer','US.HD':'Consumer',
'US.LOW':'Consumer','US.TJX':'Consumer','US.BKNG':'Consumer',
'US.LULU':'Consumer','US.SBUX':'Consumer','US.DIS':'Consumer',
'US.NFLX':'Consumer','US.CMCSA':'Consumer','US.PARA':'Consumer',
'US.WBD':'Consumer','US.YUM':'Consumer','US.QSR':'Consumer',
'US.CMG':'Consumer','US.MDLZ':'Consumer','US.HSY':'Consumer',
'US.CL':'Consumer','US.UL':'Consumer','US.GIS':'Consumer',
'US.KHC':'Consumer','US.K':'Consumer','US.MO':'Consumer',
'US.PM':'Consumer','US.BTI':'Consumer','US.CPB':'Consumer',
'US.CAG':'Consumer','US.PEP':'Consumer','US.KO':'Consumer',
'US.CLX':'Consumer','US.KMB':'Consumer','US.ADM':'Consumer',
'US.BG':'Consumer','US.TSN':'Consumer',
'US.TSLA':'Auto','US.RIVN':'Auto','US.LCID':'Auto',
'US.NIO':'Auto','US.XPEV':'Auto','US.LI':'Auto',
'US.FSR':'Auto','US.GOEV':'Auto','US.RIDE':'Auto','US.WKHS':'Auto',
'US.DASH':'Transport','US.UBER':'Transport','US.LYFT':'Transport',
'US.ABNB':'Consumer','US.EXPE':'Consumer','US.TCOM':'Consumer',
'US.DAL':'Transport','US.AAL':'Transport','US.UAL':'Transport',
'US.LUV':'Transport','US.JBLU':'Transport','US.HA':'Transport',
'US.SAVE':'Transport','US.MESA':'Transport','US.AIR':'Transport',
'US.FRO':'Transport','US.EURN':'Transport','US.TORM':'Transport',
'US.INSW':'Transport','US.STNG':'Transport','US.NMM':'Transport',
'US.SBLK':'Transport',
'US.XLU':'Utilities','US.UNG':'Gas',
'US.BLNK':'Energy','US.CHPT':'Energy','US.EVGO':'Energy',
'US.SLP':'Industrial','US.FHN':'Financial','US.RF':'Financial',
}




@dataclass
class SectorRank:
    ticker: str
    en_name: str
    cn_name: str
    price: float
    chg_1d: float
    chg_5d: float
    chg_20d: float
    chg_60d: float
    heat_score: float

def _fetch_sina_quotes(ticker_list):
    """通过Sina API获取实时ETF报价"""
    results = {}
    batch_size = 50
    for i in range(0, len(ticker_list), batch_size):
        batch = ticker_list[i:i + batch_size]
        tickers = ','.join([f"gb_{t.lower()}" for t in batch])
        url = f"http://hq.sinajs.cn/list={tickers}"
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "http://finance.sina.com.cn/",
            })
            resp = urllib.request.urlopen(req, timeout=10)
            data = resp.read().decode("gbk", errors="replace")
            for line in data.strip().split(chr(10)):
                if "hq_str_gb_" not in line:
                    continue
                parts = line.split('=')
                if len(parts) < 2:
                    continue
                tkr = parts[0].replace("var hq_str_gb_", "").strip().upper()
                vals = parts[1].split(",")
                if len(vals) < 11:
                    continue
                try:
                    price = float(vals[1])
                    prev_close = float(vals[8]) if vals[8] else 0
                    chg = (price - prev_close) / prev_close * 100 if prev_close > 0 else 0
                    results[tkr] = {"price": price, "chg_1d": chg}
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"  Sina sector quotes batch failed: {e}")
        time.sleep(0.1)
    return results


def _compute_heat_scores(ticker_list, sina_quotes):
    try:
        import akshare as ak
    except ImportError:
        logger.error('akshare not installed, sector analysis unavailable')
        return []
    results = []
    for ticker, en_name, cn_name in SECTOR_ETFS:
        if ticker not in ticker_list:
            continue
        sina = sina_quotes.get(ticker, {})
        price = sina.get('price', 0)
        chg_1d = sina.get('chg_1d', 0)
        try:
            df = ak.stock_us_daily(symbol=ticker, adjust='qfq')
            if df is not None and len(df) > 60:
                close = df['close'].iloc[-1]
                if price == 0:
                    price = close
                chg_5d = (close - df['close'].iloc[-6]) / df['close'].iloc[-6] * 100
                chg_20d = (close - df['close'].iloc[-21]) / df['close'].iloc[-21] * 100
                chg_60d = (close - df['close'].iloc[-61]) / df['close'].iloc[-61] * 100
            elif df is not None and len(df) > 5:
                close = df['close'].iloc[-1]
                if price == 0:
                    price = close
                chg_5d = (close - df['close'].iloc[-6]) / df['close'].iloc[-6] * 100 if len(df) > 5 else 0
                chg_20d = chg_60d = 0
            else:
                chg_5d = chg_20d = chg_60d = 0
                if price == 0:
                    price = 0
        except Exception as e:
            logger.warning(f'  Failed to get {ticker} historical data: {e}')
            chg_5d = chg_20d = chg_60d = 0
            if price == 0:
                price = 0
        heat_score = chg_1d * 0.15 + chg_5d * 0.25 + chg_20d * 0.30 + chg_60d * 0.30
        results.append(SectorRank(
            ticker=ticker, en_name=en_name, cn_name=cn_name,
            price=price, chg_1d=chg_1d, chg_5d=chg_5d,
            chg_20d=chg_20d, chg_60d=chg_60d, heat_score=round(heat_score, 2),
        ))
    return results

def get_sector_ranking():
    tickers = [t for t, _, _ in SECTOR_ETFS]
    logger.info(f'  Fetching {len(tickers)} sector ETFs...')
    sina_quotes = _fetch_sina_quotes(tickers)
    ranks = _compute_heat_scores(tickers, sina_quotes)
    ranks.sort(key=lambda x: x.heat_score, reverse=True)
    logger.info(f'  Sector ranking done: {len(ranks)} sectors')
    return ranks


def get_stock_sector(code):
    return _STOCK_SECTOR_MAP.get(code)


def get_sector_bonus(code, sector_ranking):
    sector = get_stock_sector(code)
    if not sector:
        return 1.0
    # Map sector name to representative ETFs
    sector_to_etfs = {
        'Tech': ('XLK', 'VGT', 'QQQ'),
        'Semi': ('SMH', 'SOXX'),
        'Biotech': ('IBB', 'XBI'),
        'Healthcare': ('VHT', 'XLV'),
        'Energy': ('XLE', 'XOP'),
        'Materials': ('XME',),
        'Financial': ('XLF',),
        'Consumer': ('XLY', 'XLP'),
        'Utilities': ('XLU',),
        'Industrial': ('XLI',),
        'Auto': ('TSLA',),
        'Gas': ('UNG',),
    }
    etf_keys = sector_to_etfs.get(sector, ())
    if not etf_keys:
        return 1.0
    sector_etfs = [r for r in sector_ranking if r.ticker in etf_keys]
    if not sector_etfs:
        return 1.0
    avg_heat = sum(r.heat_score for r in sector_etfs) / len(sector_etfs)
    if avg_heat > 5:
        return 1.10
    elif avg_heat > 2:
        return 1.05
    elif avg_heat < -5:
        return 0.95
    elif avg_heat < -2:
        return 0.98
    return 1.0


def get_sector_ranking_for_display(sector_ranking):
    return [
        {
            'ticker': r.ticker, 'en_name': r.en_name, 'cn_name': r.cn_name,
            'price': r.price, 'chg_1d': r.chg_1d, 'chg_5d': r.chg_5d,
            'chg_20d': r.chg_20d, 'chg_60d': r.chg_60d,
            'heat_score': r.heat_score,
        }
        for r in sector_ranking
    ]
