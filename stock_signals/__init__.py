# -*- coding: utf-8 -*-
"""stock_signals package v2.8.4"""
__version__ = "2.9.0"
__author__ = "SailorChina"

from .indicators import fetch_kline, compute_indicators, Indicators, signal_summary
from .scoring import compute_rating, generate_signals, get_capital_data, get_short_data, RATINGS, DIM_WEIGHTS
from ._resonance import compute_timeframe_resonance
from ._sr import compute_support_resistance, generate_trade_plan, compute_trend_phase

__all__ = [
    "fetch_kline", "compute_indicators", "Indicators", "signal_summary",
    "compute_rating", "generate_signals", "get_capital_data", "get_short_data",
    "RATINGS", "DIM_WEIGHTS",
    "compute_timeframe_resonance",
    "compute_support_resistance", "generate_trade_plan", "compute_trend_phase",
]
