# -*- coding: utf-8 -*-
"""热门股获取模块 - 多 API fallback 方案"""
from __future__ import annotations
import logging, time, os, urllib.request, json
from typing import List
import pandas as pd
logger = logging.getLogger('stock-signals')
for _k in list(os.environ.keys()):
    if 'proxy' in _k.lower(): os.environ.pop(_k, None)
os.environ.setdefault('no_proxy', '*')
os.environ.setdefault('NO_PROXY', '*')

# v2.13: market cap floor raised to 10B USD
MIN_MARKET_CAP = 10e9
MKT_CAP = {
    'NVDA': 2800000000000.0, 'AAPL': 2900000000000.0, 'MSFT': 3100000000000.0,
    'GOOG': 2000000000000.0, 'GOOGL': 2000000000000.0, 'AMZN': 1800000000000.0,
    'META': 1200000000000.0, 'TSLA': 500000000000.0, 'AVGO': 600000000000.0,
    'CSCO': 200000000000.0, 'ORCL': 350000000000.0, 'AMD': 200000000000.0,
    'INTC': 100000000000.0, 'QCOM': 180000000000.0, 'MU': 100000000000.0,
    'NXPI': 60000000000.0, 'AMAT': 150000000000.0, 'LRCX': 80000000000.0,
    'ASML': 300000000000.0, 'TXN': 170000000000.0, 'NOW': 200000000000.0,
    'CRM': 250000000000.0, 'ADBE': 220000000000.0, 'PANW': 100000000000.0,
    'PLTR': 50000000000.0, 'LLY': 600000000000.0, 'ABBV': 280000000000.0,
    'JNJ': 380000000000.0, 'MRK': 300000000000.0, 'PFE': 150000000000.0,
    'BMY': 80000000000.0, 'UNH': 480000000000.0, 'TMO': 200000000000.0,
    'DHR': 150000000000.0, 'ABT': 180000000000.0, 'V': 500000000000.0,
    'MA': 400000000000.0, 'BRK-B': 800000000000.0, 'WMT': 450000000000.0,
    'COST': 300000000000.0, 'HD': 350000000000.0, 'MCD': 180000000000.0,
    'NKE': 100000000000.0, 'DIS': 180000000000.0, 'NFLX': 200000000000.0,
    'XOM': 400000000000.0, 'COP': 120000000000.0, 'OXY': 60000000000.0,
    'HON': 150000000000.0, 'CAT': 150000000000.0, 'BA': 100000000100.0,
    'GE': 150000000000.0, 'UNP': 130000000000.0, 'UPS': 130000000000.0,
    'LMT': 100000000000.0, 'RTX': 120000000000.0, 'FCX': 50000000000.0,
    'NEM': 40000000000.0, 'EMR': 50000000000.0, 'DASH': 80000000000.0,
    'UBER': 120000000000.0, 'ABNB': 80000000000.0, 'ZTS': 80000000000.0,
    'LOW': 120000000000.0, 'TJX': 100000000000.0, 'BKNG': 70000000000.0,
    'LULU': 50000000000.0, 'SBUX': 100000000000.0, 'CMCSA': 150000000000.0,
    'MDLZ': 50000000000.0, 'HSY': 50000000000.0, 'CL': 50000000000.0,
    'UL': 80000000000.0, 'GIS': 30000000000.0, 'KHC': 20000000000.0,
    'K': 10000000000.0, 'MO': 60000000000.0, 'PM': 120000000000.0,
    'BTI': 20000000000.0, 'CPB': 20000000000.0, 'CAG': 10000000000.0,
    'PEP': 220000000000.0, 'KO': 250000000000.0, 'CLX': 50000000000.0,
    'KMB': 50000000000.0, 'BG': 20000000000.0, 'TSN': 30000000000.0,
    'HPQ': 20000000000.0, 'ADM': 30000000000.0, 'CMG': 30000000000.0,
    'HST': 10000000000.0, 'YUM': 40000000000.0, 'EQT': 10000000000.0,
    'SLB': 50000000000.0, 'HAL': 20000000000.0, 'MPC': 30000000000.0,
    'PSX': 60000000000.0, 'VLO': 30000000000.0, 'OKE': 30000000000.0,
    'WMB': 30000000000.0, 'ET': 50000000000.0, 'LNG': 30000000000.0,
    'MPLX': 40000000000.0, 'KMI': 40000000000.0, 'MRNA': 10000000000.0,
    'ALGN': 20000000000.0, 'MOH': 30000000000.0, 'UHS': 10000000000.0,
    'SNAP': 8000000000.0, 'PINS': 20000000000.0, 'F': 40000000000.0,
    'GM': 50000000000.0, 'MAR': 30000000000.0, 'HLT': 40000000000.0,
    'APLE': 10000000000.0, 'TGT': 50000000000.0, 'PARA': 10000000000.0,
    'WBD': 20000000000.0, 'QSR': 30000000000.0, 'SPGI': 130000000000.0,
    'PGR': 60000000000.0, 'CB': 80000000000.0, 'TRV': 30000000000.0,
    'ALL': 50000000000.0, 'AON': 30000000000.0, 'AJG': 20000000000.0,
    'WTW': 40000000000.0, 'BLK': 120000000000.0, 'SCHW': 100000000000.0,
    'CME': 80000000000.0, 'ICE': 80000000000.0, 'MCO': 30000000000.0,
    # Healthcare / Pharma
    'AMGN': 150000000000.0, 'GILD': 120000000000.0, 'REGN': 100000000000.0,
    'BIIB': 40000000000.0, 'VRTX': 100000000000.0,
    # Financials
    'JPM': 500000000000.0, 'BAC': 250000000000.0, 'WFC': 150000000000.0,
    'C': 100000000000.0, 'GS': 120000000000.0, 'MS': 100000000000.0,
    'USB': 60000000000.0, 'PNC': 50000000000.0, 'TFC': 40000000000.0,
    'BK': 30000000000.0, 'AXP': 150000000000.0, 'MMC': 60000000000.0,
    # Insurance
    'AIG': 40000000000.0, 'MET': 40000000000.0, 'PRU': 50000000000.0,
    'AFL': 20000000000.0, 'HIG': 30000000000.0, 'CINF': 20000000000.0,
    'L': 20000000000.0, 'RHI': 10000000000.0,
    # Industrials / Defense
    'J': 20000000000.0, 'HII': 30000000000.0, 'KTOS': 10000000000.0,
    'EW': 20000000000.0,
    # Medical devices
    'HOLX': 20000000000.0, 'SYK': 50000000000.0, 'BDX': 40000000000.0,
    'BSX': 80000000000.0, 'MDT': 50000000000.0, 'ABC': 40000000000.0,
    # Insurance / Healthcare services
    'CI': 150000000000.0, 'HUM': 50000000000.0, 'CNC': 40000000000.0,
    'ANTM': 50000000000.0, 'ELV': 50000000000.0,
    # Pharmacy / Retail
    'WBA': 10000000000.0, 'CVS': 80000000000.0,
    # Intl pharma
    'GSK': 70000000000.0, 'AZN': 180000000000.0, 'NVO': 350000000000.0,
    'SNY': 80000000000.0,
    'AVAV': 5000000000.0,
}
_US_STATIC_POOL = [
    'AAPL', 'MSFT', 'GOOG', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
    'AVGO', 'CSCO', 'ORCL', 'AMD', 'INTC', 'QCOM', 'MU', 'NXPI',
    'AMAT', 'LRCX', 'ASML', 'TXN', 'NOW', 'CRM', 'ADBE', 'PANW',
    'PLTR', 'LLY', 'ABBV', 'JNJ', 'MRK', 'PFE', 'BMY', 'UNH',
    'TMO', 'DHR', 'ABT', 'AMGN', 'GILD', 'REGN', 'BIIB', 'VRTX',
    'V', 'MA', 'BRK-B', 'WMT', 'COST', 'HD', 'MCD', 'NKE', 'DIS',
    'NFLX', 'XOM', 'COP', 'OXY', 'HON', 'CAT', 'BA', 'GE', 'UNP',
    'UPS', 'LMT', 'RTX', 'FCX', 'NEM', 'EMR', 'DASH', 'UBER', 'ABNB',
    'ZTS', 'LOW', 'TJX', 'BKNG', 'LULU', 'SBUX', 'CMCSA', 'MDLZ',
    'HSY', 'CL', 'UL', 'GIS', 'KHC', 'K', 'MO', 'PM', 'BTI',
    'CPB', 'CAG', 'PEP', 'KO', 'CLX', 'KMB', 'BG', 'TSN', 'HPQ',
    'ADM', 'CMG', 'HST', 'YUM', 'EQT', 'SLB', 'HAL', 'MPC', 'PSX',
    'VLO', 'OKE', 'WMB', 'ET', 'LNG', 'MPLX', 'KMI', 'MRNA', 'ALGN',
    'MOH', 'UHS', 'SNAP', 'PINS', 'F', 'GM', 'MAR', 'HLT', 'APLE',
    'TGT', 'PARA', 'WBD', 'QSR', 'SPGI', 'PGR', 'CB', 'TRV', 'ALL',
    'AON', 'AJG', 'WTW', 'BLK', 'SCHW', 'CME', 'ICE', 'MCO',
    'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'USB', 'PNC', 'TFC',
    'BK', 'AXP', 'MMC', 'AIG', 'MET', 'PRU', 'AFL', 'HIG', 'CINF', 'L', 'RHI',
    'J', 'HII', 'KTOS', 'AVAV', 'EW', 'HOLX', 'SYK', 'BDX', 'BSX',
    'MDT', 'ABC', 'CI', 'HUM', 'CNC', 'ANTM', 'ELV', 'WBA', 'CVS',
    'GSK', 'AZN', 'NVO', 'SNY',
    'SNPS', 'CDNS', 'ADSK', 'ANSS', 'FTNT', 'NET', 'SNOW', 'CRWD', 'DDOG', 'MDB', 'SHOP', 'SQ', 'PYPL', 'IBM', 'DELL', 'HPE', 'ACN', 'ZBH', 'COO', 'ISRG', 'BR', 'FIS', 'ADP', 'DG', 'DLTR', 'GPS', 'ANF', 'RL', 'TPR', 'M', 'KSS', 'DPZ', 'SWK', 'TM', 'APTV', 'BWA', 'AZO', 'LEA', 'ALK', 'NCLH', 'WYNN', 'MGM', 'DKNG', 'LYV', 'XEL', 'ED', 'WEC', 'ES', 'ARE', 'MAA', 'KIM', 'REG', 'GOLD', 'WPM', 'FNV', 'AA', 'NUE', 'STLD', 'ECL', 'DD', 'DOW', 'EMN', 'CTVA', 'MMM', 'MOS',
    'SNPS', 'CDNS', 'ADSK', 'ANSS', 'FTNT', 'NET', 'SNOW', 'CRWD', 'DDOG', 'MDB',
    'SHOP', 'SQ', 'PYPL', 'IBM', 'HPQ', 'DELL', 'HPE', 'ACN',
    'SYK', 'BDX', 'BSX', 'MDT', 'HOLX', 'ZBH', 'COO', 'EW', 'ISRG', 'ZTS',
    'BLK', 'SCHW', 'CME', 'ICE', 'BR', 'FIS', 'ADP',
    'AON', 'AJG', 'WTW', 'MMC', 'AIG', 'MET', 'PRU', 'AFL', 'HIG',
    'CI', 'HUM', 'CNC', 'ANTM', 'ELV',
    'DG', 'DLTR', 'GPS', 'ANF', 'RL', 'TPR', 'M', 'KSS',
    'DPZ', 'SWK',
    'TM', 'APTV', 'BWA', 'AZO', 'LEA',
    'ALK', 'NCLH',
    'WYNN', 'MGM', 'DKNG',
    'LYV',
    'XEL', 'ED', 'WEC', 'ES',
    'ARE', 'MAA', 'KIM', 'REG',
    'GOLD', 'WPM', 'FNV', 'AA', 'NUE', 'STLD',
    'ECL', 'DD', 'DOW', 'EMN', 'CTVA',
    'MMM', 'MOS',
    'CVS', 'WBA', 'ABC',
]


