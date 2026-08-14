---
name: stock-signals
description: >-
  Multi-market stock technical analysis and buy/sell signal generator.
  Supports US (US.XXXX), A-share (SH.600519 / SZ.000001), and HK (HK.00700) stocks.
  Produces a 5-tier rating (Buy / Overweight / Hold / Underweight / Sell) with
  confidence score, based on deterministic technical indicator calculations (no LLM).

  Features (v2.0):
  - Multi-timeframe resonance analysis (daily/weekly/monthly alignment)
  - Support/resistance level detection (swing points + BOLL + MA clusters)
  - Trend phase classification (accumulation/early_rally/rally/distribution/decline)
  - Trade plan generation (entry zone, stop loss, targets, risk-reward ratio)
  - 5-dimension scoring (trend/momentum/volume/volatility/capital)
  - Buy/sell signal generation with confidence levels

  Use when the user asks for: 买卖信号, 技术分析, 技术指标, 趋势判断, 买入卖出建议,
  股票分析, 信号生成, 技术面分析, MACD/RSI/KDJ/BOLL分析, or any request for
  structured buy/hold/sell signals from a stock symbol.

  Trigger keywords: analyze, signals, technical analysis, 买卖信号, 技术分析,
  股票分析, 信号, MACD, RSI, KDJ, 布林带, 趋势, 买入, 卖出, 持仓建议.
metadata:
  version: 2.0.0
  author: local
allowed-tools: Bash
---

# Stock Signals v2.0 — 股票技术分析 & 买卖信号生成

## 使用方法

```bash
# 美股
python analyze_signals.py US.NVDA
python analyze_signals.py US.NVDA --json          # JSON 输出
python analyze_signals.py US.NVDA --timeframe 1w  # 周线分析

# A股
python analyze_signals.py SH.600519
python analyze_signals.py SZ.000001

# 港股
python analyze_signals.py HK.00700
```

## 输出说明

### 评级 (Rating)
5 级评级：Buy / Overweight / Hold / Underweight / Sell
综合得分 0-100，置信度 high/medium/low

### 五维评分 (5-Dimension Scoring)
| 维度 | 权重 | 指标 |
|------|------|------|
| 趋势 | 30% | MA5/10/20/60/120/200, 金叉/死叉, 均线排列, 价格偏离度 |
| 动量 | 25% | RSI(6/12/14/24), MACD(DIF/DEA/Hist), KDJ(K/D/J) |
| 量能 | 20% | OBV趋势, 量比, 价量配合 |
| 波动率 | 15% | BOLL上下轨+带宽, ATR |
| 资金面 | 10% | 特大单/大单/中单/小单净流入, 卖空比例 |

### 多时间框架共振 (v2.0)
同时分析日线/周线/月线三个时间框架的评级一致性：
- **strong_up**: 三周期全部看多，强共振，置信度+15
- **aligned**: 多周期方向一致，共振确认，置信度+8
- **mixed**: 多周期方向分歧，观望
- **strong_down**: 三周期全部看空，强共振，置信度-15
- **aligned_down**: 多周期看空，共振确认，置信度-8

### 支撑/阻力位 (v2.0)
- **resistance_1/2**: 近期swing高点聚类 + BOLL上轨
- **support_1/2**: 近期swing低点聚类 + BOLL下轨
- 显示当前价格距各关键位的百分比

### 趋势阶段 (v2.0)
根据价格相对MA200距离、RSI、OBV、波动率等综合判断：
- accumulation（吸筹）/ early_rally（上涨早期）/ rally（上涨）
- distribution（派发）/ decline（下跌）

### 交易计划 (v2.0)
- **entry_zone**: 建议买入区间（最近支撑位/MA20/VWAP中最高者）
- **stop_loss**: 止损位（次级支撑下方或2xATR）
- **target_1/2**: 目标位（阻力位 + ATR扩展）
- **risk_reward_ratio**: 风险收益比
- **position_size_pct**: 建议仓位比例

## 依赖
- Python 3.10+, pandas, numpy, futu-api >= 10.4.6408
- Futu OpenD 运行中（默认 127.0.0.1:11111）
