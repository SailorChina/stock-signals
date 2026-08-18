# stock-signals Skill

股票买卖信号分析系统 — 三市场（A股/港股/美股）技术指标扫描

## 概述

本项目是一个股票技术指标分析系统，支持A股、港股、美股三个市场的扫描和信号识别。

## 核心功能

1. **热门股获取**: 自动获取各市场热门股列表
2. **K线数据**: 获取日K线数据（支持复权）
3. **技术指标**: 计算MA/MACD/RSI/KDJ/BOLL/ATR/OBV等
4. **信号识别**: 识别金叉/死叉、超买/超卖、突破等信号
5. **智能评分**: 综合评分给出5级评级

## 数据源 (v2.1)

- **A股**: Sina K线API + akshare fallback
- **港股**: akshare daily
- **美股**: akshare daily

## 使用方式

```bash
# 运行扫描
python run_scan.py

# Python API
from stock_signals.hot_fetcher import fetch_hot_stocks
from stock_signals.indicators import fetch_kline, compute_indicators
from stock_signals.scoring import compute_rating
```

## 性能

- 300只A股扫描: ~75秒
- 缓存命中: ~0.2秒 (17倍加速)
- 无外部API Key依赖

## 依赖

- Python 3.10+
- akshare >= 1.18
- pandas >= 2.0
- numpy >= 1.24
