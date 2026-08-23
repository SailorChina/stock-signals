# stock-signals

> **Codex Skill: 美股技术分析 & 买卖信号生成器**

基于技术指标（MA/MACD/RSI/KDJ/BOLL/ATR/OBV/ADX）+ 高级形态识别（VCP/事件驱动拐点/TD序列/多周期共振），自动生成评级、入场点、止损位和目标价。

**适用市场：美股 (US)**

## 快速开始

```bash
# 分析单只股票
python -m stock_signals.cli analyze US.NVDA
python -m stock_signals.cli analyze US.AAPL --timeframe 1w

# 全市场扫描（默认43只精选 + 300只热股 + 板块热度分析）
python -m stock_signals.cli scan
python -m stock_signals.cli scan --min-score 55 --max-picks 5 --parallel

# 导出 JSON / CSV
python -m stock_signals.cli scan --json --output report.json
python -m stock_signals.cli analyze US.NVDA --csv results.csv
```

## 核心功能

### 技术指标引擎

| 指标 | 说明 |
|------|------|
| MA/EMA | 5/10/20/60/120/200 日均线，金叉/死叉检测 |
| MACD | DIF/DEA/柱状图，金叉/死叉，背离检测 |
| RSI | 6/12/14/24 周期，超买超卖判断 |
| KDJ | K/D/J 三线，超买超卖 |
| BOLL | 布林带上中下轨 + 宽度 |
| ATR | 14 周期真实波幅，动态止损 |
| OBV | 能量潮，资金流向判断 |
| VWMA | 成交量加权均线 |
| ADX | 趋势强度，+DI/-DI 方向 |

### 高级信号

| 信号 | 说明 |
|------|------|
| **VCP** 波动率收缩 | Mark Minervini SEPA 策略，检测 2-6 次收缩周期 |
| **事件驱动拐点** | Kristjan Qullamaggie 策略，跳空高开 + 放量突破 |
| **TD 序列** | 9 连跌买入 / 9 连涨卖出 |
| **多周期共振** | 日/周/月线对齐评分，置信度加成 |
| **支撑/阻力** | Swing Point 聚类 + BOLL + MA 聚类 + VWAP |
| **趋势阶段分类** | 吸筹 / 上涨早期 / 上涨阶段 / 派发 / 下跌 |
| **交易计划生成** | 入场区间、止损、双目标、风险回报比、仓位建议 |

### 板块热度分析 (v2.11.0)

- 21个美股板块ETF实时热度排名
- 基于1d/5d/20d/60d涨幅加权计算热度分
- 热门板块加成（+10%）、冷僻板块扣分（-5%）
- 自动识别股票所属板块

### 智能过滤 (v2.5.0+)

- RSI(14) > 75 → 追高硬拦截
- 距高点距离 > -2% → 拦截追高
- MA5/MA20 偏离 > 8% → 评分下调
- MACD 金叉成熟度 → 加分/扣分
- 回踩入场评分 → pullback_score 优先级排序

## 数据源

| 数据 | 来源 |
|------|------|
| K 线 | akshare `stock_us_daily`（daily/weekly/monthly） |
| 热门股 | Sina 成交量排序，静态池 300 只蓝筹 |
| 卖空比例 | futu-api（可选） |

内存缓存：K 线按 `{code}_{num}` 缓存，命中 ~0.2s。

## 项目结构

```
stock_signals/
+- __init__.py            # v2.11.0，核心 API 导出
+- _info.py               # 股票信息库（英文名/行业/描述）
+- _resonance.py          # 多周期共振分析（日/周/月）
+- _sr.py                 # 支撑阻力计算 + 交易计划生成
+- _vcp.py                # VCP 波动率收缩检测
+- _episodic_pivot.py     # 事件驱动拐点检测
+- indicators.py          # 通用指标计算 (MA/MACD/RSI/KDJ/BOLL/ATR/OBV/VWMA/ADX)
+- scoring.py             # 通用评分引擎（趋势/动量/量能/波动/卖空，5 维加权）
+- screener.py            # 并行扫描引擎（43 只静态池 + 300 只热股）
+- sector.py              # 板块热度分析（ETF排名 + 板块加成）
+- meme_tracker.py       # 网红/大V 股票追踪（猫姐 watchlist + 自动抓取接口）
+- hot_fetcher.py         # 热门股获取（Sina 成交量排序）
+- cli.py                 # CLI 入口 (analyze/scan 子命令)
+- reporter.py            # 中文扫描报告输出
+- config.py              # 配置管理（缓存/TTL/重试）
+- data_sources.py        # 数据源接口封装
+- dynamic_pool.py        # 动态股票池管理
+- us/                    # 美股子模块（独立于主模块）
   +- indicators_us.py     # 美股专用指标
   +- scoring_us.py        # 美股专用评分
   +- screener_us.py       # 美股专用扫描
   +- backtest_us.py       # 美股回测
   +- optimize_us.py       # 参数优化
   +- us_pool_full.txt     # 300 只蓝筹完整列表
tests/
+- test_stock_signals.py  # 单元测试
backtest_v2.py             # 独立回测脚本
pyproject.toml             # 项目配置
```

