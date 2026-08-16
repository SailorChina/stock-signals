# -*- coding: utf-8 -*-
"""Unit tests for stock_signals"""
import pytest
import numpy as np
import pandas as pd
import sys
import os
from dataclasses import dataclass

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


class TestNewFeatures:
    def test_adx_computed(self):
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        assert ind.adx >= 0
        assert ind.plus_di >= 0
        assert ind.minus_di >= 0

    def test_candle_pattern_fields(self):
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        assert hasattr(ind, "candle_pattern")
        assert hasattr(ind, "gap_type")
        assert hasattr(ind, "vol_regime")
        assert ind.vol_regime in ("low", "normal", "high")
        assert ind.gap_type in ("gap_up", "gap_down", "none", "")

    def test_divergence_fields(self):
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        assert hasattr(ind, "macd_divergence")
        assert hasattr(ind, "rsi_divergence")
        assert ind.macd_divergence in ("bullish", "bearish", "none")
        assert ind.rsi_divergence in ("bullish", "bearish", "none")

    def test_dynamic_weights_sum_to_one(self):
        from scoring import get_dynamic_weights
        df = _make_df(100, "flat")
        ind = compute_indicators(df, "US.TEST", "1d")
        weights = get_dynamic_weights(ind)
        assert abs(sum(weights.values()) - 1.0) < 0.001

    def test_signal_summary_new_items(self):
        from indicators import signal_summary
        df = _make_df(100, "up")
        ind = compute_indicators(df, "US.TEST", "1d")
        sigs = signal_summary(ind)
        assert len(sigs) >= 3

    def test_td_sequential_bullish(self):
        np.random.seed(99)
        n = 20
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
        assert ind.td_buy_setup or ind.td_buy_count > 0

    def test_td_sequential_sell(self):
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


class TestReporter:
    """测试 reporter.py 的中文报告生成和观察列表显示"""

    def test_fmt_pct(self):
        from stock_signals.reporter import _fmt_pct
        assert _fmt_pct(110.0, 100.0) == "+10.0%"
        assert _fmt_pct(90.0, 100.0) == "-10.0%"
        assert _fmt_pct(100.0, 100.0) == "+0.0%"
        assert _fmt_pct(50.0, 0) == ""

    def test_gen_entry_conditions_rsi_overbought(self):
        from stock_signals.reporter import _gen_entry_conditions
        @dataclass
        class MockResult:
            code = "US.TEST"
            last_close = 100.0
            entry = 95.0
            reasons = ["RSI(14)=75.2，超买", "MACD柱为正，多头动能"]
            risk_reward = 2.5
        r = MockResult()
        conditions = _gen_entry_conditions(r)
        assert any("RSI" in c for c in conditions)

    def test_gen_entry_conditions_no_match(self):
        from stock_signals.reporter import _gen_entry_conditions
        @dataclass
        class MockResult:
            code = "US.TEST"
            last_close = 100.0
            entry = 95.0
            reasons = []
            risk_reward = 3.0
        r = MockResult()
        conditions = _gen_entry_conditions(r)
        assert len(conditions) > 0
        assert "等待" in conditions[0]

    def test_gen_risk_warnings_overbought(self):
        from stock_signals.reporter import _gen_risk_warnings
        @dataclass
        class MockResult:
            code = "US.TEST"
            last_close = 100.0
            entry = 95.0
            reasons = ["RSI(14)=82.5，严重超买"]
            risk_reward = 2.5
        r = MockResult()
        warnings = _gen_risk_warnings(r)
        assert any("严重超买" in w for w in warnings)

    def test_gen_risk_warnings_low_rr(self):
        from stock_signals.reporter import _gen_risk_warnings
        @dataclass
        class MockResult:
            code = "US.TEST"
            last_close = 100.0
            entry = 98.0
            reasons = []
            risk_reward = 1.5
        r = MockResult()
        warnings = _gen_risk_warnings(r)
        assert any("风险回报不足" in w for w in warnings)

    def test_print_stock_watchlist(self, capsys):
        from stock_signals.reporter import _print_stock
        @dataclass
        class MockResult:
            code = "US.LRCX"
            rating = "Overweight"
            score = 58.5
            alignment = "mixed"
            trend_phase = "accumulation"
            entry = 850.0
            stop_loss = 810.0
            target_1 = 920.0
            target_2 = 960.0
            risk_reward = 2.8
            position_pct = 2.0
            last_close = 880.0
            reasons = ["KDJ K=80.5，超买", "ADX=18.9，趋势弱"]
        r = MockResult()
        _print_stock(r, 1, watch=True)
        captured = capsys.readouterr()
        assert "US.LRCX" in captured.out
        assert "现价" in captured.out
        assert "等待条件" in captured.out
        assert "风险提示" in captured.out
        assert "入场" in captured.out
        assert "止损" in captured.out
        assert "目标" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestVCP:
    """测试 VCP 波动率收缩检测"""
    def test_vcp_module_import(self):
        from stock_signals._vcp import detect_vcp
        assert callable(detect_vcp)

    def test_vcp_no_data(self):
        from stock_signals._vcp import detect_vcp
        import pandas as pd
        df = pd.DataFrame({'close': [100], 'high': [100], 'low': [99], 'volume': [1000]})
        result = detect_vcp(df)
        assert not result.detected

    def test_vcp_contraction_detection(self):
        from stock_signals._vcp import detect_vcp
        import numpy as np
        import pandas as pd
        np.random.seed(42)
        n = 100
        close = np.ones(n) * 100
        close[20:30] = 100 - np.linspace(0, 15, 10)
        close[30:45] = 85 + np.linspace(0, 8, 15)
        close[45:52] = 93 - np.linspace(0, 8, 7)
        close[52:65] = 85 + np.linspace(0, 5, 13)
        close[65:] = 85 + np.linspace(0, 12, 35)
        high = close + np.abs(np.random.randn(n) * 2)
        low = close - np.abs(np.random.randn(n) * 2)
        volume = np.random.randint(100000, 1000000, n).astype(float)
        volume[45:70] = volume[45:70] * 0.5
        df = pd.DataFrame({'time': pd.date_range('2024-01-01', periods=n, freq='D').astype(str), 'open': close, 'high': high, 'low': low, 'volume': volume})
        result = detect_vcp(df)
        assert hasattr(result, 'detected')
        assert hasattr(result, 'contractions')


