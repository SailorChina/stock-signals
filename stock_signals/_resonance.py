# -*- coding: utf-8 -*-
import sys, os as _os
from dataclasses import dataclass

sys.path.insert(0, r'C:\Users\Administrator\.codex\skills\futuapi\scripts')

from .indicators import fetch_kline, compute_indicators
from .scoring import compute_rating, RATINGS


@dataclass
class ResonanceResult:
    daily_rating: str = 'Hold'
    weekly_rating: str = 'Hold'
    monthly_rating: str = 'Hold'
    daily_score: float = 50.0
    weekly_score: float = 50.0
    monthly_score: float = 50.0
    alignment: str = 'none'
    confidence_boost: float = 0.0
    details: str = ''


def compute_timeframe_resonance(code, daily_ind, capital=None, short_pct=None):
    result = ResonanceResult()
    d_r = compute_rating(daily_ind, capital, short_pct)
    result.daily_rating = d_r['rating']
    result.daily_score = d_r['score']
    df_w = fetch_kline(code, '1w', num=100)
    if not df_w.empty and len(df_w) >= 20:
        ind_w = compute_indicators(df_w, code, '1w')
        w_r = compute_rating(ind_w, capital, short_pct)
        result.weekly_rating = w_r['rating']
        result.weekly_score = w_r['score']
    else:
        result.weekly_score = 50.0
    df_m = fetch_kline(code, '1M', num=60)
    if not df_m.empty and len(df_m) >= 10:
        ind_m = compute_indicators(df_m, code, '1M')
        m_r = compute_rating(ind_m, capital, short_pct)
        result.monthly_rating = m_r['rating']
        result.monthly_score = m_r['score']
    else:
        result.monthly_score = 50.0
    def r2n(r): return RATINGS.index(r) if r in RATINGS else 2
    d, w, m = r2n(result.daily_rating), r2n(result.weekly_rating), r2n(result.monthly_rating)
    spread = max(d, w, m) - min(d, w, m)
    if d <= 1 and w <= 1 and m <= 1:
        result.alignment, result.confidence_boost = 'strong_up', 15.0
        result.details = 'Daily/Weekly/Monthly all bullish - strong resonance'
    elif d >= 3 and w >= 3 and m >= 3:
        result.alignment, result.confidence_boost = 'strong_down', -15.0
        result.details = 'Daily/Weekly/Monthly all bearish - strong resonance'
    elif spread <= 1:
        if d <= 1:
            result.alignment, result.confidence_boost = 'aligned', 8.0
            result.details = 'Multi-timeframe bullish, resonance confirmed'
        elif d >= 3:
            result.alignment, result.confidence_boost = 'aligned_down', -8.0
            result.details = 'Multi-timeframe bearish, resonance confirmed'
        else:
            result.alignment, result.confidence_boost = 'mixed', 0.0
            result.details = 'Multi-timeframe direction neutral'
    else:
        result.alignment, result.confidence_boost = 'mixed', 0.0
        result.details = 'Multi-timeframe divergence, wait for clarity'
    return result
