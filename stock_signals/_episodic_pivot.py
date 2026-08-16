# -*- coding: utf-8 -*-
"""Episodic Pivot (事件性转折) 检测
基于 Kristjan Qullamaggie 的突破策略
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class EpisodicPivot:
    """事件性转折检测结果"""
    detected: bool = False
    gap_up_pct: float = 0.0      # 跳空高开幅度
    volume_spike: float = 0.0    # 成交量放大倍数
    catalyst_score: float = 0.0  # 催化剂评分
    breakout_valid: bool = False  # 突破是否有效
    entry_zone: float = 0.0      # 入场区间
    stop_loss: float = 0.0       # 止损位
    quality: str = "none"        # 质量: strong/medium/weak/none

def detect_episodic_pivot(df, lookback: int = 60) -> EpisodicPivot:
    """
    检测事件性转折 (Episodic Pivot)
    
    特征:
    1. 突然跳空高开 (>2%)
    2. 成交量放大 (>2倍平均)
    3. 突破近期阻力位
    4. 价格收盘在日内高点附近
    
    返回:
        EpisodicPivot 对象
    """
    if df is None or len(df) < 30:
        return EpisodicPivot()
    
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    volume = df["volume"].values.astype(float)
    n = len(close)
    
    if n < lookback:
        return EpisodicPivot()
    
    recent = close[-lookback:]
    recent_vol = volume[-lookback:]
    
    # 1. 检测跳空高开
    prev_close = close[-2] if n >= 2 else close[-1]
    gap_up_pct = 0.0
    if prev_close > 0:
        gap_up_pct = (close[-1] - prev_close) / prev_close * 100
    
    # 2. 检测成交量放大
    avg_vol = np.mean(recent_vol)
    curr_vol = volume[-1]
    volume_spike = curr_vol / avg_vol if avg_vol > 0 else 1.0
    
    # 3. 检测突破阻力位
    recent_high = np.max(recent)
    breakout_valid = close[-1] >= recent_high * 0.98
    
    # 4. 检测收盘位置
    day_range = high[-1] - low[-1]
    close_position = (close[-1] - low[-1]) / day_range if day_range > 0 else 0.5
    
    # 综合评分
    catalyst_score = 0.0
    if gap_up_pct > 2:
        catalyst_score += 30
    elif gap_up_pct > 1:
        catalyst_score += 15
    if volume_spike > 2:
        catalyst_score += 30
    elif volume_spike > 1.5:
        catalyst_score += 15
    if breakout_valid:
        catalyst_score += 20
    if close_position > 0.8:
        catalyst_score += 20
    
    # 确定结果
    detected = catalyst_score >= 50 and gap_up_pct > 1.5 and volume_spike > 1.5
    quality = "weak"
    if catalyst_score >= 80 and gap_up_pct > 3:
        quality = "strong"
    elif catalyst_score >= 60:
        quality = "medium"
    
    # 计算入场区间和止损
    atr = np.mean(np.abs(high - low)[-14:]) if len(high) >= 14 else 0
    entry_zone = round(close[-1], 2)
    stop_loss = round(close[-1] - 1.5 * atr, 2) if atr > 0 else round(close[-1] * 0.95, 2)
    
    return EpisodicPivot(
        detected=detected,
        gap_up_pct=round(gap_up_pct, 2),
        volume_spike=round(volume_spike, 2),
        catalyst_score=round(catalyst_score, 1),
        breakout_valid=breakout_valid,
        entry_zone=entry_zone,
        stop_loss=stop_loss,
        quality=quality,
    )
