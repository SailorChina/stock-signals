# -*- coding: utf-8 -*-
"""Unit tests for stock_signals"""
import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "stock_signals"))

from indicators import compute_indicators, Indicators, _ema, _kdj_full_series
from scoring import compute_rating, generate_signals, RATINGS, DIM_WEIGHTS, score_trend, score_momentum, score_volume, score_volatility, score_capital
from _sr import compute_support_resistance, generate_trade_plan, compute_trend_phase


def _make_df(n=100, trend="up"):
    np.random.seed(42)
    if trend == "up":
        close = 100 + np.cumsum(np.random.randn(n) * 0.3) + np.linspace(0, 20, n)
    elif trend == "down":
        close = 100 + np.cumsum(np.random.randn(n) * 0.3) - np.linspace(0, 20, n)
    else:
        close = 100 + np.cumsum(np.random.randn(n) * 0.3)
    high = close + np.abs(np.random.randn(n) * 0.5)
    low = close - np.abs(np.random.randn(n) * 0.5)
    volume = np.random.randint(100000, 1000000, n).astype(float)
    times = pd.date_range("2024-01-01", periods=n, freq="D").astype(str)
    return pd.DataFrame({"time": times, "open": close, "high": high, "low": low, "close": close, "volume": volume})


class TestIndicators:
    def test_compute_indicators_basic(self):
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        assert ind.last_close > 0
        assert ind.ma5 > 0
        assert ind.ma20 > 0
        assert ind.macd_dif != 0
        assert ind.rsi_14 > 0
        assert ind.kdj_k > 0
        assert ind.boll_mid > 0
        assert ind.atr_14 > 0
        assert ind.obv_trend in ("up", "down", "flat")

    def test_compute_indicators_short(self):
        df = _make_df(20, "flat")
        ind = compute_indicators(df, "US.TEST", "1d")
        assert ind.last_close > 0

    def test_ema(self):
        arr = np.arange(1, 11, dtype=float)
        result = _ema(arr, 3)
        assert len(result) == 10
        assert result[0] == 1.0
        assert result[-1] > result[0]

    def test_kdj(self):
        close = np.linspace(10, 20, 50)
        high = close + 0.5
        low = close - 0.5
        k, d = _kdj_full_series(low, high, close, 9, 3, 3)
        assert len(k) == 50
        assert all(0 <= v <= 100 for v in k[-10:])
        assert all(0 <= v <= 100 for v in d[-10:])


class TestScoring:
    def test_score_trend_bullish(self):
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        s, r = score_trend(ind)
        assert 50 <= s <= 100
        assert isinstance(r, str) and len(r) > 0

    def test_score_trend_bearish(self):
        df = _make_df(100, "down")
        ind = compute_indicators(df, "US.TEST", "1d")
        s, r = score_trend(ind)
        assert 0 <= s <= 50

    def test_compute_rating(self):
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        result = compute_rating(ind, {}, None)
        assert result["rating"] in RATINGS
        assert 0 <= result["score"] <= 100
        assert result["confidence"] in ("high", "medium", "low")
        assert "dimensions" in result
        for dim in DIM_WEIGHTS:
            assert dim in result["dimensions"]

    def test_weights_sum_to_one(self):
        total = sum(DIM_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001


class TestSupportResistance:
    def test_compute_sr(self):
        df = _make_df(100, "up")
        sr = compute_support_resistance(df)
        assert sr["resistance_1"] > 0
        assert sr["support_1"] > 0
        assert sr["resistance_1"] > sr["support_1"]
        assert sr["vwap"] > 0

    def test_trade_plan(self):
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        sr = compute_support_resistance(df)
        tp = generate_trade_plan(ind, sr, "rally")
        assert tp.entry_zone > 0
        assert tp.stop_loss > 0
        assert tp.target_1 > tp.entry_zone
        assert tp.risk_reward > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
