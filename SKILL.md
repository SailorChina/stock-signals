---
name: stock-signals
description: >-
  Multi-market stock technical analysis and buy/sell signal generator.
  Supports US (US.XXXX), A-share (SH.600519 / SZ.000001), and HK (HK.00700) stocks.
  Produces a 5-tier rating (Buy / Overweight / Hold / Underweight / Sell) with
  confidence score, based on deterministic technical indicator calculations (no LLM).

  Features (v2.3.3):
  - Multi-timeframe resonance analysis (daily/weekly/monthly alignment)
  - Support/resistance level detection (swing points + BOLL + MA clusters)
  - Trend phase classification (accumulation/early_rally/rally/distribution/decline)
  - Trade plan generation (entry zone, stop loss, targets, risk-reward ratio)
  - 5-dimension scoring (trend/momentum/volume/volatility/capital)
  - TD Sequential (9转信号): buy/sell setup + Turn detection
  - ADX trend strength (+DI/-DI directional bias)
  - MACD/RSI divergence detection
  - Candlestick patterns (engulfing, shooting star, etc.)
  - Gap analysis (up/down gap + fill status)
  - Volatility regime classification (low/normal/high)
  - Smart stock screener: auto-scan 3 markets, recommend best entry opportunities
  - K-line caching and API retry
  - All Chinese text output
  - Batch analysis and CSV export

  Use when the user asks for: 买卖信号, 技术分析, 技术指标, 趋势判断, 买入卖出建议,
  股票分析, 信号生成, 技术面分析, MACD/RSI/KDJ/BOLL分析, 股票筛选, 选股, 9转信号,
  或任何需要结构化买卖信号/多市场推荐的请求.

  Trigger keywords: analyze, signals, technical analysis, 买卖信号, 技术分析,
  股票分析, 信号, MACD, RSI, KDJ, 布林带, 趋势, 买入, 卖出, 持仓建议, scan, 筛选, 选股.
metadata:
  version: 2.3.3
  author: SailorChina
allowed-tools: Bash
---

# Stock Signals v2.3.3 — 股票技术分析 & 买卖信号生成

## 使用方法

```bash
# ── analyze 子命令：分析单只/多只股票 ──────────────────────────────
python -m stock_signals.cli analyze US.NVDA
python -m stock_signals.cli analyze US.NVDA --json
python -m stock_signals.cli analyze US.NVDA --timeframe 1w
python -m stock_signals.cli analyze SH.600519
python -m stock_signals.cli analyze HK.00700
python -m stock_signals.cli analyze US.NVDA US.AAPL SH.600519 --json
python -m stock_signals.cli analyze US.NVDA US.AAPL --csv results.csv

# ── scan 子命令：多市场智能选股 ────────────────────────────────────
python -m stock_signals.cli scan                    # 交互式选择市场
python -m stock_signals.cli scan --markets US       # 只扫美股
python -m stock_signals.cli scan --markets A        # 只扫A股
python -m stock_signals.cli scan --markets HK       # 只扫港股
python -m stock_signals.cli scan --markets A,US,HK  # 全市场
python -m stock_signals.cli scan --min-score 55 --max-picks 5
python -m stock_signals.cli scan --json --output report.json
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
| 量能 | 20% | OBV趋势, 量比, 量价配合 |
| 波动率 | 15% | BOLL上下轨, 带宽, ATR |
| 资金面 | 10% | 特大单/大单/中单/小单净流入, 卖空比例 |

### 多时间框架共振 (v2.0)
同时分析日线/周线/月线三个时间框架的评级一致性：
- **strong_up**: 三周期全部看多，强共振，置信度+15
- **aligned**: 多周期方向一致，共振确认，置信度+8
- **mixed**: 多周期方向分歧，观望
- **strong_down**: 三周期全部看空，强共振，置信度-15
- **aligned_down**: 多周期看空，共振确认，置信度-8

### TD Sequential (9转信号) v2.3
- **TD买入序列**: 连续9根收盘价低于4根前 → 超卖反转
- **TD卖出序列**: 连续9根收盘价高于4根前 → 超买反转
- **TD Turn**: 第10根打破序列方向 → 反转确认信号

### ADX趋势强度 v2.3
- ADX>40: 强趋势 | ADX 25-40: 中等 | ADX<25: 震荡市
- +DI/-DI 判断多空方向

### 支撑/阻力位 (v2.0)
- **resistance_1/2**: 近期swing高点聚类 + BOLL上轨
- **support_1/2**: 近期swing低点聚类 + BOLL下轨
- 显示当前价格距各关键位的百分比

### 趋势阶段 (v2.0)
- accumulation（吸筹）/ early_rally（上涨早期）/ rally（上涨）
- distribution（派发）/ decline（下跌）

### 交易计划 (v2.0)
- **entry_zone**: 建议买入区间
- **stop_loss**: 止损位
- **target_1/2**: 目标位
- **risk_reward_ratio**: 风险收益比
- **position_size_pct**: 建议仓位

### scan 选股报告
- 每市场1-5只推荐 + 观察名单
- 含入场区间、止损、目标、风险收益比、推荐理由
- 支持 JSON 输出和文件保存

## 依赖
- Python 3.10+, pandas, numpy, futu-api >= 10.4.6408
- Futu OpenD 运行中（默认 127.0.0.1:11111）
