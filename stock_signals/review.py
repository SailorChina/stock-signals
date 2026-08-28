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
    status = 'holding'
    if current_price <= sl and sl > 0:
        status = 'stop_loss'
    elif current_price >= t1 and t1 > 0:
        status = 'target1_achieved'
    elif current_price >= t2 and t2 > 0:
        status = 'target2_achieved'
    return {'pnl_pct': round(pnl_pct, 2), 'status': status}
