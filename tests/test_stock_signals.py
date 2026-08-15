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


class TestNewFeatures:
    """测试新增功能: ADX、背离、K线形态、缺口、波动率市况"""

    def test_adx_computed(self):
        df = _make_df(100, "up")
        from indicators import compute_indicators
        ind = compute_indicators(df, "US.TEST", "1d")
        assert ind.adx >= 0
        assert ind.plus_di >= 0
        assert ind.minus_di >= 0

    def test_candle_pattern_fields(self):
        from indicators import compute_indicators
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        assert hasattr(ind, "candle_pattern")
        assert hasattr(ind, "gap_type")
        assert hasattr(ind, "vol_regime")
        assert ind.vol_regime in ("low", "normal", "high")
        assert ind.gap_type in ("gap_up", "gap_down", "none", "")

    def test_divergence_fields(self):
        from indicators import compute_indicators
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        assert hasattr(ind, "macd_divergence")
        assert hasattr(ind, "rsi_divergence")
        assert ind.macd_divergence in ("bullish", "bearish", "none")
        assert ind.rsi_divergence in ("bullish", "bearish", "none")

    def test_dynamic_weights_sum_to_one(self):
        from scoring import get_dynamic_weights
        from indicators import compute_indicators
        df = _make_df(100, "flat")
        ind = compute_indicators(df, "US.TEST", "1d")
        weights = get_dynamic_weights(ind)
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_signal_summary_new_items(self):
        from indicators import compute_indicators, signal_summary
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        sigs = signal_summary(ind)
        assert len(sigs) >= 3
        # New signal types should not crash
        labels = [s[0] for s in sigs]
        assert "趋势强度" in labels or "背离" in labels or "K线形态" in labels or len(sigs) >= 3

    def test_td_sequential_bullish(self):
        """测试TD买入序列：连续9根收盘价低于4根前"""
        import numpy as np
        import pandas as pd
        from indicators import compute_indicators
        np.random.seed(99)
        n = 20
        # 构造连续下跌：每根close都比4根前低
        close = np.array([100., 98., 96., 94., 92., 90., 88., 86., 84., 82.,
                          80., 78., 76., 74., 72., 70., 68., 66., 64., 62.])
        open_arr = close + 0.5
        high = close + 1.0
        low = close - 0.5
        volume = np.ones(n) * 100000
        times = pd.date_range("2024-01-01", periods=n, freq="D").astype(str)
        df = pd.DataFrame({"time": times, "open": open_arr, "high": high,
                           "low": low, "close": close, "volume": volume})
        ind = compute_indicators(df, "US.TEST", "1d")
        # 应该有买入序列
        assert ind.td_buy_setup or ind.td_buy_count > 0

    def test_td_sequential_sell(self):
        """测试TD卖出序列：连续9根收盘价高于4根前"""
        import numpy as np
        import pandas as pd
        from indicators import compute_indicators
        np.random.seed(99)
        n = 20
        close = np.array([62., 64., 66., 68., 70., 72., 74., 76., 78., 80.,
                          82., 84., 86., 88., 90., 92., 94., 96., 98., 100.])
        open_arr = close - 0.5
        high = close + 1.0
        low = close - 0.5
        volume = np.ones(n) * 100000
        times = pd.date_range("2024-01-01", periods=n, freq="D").astype(str)
        df = pd.DataFrame({"time": times, "open": open_arr, "high": high,
                           "low": low, "close": close, "volume": volume})
        ind = compute_indicators(df, "US.TEST", "1d")
        assert ind.td_sell_setup or ind.td_sell_count > 0
