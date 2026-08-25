"""Futu OpenD real-time quote module with rate limiting.
Uses Futu OpenD to get real-time US stock prices.
"""
from __future__ import annotations
import logging
import threading
import time
from typing import Dict, Optional

logger = logging.getLogger('stock-signals')


# 全局连接池
_quote_ctx = None
_ctx_lock = threading.Lock()
_last_connect_time = 0
_MIN_CONNECT_INTERVAL = 2.0


def _get_ctx():
    """获取 Futu OpenD 连接（带限流）"""
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
            logger.warning(f'Futu OpenD connection failed: {e}')
            _quote_ctx = None
        return _quote_ctx


def fetch_realtime_prices(codes):
    """批量获取实时报价（带限流保护）"""
    result = {}
    ctx = _get_ctx()
    if ctx is None:
        return result
    try:
        from futu import SubType
        ctx.subscribe(codes, [SubType.QUOTE])
        ret, data = ctx.get_stock_quote(codes)
        if ret != 0:
            logger.warning(f'Futu get_stock_quote error code={ret}')
            return result
        for _, row in data.iterrows():
            code = row['code']
            last = float(row['last_price']) if row['last_price'] else 0.0
            prev = float(row['prev_close_price']) if row['prev_close_price'] else last
            result[code] = {
                'last_price': last,
                'open': float(row['open_price']) if row['open_price'] else 0.0,
                'high': float(row['high_price']) if row['high_price'] else 0.0,
                'low': float(row['low_price']) if row['low_price'] else 0.0,
                'prev_close': prev,
                'volume': int(row['volume']) if row['volume'] else 0,
                'change_pct': (last - prev) / prev * 100 if prev > 0 else 0.0,
            }
    except Exception as e:
        logger.warning(f'Futu realtime error: {e}')
        global _quote_ctx
        with _ctx_lock:
            _quote_ctx = None
    return result


def fetch_realtime_price(code):
    """获取单只股票实时报价"""
    results = fetch_realtime_prices([code])
    return results.get(code)


def refresh_indicators_with_realtime(ind, code):
    """用 Futu 实时价格覆盖 indicators 对象"""
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
            _recent_high = high_52w
            _recent_low = low_52w
            ind.rs_percentile = round((new_price - _recent_low) / (_recent_high - _recent_low) * 100, 1) if _recent_high > _recent_low else 50.0
            ind.rs_rating = int(ind.rs_percentile)
    _passed = True
    if ind.ma200 > 0:
        if new_price <= ind.ma20: _passed = False
        if new_price <= ind.ma60: _passed = False
        if new_price <= ind.ma200: _passed = False
        if ind.ma60 <= ind.ma200: _passed = False
    ind.trend_template_pass = _passed
    logger.info(f'  {code} realtime overlay: {old_price:.2f} -> {new_price:.2f} (dist MA200: {ind.price_vs_ma200:+.1f}%)')
    return True
