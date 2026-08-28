# -*- coding: utf-8 -*-
def get_pending_reviews():
    from stock_signals.tracker import get_recommendations
    return [r for r in get_recommendations() if r['outcome'] in ('recommended', 'watch') and r.get('outcome_price') is None]

def fetch_current_prices(symbols):
    prices = {}
    if not symbols:
        return prices
    try:
        from stock_signals.futu_api import fetch_realtime_prices
        result = fetch_realtime_prices(symbols)
        if result:
            for s, p in result.items():
                if p and p > 0:
                    prices[s] = float(p)
    except ImportError:
        pass
    except Exception:
        pass
    return prices

def calc_pnl(rec, current_price):
    entry = rec.get('entry_price') or rec.get('current_price') or 0
    if entry <= 0:
        return {'pnl_pct': None, 'status': 'unknown'}
    pnl_pct = (current_price - entry) / entry * 100
    sl = rec.get('stop_loss') or 0
    t1 = rec.get('target1') or 0
    t2 = rec.get('target2') or 0
    if current_price <= sl and sl > 0:
        status = 'stopped'
    elif current_price >= t1 and t1 > 0:
        status = 'target1_hit'
    elif current_price >= t2 and t2 > 0:
        status = 'target2_hit'
    elif pnl_pct > 5:
        status = 'profit'
    elif pnl_pct < -5:
        status = 'loss'
    else:
        status = 'holding'
    return {'pnl_pct': round(pnl_pct, 2), 'status': status}

def auto_review(yesterday_date=None):
    from datetime import datetime, timedelta
    if yesterday_date is None:
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    from stock_signals.tracker import get_recommendations
    recs = get_recommendations(date=yesterday_date, outcome='recommended')
    if not recs:
        recs = get_recommendations(date=yesterday_date, outcome='watch')
    if not recs:
        return {'message': f'没有找到 {yesterday_date} 的推荐记录', 'recs': []}
    symbols = [r['symbol'] for r in recs]
    live_prices = {}
    try:
        live_prices = fetch_current_prices(symbols)
    except Exception:
        pass
    results = []
    for r in recs:
        sym = r['symbol']
        cur = live_prices.get(sym) or r.get('current_price') or 0
        pnl = calc_pnl(r, cur)
        results.append({**r, 'current_price': cur, 'pnl_pct': pnl['pnl_pct'], 'status': pnl['status'], 'live_price': sym in live_prices})
    return {'date': yesterday_date, 'recs': results, 'prices': live_prices}
