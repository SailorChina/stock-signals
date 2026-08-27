---
name: tech-signal-FUTU-skill
description: >-
  Multi-market stock technical analysis and buy/sell signal generator.
  Supports US (US.XXXX) stocks. Produces a 5-tier rating (Buy / Overweight / Hold / Underweight / Sell) with
  confidence score, based on deterministic technical indicator calculations (no LLM).
  Features: VCP pattern, event-driven pivot, TD序列, multi-timeframe resonance,
  entry_type (现价/回调/突破入场), sector heat analysis, meme stock tracker.
  Requires: Futu OpenD running (127.0.0.1:11111) for real-time quotes; falls back to akshare.

  Use when the user asks for: 美股推荐, 技术分析, 买卖信号, 股票分析, 信号生成,
  技术面分析, MACD/RSI/KDJ/BOLL分析, 选股, scan, analyze, entry_type.

  Trigger keywords: 推荐美股, 技术分析, 买卖信号, 选股, scan, analyze, 入场, 止损,
  目标价, 交易计划, 美股推荐.
metadata:
  version: 2.16.1
  author: local
allowed-tools: Bash
---

# tech-signal-FUTU-skill

> 美股技术分析 & 买卖信号生成器 | Codex Skill v2.16.1

基于技术指标（MA/MACD/RSI/KDJ/BOLL/ATR/OBV/ADX）+ 高级形态识别（VCP/事件驱动拐点/TD序列/多周期共振），自动生成评级、入场点、止损位和目标价。

**适用市场：美股 (US)**

## CLI 命令

`ash
# 分析单只股票
python -m stock_signals.cli analyze US.NVDA
python -m stock_signals.cli analyze US.AAPL --timeframe 1w

# 全市场扫描
python -m stock_signals.cli scan
python -m stock_signals.cli scan --min-score 55 --max-picks 5 --parallel

# 导出 JSON
python -m stock_signals.cli scan --json --output report.json

# 猫姐 meme 股票追踪
python -m stock_signals.cli meme scan

# 板块热度排名
python -m stock_signals.cli sector --top 10
`

## 功能

1. **K 线获取**: akshare 美股日/周/月 K 线（Futu OpenD 实时价格覆盖）
2. **技术指标**: MA/MACD/RSI/KDJ/BOLL/ATR/OBV/VWMA/ADX
3. **信号识别**: VCP 波动率收缩、事件驱动拐点、TD 序列、多周期共振
4. **交易计划**: 入场区间(entry_type) + 止损 + 双目标 + 风险回报比 + 仓位建议
5. **评分引擎**: 5 维加权（趋势/动量/量能/波动/卖空）+ 动态权重
6. **板块热度**: 21 个美股 ETF 实时热度排名 + 板块加成
7. **Meme 追踪**: 猫姐 watchlist 自动扫描评分

## 入场类型 (entry_type)

扫描结果显式标注入场方式：
- 现价入场: 偏离 < 2%，适合市价直接买入
- 回调入场: 价格低于现价，等待回踩支撑后分批建仓
- 突破入场: 价格高于现价，等待突破阻力后跟进

交易计划文本示例：
- 市价直接入场(现价附近, 偏离 1.0%)
- 回调入场, 等待价格回落至 47.32 (-1.0%) 附近分批建仓

## 过滤规则

- 市值 >= 10B（排除小盘股）
- 价格 > MA200（排除下跌趋势）
- RR >= 2.0
- 基本面：毛利率>=20%（服务类豁免），净利率>=5%，营收增长>=-10%
- phase != decline，alignment != strong_down
- RSI(14) 不超卖（<30，大盘股<25）
- 距52周高点 > 8%（不追高）

## 依赖

- Python 3.10+
- akshare >= 1.18, pandas >= 2.0, numpy >= 1.24
- futu-api >= 10.4.6408（可选，实时报价）
- **Futu OpenD** 运行于 127.0.0.1:11111（需手动启动）
