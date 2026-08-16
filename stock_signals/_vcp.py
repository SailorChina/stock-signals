# -*- coding: utf-8 -*-
"""VCP (Volatility Contraction Pattern) 波动率收缩模式检测
基于 Mark Minervini 的 SEPA 策略
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class VCPResult:
    """VCP 检测结果"""
    detected: bool = False           # 是否检测到 VCP 模式
    contractions: int = 0            # 收缩次数 (2-6次)
    contraction_sizes: List[float] = None  # 每次收缩的幅度 (%)
    pivot_point: float = 0.0        #  pivot 点 (入场价)
    pivot_bar: int = 0               # pivot 发生在第几根K线
    volume_drying: bool = False      # 成交量是否萎缩
    pattern_width: float = 0.0       # 模式总宽度 (%)
    pattern_start_bar: int = 0       # 模式起始位置
    pattern_end_bar: int = 0         # 模式结束位置
    quality: str = "none"            # pattern quality: strong/medium/weak/none
    
    def __post_init__(self):
        if self.contraction_sizes is None:
            self.contraction_sizes = []

def detect_vcp(df, lookback: int = 100, min_contractions: int = 2) -> VCPResult:
    """
    检测 VCP 模式
    
    参数:
        df: K线数据 (需要 open, high, low, close, volume 列)
        lookback: 回溯K线数
        min_contractions: 最少收缩次数 (默认2)
    
    返回:
        VCPResult 对象
    """
    if df is None or len(df) < 30:
        return VCPResult()
    
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    volume = df["volume"].values.astype(float)
    n = len(close)
    
    # 取最近 lookback 根K线
    start = max(0, n - lookback)
    close_slice = close[start:]
    high_slice = high[start:]
    low_slice = low[start:]
    volume_slice = volume[start:]
    
    # 找到局部高点和低点
    swings_high = []
    swings_low = []
    swing_indices = []
    
    window = 5
    for i in range(window, len(close_slice) - window):
        local_high = True
        local_low = True
        for j in range(i - window, i + window + 1):
            if j == i:
                continue
            if close_slice[j] >= close_slice[i]:
                local_high = False
            if close_slice[j] <= close_slice[i]:
                local_low = False
        if local_high:
            swings_high.append((start + i, close_slice[i]))
        if local_low:
            swings_low.append((start + i, close_slice[i]))
    
    if len(swings_high) < 3 or len(swings_low) < 3:
        return VCPResult()
    
    # 检测波动率收缩
    # VCP特征：每次回调幅度约为前一次的一半
    contractions = []
    prev_amplitude = None
    
    # 从高点和低点的交替中检测收缩
    for i in range(1, len(swings_low)):
        if i >= len(swings_high):
            break
        
        # 计算从高点到低点的回撤幅度
        pivot_high_idx, pivot_high_price = swings_high[i - 1]
        pivot_low_idx, pivot_low_price = swings_low[i]
        
        # 计算从低点到下一个高点的反弹幅度
        if i < len(swings_high):
            next_high_idx, next_high_price = swings_high[i]
            
            # 计算当前收缩幅度
            amplitude = (pivot_high_price - pivot_low_price) / pivot_high_price * 100
            
            # 检查是否满足收缩条件 (每次收缩幅度减小)
            if prev_amplitude is not None and amplitude < prev_amplitude * 1.0:
                contractions.append({
                    'idx': i,
                    'amplitude': amplitude,
                    'start_idx': pivot_high_idx,
                    'end_idx': pivot_low_idx,
                    'high_price': pivot_high_price,
                    'low_price': pivot_low_price,
                })
                prev_amplitude = amplitude
    
    # 检查是否有足够的收缩次数
    if len(contractions) < min_contractions:
        return VCPResult()
    
    # 检查成交量是否萎缩 (VCP关键特征)
    # 收缩阶段成交量应逐步减少
    volume_drying = False
    if len(contractions) >= 2:
        vol_ratios = []
        for c in contractions:
            vol_start = max(0, c['start_idx'] - start - 10)
            vol_end = min(len(volume_slice), c['end_idx'] - start + 10)
            if vol_end > vol_start:
                avg_vol = np.mean(volume_slice[vol_start:vol_end])
                vol_ratios.append(avg_vol)
        
        if len(vol_ratios) >= 2:
            # 检查成交量是否总体下降
            if vol_ratios[-1] < vol_ratios[0] * 0.8:
                volume_drying = True
    
    # 确定 pivot 点 (最新高点的阻力位)
    latest_high_idx, latest_high_price = swings_high[-1]
    latest_low_idx, latest_low_price = swings_low[-1]
    
    pivot_point = latest_high_price
    pivot_bar = latest_high_idx
    
    # 计算模式总宽度
    pattern_width = (latest_high_price - latest_low_price) / latest_high_price * 100
    
    # 确定模式边界
    pattern_start_bar = contractions[0]['start_idx'] if contractions else latest_low_idx
    pattern_end_bar = latest_high_idx
    
    # 评估模式质量
    quality = "weak"
    if len(contractions) >= 3 and volume_drying and pattern_width < 20:
        quality = "strong"
    elif len(contractions) >= 2 and pattern_width < 25:
        quality = "medium"
    
    return VCPResult(
        detected=True,
        contractions=len(contractions),
        contraction_sizes=[c['amplitude'] for c in contractions],
        pivot_point=round(pivot_point, 2),
        pivot_bar=pivot_bar,
        volume_drying=volume_drying,
        pattern_width=round(pattern_width, 2),
        pattern_start_bar=pattern_start_bar,
        pattern_end_bar=pattern_end_bar,
        quality=quality,
    )


def detect_vol_contraction_series(close: np.ndarray, lookback: int = 50) -> dict:
    """
    简化版波动率收缩检测，用于快速筛选
    
    返回:
        dict with contraction info
    """
    if len(close) < lookback:
        return {"detected": False, "contractions": 0, "width": 0.0}
    
    slice_close = close[-lookback:]
    slice_high = np.max(slice_close.reshape(-1, 1).T * np.ones_like(slice_close), axis=0)
    
    # 计算滚动波动率
    rolling_vol = []
    for i in range(10, len(slice_close), 10):
        window = slice_close[max(0, i-10):i+10]
        if len(window) > 0:
            vol = np.std(window) / np.mean(window) * 100
            rolling_vol.append(vol)
    
    if len(rolling_vol) < 2:
        return {"detected": False, "contractions": 0, "width": 0.0}
    
    # 检测波动率是否下降
    contraction_count = 0
    for i in range(1, len(rolling_vol)):
        if rolling_vol[i] < rolling_vol[i-1]:
            contraction_count += 1
    
    # 计算模式宽度
    high = np.max(slice_close)
    low = np.min(slice_close[-30:])  # 最近30根K线的低点
    width = (high - low) / high * 100
    
    return {
        "detected": contraction_count >= 2 and width < 25,
        "contractions": contraction_count,
        "width": round(width, 2),
        "vol_trend": "decreasing" if rolling_vol[-1] < rolling_vol[0] else "increasing",
    }