class TestEpisodicPivot:
    """测试 Episodic Pivot 事件性转折检测"""
    def test_ep_module_import(self):
        from stock_signals._episodic_pivot import detect_episodic_pivot
        assert callable(detect_episodic_pivot)

    def test_ep_no_data(self):
        from stock_signals._episodic_pivot import detect_episodic_pivot
        import pandas as pd
        df = pd.DataFrame({'close': [100], 'high': [100], 'low': [99], 'volume': [1000]})
        result = detect_episodic_pivot(df)
        assert not result.detected

    def test_ep_gap_detection(self):
        from stock_signals._episodic_pivot import detect_episodic_pivot
        import numpy as np
        import pandas as pd
        n = 60
        close = np.ones(n) * 100
        close[-1] = 105
        high = close + 1
        low = close - 1
        volume = np.ones(n) * 100000
        volume[-1] = 500000
        df = pd.DataFrame({'time': pd.date_range('2024-01-01', periods=100, freq='D').astype(str), 'close': close, 'high': high, 'low': low, 'volume': volume})
        result = detect_episodic_pivot(df)
        assert result.gap_up_pct > 0
        assert result.volume_spike > 1


class TestRSAndTrendTemplate:
    """测试相对强度和趋势模板"""
    def test_rs_fields_exist(self):
        from stock_signals.indicators import compute_indicators
        import numpy as np
        import pandas as pd
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(100) * 0.5) + np.linspace(0, 30, 100)
        high = close + 1
        low = close - 1
        volume = np.ones(100) * 100000
        df = pd.DataFrame({'time': pd.date_range('2024-01-01', periods=100, freq='D').astype(str), 'open': close, 'high': high, 'low': low, 'volume': volume})
        ind = compute_indicators(df, 'US.TEST', '1d')
        assert hasattr(ind, 'rs_rating')
        assert hasattr(ind, 'distance_from_52w_high')
        assert hasattr(ind, 'trend_template_pass')
