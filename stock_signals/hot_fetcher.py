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

# US static pool (384 stocks)
# 美股静态池 (384只蓝筹) - 用于Sina API批量查询
_US_STATIC_POOL = [
    'AAPL', 'MSFT', 'NVDA', 'AMZN', 'META',
    'GOOG', 'GOOGL', 'TSLA', 'AVGO', 'CSCO',
    'ORCL', 'AMD', 'INTC', 'QCOM', 'MU',
    'NXPI', 'AMAT', 'LRCX', 'ASML', 'TXN',
    'NOW', 'CRM', 'ADBE', 'PANW', 'PLTR',
    'SNPS', 'CDNS', 'MCHP', 'IDXX', 'ZBRA',
    'HOLX', 'DXCM', 'ILMN', 'MRNA', 'VTRS',
    'REGN', 'BIIB', 'BMRN', 'CELG', 'CERN',
    'VRTX', 'ISRG', 'ZTS', 'AMGN', 'GILD',
    'LLY', 'ABBV', 'JNJ', 'MRK', 'PFE',
    'BMY', 'UNH', 'HUM', 'CVS', 'SYK',
    'BSX', 'TMO', 'DHR', 'ABT', 'JPM',
    'BAC', 'WFC', 'C', 'GS', 'MS',
    'BK', 'PNC', 'USB', 'TFC', 'COF',
    'AXP', 'BRK-B', 'V', 'MA', 'PYPL',
    'SQ', 'FIS', 'FISV', 'GPN', 'STT',
    'NTRS', 'CBOE', 'ICE', 'MCO', 'SPGI',
    'AON', 'AJG', 'TRV', 'HIG', 'ALL',
    'AIG', 'PGR', 'CINF', 'L', 'BLK',
    'SCHW', 'MMC', 'WTW', 'SLP', 'FHN',
    'SWK', 'RF', 'WMT', 'COST', 'TGT',
    'HD', 'LOW', 'TJX', 'BKNG', 'MCD',
    'NKE', 'LULU', 'SBUX', 'DIS', 'NFLX',
    'CMCSA', 'PARA', 'WBD', 'YUM', 'QSR',
    'CMG', 'DPW', 'DCH', 'MDLZ', 'HSY',
    'CL', 'UL', 'GIS', 'KHC', 'K',
    'SYZ', 'HST', 'ANN', 'AHT', 'DRH',
    'RHP', 'PEAK', 'VTR', 'PSA', 'ESS',
    'AMT', 'EXR', 'HON', 'CAT', 'DE',
    'BA', 'GE', 'UNP', 'UPS', 'LMT',
    'NOC', 'GD', 'ETN', 'PHI', 'ROK',
    'IID', 'JEC', 'JBHT', 'ODFL', 'CHRW',
    'XPO', 'KNX', 'APD', 'BKR', 'EMR',
    'RTX', 'FCX', 'NEM', 'COP', 'XOM',
    'OXY', 'DVN', 'EOG', 'PXD', 'MPC',
    'VLO', 'TSO', 'CTRA', 'WLL', 'PR',
    'RRC', 'THO', 'EQT', 'LIN', 'DD',
    'NUE', 'STLD', 'CLF', 'CVV', 'RS',
    'PKG', 'VMC', 'ML', 'AA', 'X',
    'SM', 'BAX', 'ALGN', 'MOH', 'UHS',
    'HCAT', 'INCY', 'MRVI', 'SRPT', 'NBIX',
    'SGMO', 'BNTX', 'NVAX', 'SRNE', 'SRRK',
    'KPTI', 'ACAD', 'CRSP', 'EDIT', 'BEAM',
    'NTLA', 'VERV', 'MO', 'PM', 'BTI',
    'CPB', 'CAG', 'PEP', 'KO', 'CLX',
    'KMB', 'ADM', 'BG', 'TSN', 'HPQ',
    'CMC', 'MLM', 'BHI', 'RIG', 'SLB',
    'PSX', 'HES', 'FANG', 'MRO', 'APA',
    'SWN', 'CNX', 'AR', 'GPOR', 'PARR',
    'HAL', 'FTI', 'NOV', 'OII', 'CHX',
    'PII', 'VAL', 'HP', 'NE', 'OVV',
    'MUR', 'WTI', 'RNG', 'CHK', 'PRT',
    'MGY', 'CRK', 'LGP', 'CNQ', 'TCM',
    'NLP', 'BTO', 'WEP', 'MEG', 'TGNA',
    'CVCO', 'GMS', 'MGC', 'NAT', 'TGP',
    'PAA', 'WMB', 'NBL', 'LPL', 'MTDR',
    'WPX', 'RPTX', 'GEL', 'NBR', 'CNP',
    'ET', 'LNG', 'MPLX', 'PAGP', 'WES',
    'OKE', 'TECK', 'WPM', 'AEM', 'KGE',
    'GLDG', 'AU', 'GOLD', 'FNV', 'HL',
    'CDE', 'AG', 'MAG', 'SAND', 'PAAS',
    'EXK', 'SLRC', 'EPRT', 'REI', 'CDZI',
    'GLAD', 'CARS', 'FRO', 'EURN', 'TORM',
    'INSW', 'STNG', 'FAL', 'NAVG', 'NMM',
    'SBLK', 'CMCGK', 'DHT', 'GRIM', 'LPG',
    'GATX', 'JJSF', 'SAIA', 'EXPD', 'LSTR',
    'ARCB', 'WERN', 'SAIC', 'UI', 'HTLD',
    'IMII', 'CRUK', 'MRTN', 'PCAR', 'SANM',
    'WAB', 'GT', 'ALK', 'LUV', 'DAL',
    'AAL', 'UAL', 'SKYW', 'JBLU', 'HA',
    'SAVE', 'MESA', 'AIR', 'MAR', 'HLT',
    'IHG', 'H', 'WH', 'APLE', 'XHR',
    'RIVN', 'LCID', 'NIO', 'XPEV', 'LI',
    'FSR', 'GOEV', 'RIDE', 'WKHS', 'BLNK',
    'CHPT', 'EVGO', 'SPCC', 'HTHP', 'FIVN',
    'GRAB', 'DASH', 'UBER', 'LYFT', 'ABNB',
    'EXPE', 'TCOM', 'MMYT', 'TRIP',
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
    if market == "US": return fetch_us_hot_stocks(top_n)
    return []
    """统一入口"""
    if market == "US": return fetch_us_hot_stocks(top_n)
    return []
    """统一入口"""
    if market == "US": return fetch_us_hot_stocks(top_n)
    return []
    """统一入口"""
    if market == "US": return fetch_us_hot_stocks(top_n)
    return []