## 安装

```bash
pip install -e .
```

依赖：
- Python >= 3.10
- pandas >= 2.0
- numpy >= 1.24
- akshare >= 1.18（K 线数据，必须）
- futu-api >= 10.4.6408（卖空数据，可选）

## 使用

### CLI

`ash
# 猫姐 Meme 股票追踪
python -m stock_signals.cli meme list        # 查看 watchlist
python -m stock_signals.cli meme add US.NVDA  # 添加股票
python -m stock_signals.cli meme remove US.NVDA  # 移除股票
python -m stock_signals.cli meme scan         # 分析所有 meme 股票
python -m stock_signals.cli meme scrape       # 尝试自动抓取（需网络）

# 板块热度排名
python -m stock_signals.cli sector
`

```bash
# 分析单只股票
python -m stock_signals.cli analyze US.NVDA
python -m stock_signals.cli analyze US.AAPL --timeframe 1w
python -m stock_signals.cli analyze US.NVDA --timeframe 1m

# 全市场扫描（默认美股）
python -m stock_signals.cli scan
python -m stock_signals.cli scan --markets US
python -m stock_signals.cli scan --min-score 55 --max-picks 5 --parallel

# 导出
python -m stock_signals.cli scan --json --output report.json
python -m stock_signals.cli analyze US.NVDA --csv results.csv
```

### Python API

```python
from stock_signals.indicators import fetch_kline, compute_indicators
from stock_signals.scoring import compute_rating
from stock_signals._resonance import compute_timeframe_resonance
from stock_signals._sr import compute_support_resistance, generate_trade_plan
from stock_signals.screener import scan_parallel, ScanConfig

# 获取 K 线
df = fetch_kline('US.NVDA', ktype='1d', num=300)

# 计算指标
ind = compute_indicators(df, 'US.NVDA', '1d')

# 评分
result = compute_rating(ind)
print(f"评级: {result['rating']}, 评分: {result['score']:.1f}")

# 多周期共振
resonance = compute_timeframe_resonance('US.NVDA', ind)
print(f"共振: {resonance.alignment}, 置信度加成: {resonance.confidence_boost}")

# 支撑阻力 + 交易计划
sr = compute_support_resistance(df)
plan = generate_trade_plan(ind, sr)
print(f"入场: {plan['entry']:.2f}, 止损: {plan['stop_loss']:.2f}")
print(f"目标1: {plan['target_1']:.2f}, 目标2: {plan['target_2']:.2f}")
print(f"风险回报比: {plan['risk_reward']:.1f}:1")
```

## 评级体系

| 评级 | 分数区间 | 含义 |
|------|----------|------|
| Buy | 75-100 | 强力买入 |
| Overweight | 60-74 | 优于大盘 |
| Hold | 40-59 | 观望持有 |
| Underweight | 25-39 | 弱于大盘 |
| Sell | 0-24 | 建议卖出 |

## 动态权重 (v2.6.0+)

根据波动率 regime 自动调整维度权重：
- 低波动：动量/量能权重增加，趋势权重降低
- 高波动：趋势/动量权重增加，量能/卖空权重降低

## 测试

```bash
python -m unittest tests.test_stock_signals
```

## v2.13.0 (2026-08-23)
- **趋势质量硬过滤**: 新增 4 项过滤规则，过滤下跌趋势股票
  - phase=decline 的硬过滤（价格远低于MA200的下跌阶段）
  - lignment=strong_down 的硬过滤（多头排列被破坏）
  - RSI<30 的硬过滤（超卖接飞刀风险）
  - 价格低于MA200超过20% 的硬过滤（趋势过弱）
- 过滤效果: 删除 FMC/HST/POOL/ZTS 等下跌趋势股票推荐
- 推荐质量提升: 所有推荐股票均为 accumulation/early_rally 阶段，strong_up 对齐

## 更新日志

### v2.11.0 (2026-08-21)
- **移除 A 股和港股支持，专注美股**
- 修复 `today_hot` UnboundLocalError BUG（扫描崩溃）
- 修复 `fetch_realtime` 语法错误（删除 A/HK 分支后遗留 elif）
- 清理所有 A 股/港股相关死代码和注释
- CLI 简化：去掉 --strategy 选项，默认美股扫描
- 版本号更新

### v2.8.5
- CLI 支持并行扫描（--parallel 提速 3-5 倍）
- 智能过滤系统：RSI/偏离/MACD 成熟度/回踩入场

### v2.5.0
- VCP 波动率收缩检测（Minervini SEPA）
- 事件驱动拐点检测（Qullamaggie）
- 多周期共振分析（日/周/月对齐）
- 支撑阻力聚类 + 交易计划生成

### v2.1
- 移除 Futu OpenAPI K 线依赖，改用 akshare 单数据源
- 新增内存缓存机制（命中率 ~0.2s）

## 免责声明

本工具仅供技术分析参考，不构成投资建议。股市投资有风险，请根据自身风险承受能力综合判断，独立决策。
