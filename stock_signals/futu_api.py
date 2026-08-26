# -*- coding: utf-8 -*-
"""Futu OpenD real-time quote module with rate limiting and batch processing."""
from __future__ import annotations
import logging
import threading
import time
from typing import Dict, Optional, List

logger = logging.getLogger('tech-signal-skill')
_quote_ctx = None
_ctx_lock = threading.Lock()
_last_connect_time = 0
_MIN_CONNECT_INTERVAL = 2.0
_BATCH_SIZE = 25
_BATCH_INTERVAL = 0.3


def _get_ctx():
    global _quote_ctx, _last_connect_time
    with _ctx_lock:
        now = time.time()
        if _quote_ctx is not None:
            try:
                _quote_ctx.get_market_snapshot(['US.AAPL'])
                return _quote_ctx
            except Exception:
                try:
                    _quote_ctx.close()
                except Exception:
                    pass
                _quote_ctx = None
        elapsed = now - _last_connect_time
        if elapsed < _MIN_CONNECT_INTERVAL:
            time.sleep(_MIN_CONNECT_INTERVAL - elapsed)
        from futu import OpenQuoteContext
        try:
            _quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
            logger.info('Futu OpenD connected')
            _last_connect_time = time.time()
        except Exception as e:
            logger.warning('Futu OpenD connection failed: ' + str(e))
            _quote_ctx = None
        return _quote_ctx

def fetch_realtime_prices(codes):
    result = {}
    if not codes:
        return result
    ctx = _get_ctx()
    if ctx is None:
        return result
    try:
        from futu import SubType
        for i in range(0, len(codes), _BATCH_SIZE):
            batch = codes[i:i + _BATCH_SIZE]
            ctx.subscribe(batch, [SubType.QUOTE])
            ret, data = ctx.get_market_snapshot(batch)
            if ret != 0:
                logger.warning('Futu error code=' + str(ret))
                continue
            for _, row in data.iterrows():
                code = row.get('code', '')
                last = float(row.get('last_price', 0) or 0)
                prev = float(row.get('prev_close_price', 0) or last)
                result[code] = {
                    'last_price': last,
                    'open': float(row.get('open_price', 0) or 0),
                    'high': float(row.get('high_price', 0) or 0),
                    'low': float(row.get('low_price', 0) or 0),
                    'prev_close': prev,
                    'volume': int(row.get('volume', 0) or 0),
                    'change_pct': (last - prev) / prev * 100 if prev > 0 else 0.0,
                }
            time.sleep(_BATCH_INTERVAL)
        logger.info('Futu batch fetch done: ' + str(len(result)) + '/' + str(len(codes)) + ' stocks')
    except Exception as e:
        logger.warning('Futu realtime error: ' + str(e))
        global _quote_ctx
        with _ctx_lock:
            _quote_ctx = None
    return result


def fetch_realtime_price(code):
    results = fetch_realtime_prices([code])
    return results.get(code)

def refresh_indicators_with_realtime(ind, code):
    realtime = fetch_realtime_price(code)
    if realtime is None:
        return False
    old_price = ind.last_close
    new_price = realtime['last_price']
    if new_price <= 0:
        return False
    ind.last_close = new_price
    ind.prev_close = realtime['prev_close'] if realtime['prev_close'] > 0 else old_price
    ind.day_change_pct = realtime['change_pct']
    for ma_attr, pct_attr in [('ma20', 'price_vs_ma20'), ('ma60', 'price_vs_ma60'), ('ma200', 'price_vs_ma200')]:
        ma_val = getattr(ind, ma_attr, 0)
        if ma_val > 0:
            setattr(ind, pct_attr, (new_price - ma_val) / ma_val * 100)
    n = len(ind.df) if hasattr(ind, 'df') and ind.df is not None else 0
    if n >= 20:
        close = ind.df['close'].values.astype(float) if hasattr(ind, 'df') and ind.df is not None else []
        high = ind.df['high'].values.astype(float) if hasattr(ind, 'df') and ind.df is not None else []
        _52w = min(252, n)
        if len(close) >= _52w and len(high) >= _52w:
            high_52w = float(max(high[-_52w:]))
            low_52w = float(min(high[-_52w:]))
            if high_52w > 0:
                ind.distance_from_52w_high = (high_52w - new_price) / high_52w * 100
            if low_52w > 0:
                ind.distance_from_52w_low = (new_price - low_52w) / low_52w * 100
            ind.rs_percentile = round((new_price - low_52w) / (high_52w - low_52w) * 100, 1) if high_52w > low_52w else 50.0
            ind.rs_rating = int(ind.rs_percentile)
    _passed = True
    if ind.ma200 > 0:
        if new_price <= ind.ma20:
            _passed = False
        if new_price <= ind.ma60:
            _passed = False
        if new_price <= ind.ma200:
            _passed = False
        if ind.ma60 <= ind.ma200:
            _passed = False
    ind.trend_template_pass = _passed
    dist = (new_price - ind.ma200) / ind.ma200 * 100 if ind.ma200 > 0 else 0
    logger.info('  ' + code + ' realtime: ' + str(round(old_price, 2)) + ' -> ' + str(round(new_price, 2)) + ' (MA200: ' + format(dist, '+.1f') + '%)')
    return True