def _fetch_us_quotes_from_sina(ticker_list, batch_size=80):
    all_stocks = []
    for i in range(0, len(ticker_list), batch_size):
        batch = ticker_list[i:i+batch_size]
        gbs = ['gb_' + t.lower() for t in batch]
        tickers = ','.join(gbs)
        url = 'http://hq.sinajs.cn/list=' + tickers
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer': 'http://finance.sina.com.cn/'})
            resp = urllib.request.urlopen(req, timeout=10)
            data = resp.read().decode('gbk', errors='replace')
            for line in data.strip().split(chr(10)):
                if 'hq_str_gb_' not in line:
                    continue
                parts = line.split('=')
                if len(parts) < 2:
                    continue
                ticker = parts[0].replace('var hq_str_gb_', '').strip().upper()
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
            logger.warning('Sina batch failed: ' + str(e))
    return all_stocks


def fetch_us_hot_stocks(top_n=300):
    pool = list(dict.fromkeys(_US_STATIC_POOL))
    logger.info('  US static pool: ' + str(len(pool)) + ' stocks')
    try:
        t = time.time()
        quotes = _fetch_us_quotes_from_sina(pool)
        if quotes:
            quotes.sort(key=lambda x: x['volume'], reverse=True)
            codes = ['US.' + s['ticker'] for s in quotes[:top_n]]
            elapsed = time.time() - t
            logger.info('  US hot (volume): ' + str(len(codes)) + ' stocks (' + str(round(elapsed, 1)) + 's)')
            return codes
        else:
            logger.warning('  Sina no data')
    except Exception as e:
        logger.warning('  US hot fetch failed: ' + str(e))
    logger.info('  US: using static pool')
    return ['US.' + t for t in pool[:top_n]]


def fetch_hot_stocks(market, top_n=300):
    if market == 'US':
        return fetch_us_hot_stocks(top_n)
    return []