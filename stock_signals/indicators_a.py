# -*- coding: utf-8 -*-
"""A股专属技术指标模块"""
from __future__ import annotations
import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class IndicatorsA:
    ma5: float = 0.0; ma10: float = 0.0; ma20: float = 0.0; ma60: float = 0.0
    rsi_14: float = 0.0; macd_dif: float = 0.0; macd_dea: float = 0.0
    atr_14: float = 0.0; obv_trend: str = "flat"; vol_ratio: float = 0.0
    last_close: float = 0.0; day_change_pct: float = 0.0
    turnover_rate: float = 0.0; north_flow: float = 0.0
    is_longhubang: bool = False; is_sector_leader: bool = False
    limit_up_prob: float = 0.0; sector_change: float = 0.0
    # KDJ
    kdj_k: float = 0.0; kdj_d: float = 0.0; kdj_j: float = 0.0
    # 涨跌停保护
    is_limit_up: bool = False; is_limit_down: bool = False
    change_pct_5d: float = 0.0
    price_vs_ma20: float = 0.0
    price_vs_ma5: float = 0.0; price_vs_ma10: float = 0.0
    # BOLL布林带
    bb_upper: float = 0.0; bb_middle: float = 0.0; bb_lower: float = 0.0
    bb_width: float = 0.0
    price_vs_bb: str = "middle"

    def update(self, df, code=""):
        close = df["close"].values.astype(float)
        high = df["high"].values.astype(float)
        low = df["low"].values.astype(float)
        volume = df["volume"].values.astype(float)
        self.ma5 = float(np.mean(close[-5:])) if len(close) >= 5 else close[-1]
        self.ma10 = float(np.mean(close[-10:])) if len(close) >= 10 else close[-1]
        self.ma20 = float(np.mean(close[-20:])) if len(close) >= 20 else close[-1]
        self.ma60 = float(np.mean(close[-60:])) if len(close) >= 60 else close[-1]
        self.last_close = float(close[-1])
        self.day_change_pct = (close[-1] - close[-2]) / close[-2] * 100 if len(close) > 1 else 0
        if len(close) >= 15:
            delta = np.diff(close)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            rs = np.mean(gain[-14:]) / np.mean(loss[-14:]) if np.mean(loss[-14:]) > 0 else 100
            self.rsi_14 = 100 - (100 / (1 + rs))
        if len(close) >= 35:
            ema12 = self._ema(close, 12); ema26 = self._ema(close, 26)
            dif = ema12 - ema26
            self.macd_dif = float(dif[-1]) if len(dif) > 0 else 0
            self.macd_dea = float(self._ema(np.array(dif), 9)[-1]) if len(dif) > 0 else 0
        if len(high) >= 15:
            tr_vals = [max(high[i]-low[i], abs(high[i]-close[i-1]) if i > -len(close) else 0, abs(low[i]-close[i-1]) if i > -len(close) else 0) for i in range(-14, 0)]
            self.atr_14 = float(np.mean(tr_vals))
        if len(volume) >= 6:
            self.vol_ratio = float(volume[-1] / np.mean(volume[-6:-1])) if np.mean(volume[-6:-1]) > 0 else 1.0
        self.price_vs_ma5 = (self.last_close - self.ma5) / self.ma5 * 100 if self.ma5 > 0 else 0
        self.price_vs_ma10 = (self.last_close - self.ma10) / self.ma10 * 100 if self.ma10 > 0 else 0
        self.price_vs_ma20 = (self.last_close - self.ma20) / self.ma20 * 100 if self.ma20 > 0 else 0
        if len(close) >= 6:
            obv = sum(volume[i] if close[i] > close[i-1] else (-volume[i] if close[i] < close[i-1] else 0) for i in range(-5, 0))
            self.obv_trend = "up" if obv > 0 else "down" if obv < 0 else "flat"
        self.update_boll(df)
        self.update_kdj_and_limits(df, code)

    def update_boll(self, df):
        """Calculate Bollinger Bands (20-day, 2 std)"""
        close = df["close"].values.astype(float)
        if len(close) < 20: return
        mid = float(np.mean(close[-20:]))
        std = float(np.std(close[-20:]))
        self.bb_upper = mid + 2 * std
        self.bb_middle = mid
        self.bb_lower = mid - 2 * std
        self.bb_width = (self.bb_upper - self.bb_lower) / mid * 100 if mid > 0 else 0
        if self.last_close > self.bb_upper:
            self.price_vs_bb = "above"
        elif self.last_close > self.bb_middle:
            self.price_vs_bb = "upper_half"
        elif self.last_close > self.bb_lower:
            self.price_vs_bb = "lower_half"
        else:
            self.price_vs_bb = "below"

    def update_kdj_and_limits(self, df, code=""):
        """Calculate KDJ and limit up/down protection"""
        close = df["close"].values.astype(float)
        high = df["high"].values.astype(float)
        low = df["low"].values.astype(float)

        if len(close) >= 9:
            n = len(close)
            rsv_list = []
            for i in range(8, n):
                window = close[i-8:i+1]
                h_window = high[i-8:i+1]
                l_window = low[i-8:i+1]
                h9 = float(np.max(h_window))
                l9 = float(np.min(l_window))
                if h9 == l9:
                    rsv_list.append(50.0)
                else:
                    rsv_list.append((close[i] - l9) / (h9 - l9) * 100)
            if rsv_list:
                k_vals = [rsv_list[0]]
                for i in range(1, len(rsv_list)):
                    k_vals.append(k_vals[-1] * 2/3 + rsv_list[i] * 1/3)
                d_vals = [k_vals[0]]
                for i in range(1, len(k_vals)):
                    d_vals.append(d_vals[-1] * 2/3 + k_vals[i] * 1/3)
                self.kdj_k = k_vals[-1]
                self.kdj_d = d_vals[-1]
                self.kdj_j = 3 * self.kdj_k - 2 * self.kdj_d

        if len(close) >= 2:
            daily_change = (close[-1] - close[-2]) / close[-2] * 100
            self.is_limit_up = daily_change >= 9.5
            self.is_limit_down = daily_change <= -9.5

        if len(close) >= 6:
            self.change_pct_5d = (close[-1] - close[-6]) / close[-6] * 100

    def _ema(self, data, period):
        if len(data) < period: return data
        m = 2 / (period + 1); ema = np.empty_like(data); ema[0] = data[0]
        for i in range(1, len(data)): ema[i] = (data[i] - ema[i-1]) * m + ema[i-1]
        return ema
