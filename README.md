# stock-signals v2.3.3 — 股票技术分析 & 买卖信号生成器

支持美股 / A股 / 港股的多时间框架技术分析 skill，基于富途 OpenAPI 获取实时行情数据。

## 功能概览

- **5 级买卖评级**: Buy / Overweight / Hold / Underweight / Sell
- **多时间框架共振**: 日线 + 周线 + 月线联动分析
- **支撑阻力位**: 基于 swing point 聚类 + 布林带 + 均线检测
- **趋势阶段判断**: 吸筹 / 上涨早期 / 上涨 / 派发 / 下跌
- **交易计划生成**: 建议买入区间、止损位、目标位、风险收益比
- **五维评分引擎**: 趋势(30%) + 动量(25%) + 量能(20%) + 波动率(15%) + 资金面(10%)
- **TD Sequential (9转信号)**: 买入/卖出序列检测 + Turn确认
- **ADX趋势强度**: 趋势跟踪 vs 震荡市判断
- **MACD/RSI背离检测**: 价格与动量分歧警示
- **K线形态识别**: 吞没、射击之星等
- **缺口分析**: 向上/向下缺口 + 回补状态
- **波动率市况分类**: 低/正常/高波动率自动判断
- **智能股票筛选器**: 多市场自动扫描，推荐最佳入场机会
- **纯确定性计算**: 不依赖 LLM，结果可复现
- **API 重试 & K线缓存**: 网络不稳定时自动重试，本地缓存加速
- **批量分析 & CSV 导出**: 一次分析多只股票
- **完善日志系统**: 结构化日志输出

## 支持的市场

| 市场 | 前缀 | 示例 |
|------|------|------|
| 美股 | US. | US.NVDA, US.AAPL, US.DRAM |
| A股 | SH. / SZ. | SH.600519, SZ.000001 |
| 港股 | HK. | HK.00700, HK.00700.HK |

## 安装方法

### 1. 安装富途 OpenAPI

```bash
pip install futu-api>=10.4.6408
```

### 2. 启动富途 OpenD

确保富途牛牛 OpenD 服务正在运行（默认端口 11111）。

### 3. 安装本 Skill

```bash
# 复制 skill 到 Codex skills 目录
cp -r stock-signals ~/.codex/skills/
```

或在 Codex 中使用：
```
/plugin install SailorChina/stock-signals
```

## 使用方法

### 子命令说明

```
python -m stock_signals.cli {analyze,scan} [选项]
```

### analyze — 分析单只/多只股票

```bash
# 美股分析
python -m stock_signals.cli analyze US.NVDA

# JSON 输出
python -m stock_signals.cli analyze US.NVDA --json

# 周线分析
python -m stock_signals.cli analyze US.NVDA --timeframe 1w

# A股
python -m stock_signals.cli analyze SH.600519

# 港股
python -m stock_signals.cli analyze HK.00700

# 批量分析
python -m stock_signals.cli analyze US.NVDA US.AAPL SH.600519 --json

# 导出 CSV
python -m stock_signals.cli analyze US.NVDA US.AAPL --csv results.csv
```

### scan — 多市场智能选股（新功能）

自动扫描候选股票池，筛选出技术面最佳的入场机会。

**交互式模式**（推荐）— 无参数时弹出菜单：

```bash
python -m stock_signals.cli scan
```

```
  请选择扫描市场:
  [1] A股（沪深核心龙头）
  [2] 港股（恒生+恒生科技）
  [3] 美股（道指+标普500+纳指）
  [4] 全部市场

  输入选项 (1/2/3/4):
```

**命令行模式** — 指定市场跳过交互：

```bash
# 只扫美股
python -m stock_signals.cli scan --markets US

# 只扫A股
python -m stock_signals.cli scan --markets A

# 只扫港股
python -m stock_signals.cli scan --markets HK

# 全市场扫描
python -m stock_signals.cli scan --markets A,US,HK
```

**参数说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--markets, -m` | A,US,HK | 市场列表，逗号分隔 |
| `--min-score` | 60.0 | 最低评分门槛（>=此分才推荐） |
| `--max-picks` | 3 | 每个市场最多推荐数 |
| `--delay` | 0.5 | API请求间隔（秒），避免限速 |
| `--json, -j` | - | JSON格式输出 |
| `--output, -o` | - | 保存结果到文件 |

**筛选逻辑：**
- 硬门槛：综合评分 >= min_score，多周期共振 aligned/strong_up
- 加分项：MA金叉、MACD金叉、9转买入完成、OBV上升、风险收益比>=2:1
- 排序：评分高优先，同分共振强优先，上涨趋势阶段优先

**输出示例：**
```
============================================================
  每日股票推荐报告  2026-08-15
============================================================
  扫描时间: 2026-08-15 20:30:00
  分析 58 只 | 推荐 3 只 | 观察 5 只

  ────────────────────────────────────────────────────────
  美股
  ────────────────────────────────────────────────────────
  1. US.NVDA  价格: 132.50
      评级: Buy (买入) · 分: 78.5 · 共振: 强共振看多
      趋势: 上涨阶段
      入场: 128.00  止损: 122.50  目标1: 145.00  目标2: 155.00  RR: 3.2:1
      理由: MA5/MA10 金叉, MACD 金叉, OBV 上升，资金流入

  2. US.AAPL  价格: 225.30
      评级: Overweight (偏多) · 分: 68.2 · 共振: 共振看多
      趋势: 上涨早期
      ...
```

## Python 库调用

```python
from stock_signals import fetch_kline, compute_indicators, compute_rating
from stock_signals import compute_timeframe_resonance, compute_support_resistance, generate_trade_plan
from stock_signals.screener import scan, ScanConfig

# 获取 K 线
df = fetch_kline("US.NVDA", "1d", num=300)

# 计算指标
ind = compute_indicators(df, "US.NVDA", "1d")

# 计算评级
rating = compute_rating(ind, {}, None)
print(rating["rating"])  # "Buy" / "Overweight" / "Hold" / "Underweight" / "Sell"

# 多市场扫描
cfg = ScanConfig(min_score=60, max_per_market=3, max_delay=0.6)
result = scan(markets=["US"], config=cfg)
```

## 输出说明

### 评级体系

| 评级 | 分数范围 | 含义 |
|------|----------|------|
| Buy | 70-100 | 强烈买入信号，技术指标全面向好 |
| Overweight | 60-70 | 偏多，可逢低布局 |
| Hold | 40-60 | 中性震荡，观望为主 |
| Underweight | 30-40 | 偏空，注意风险 |
| Sell | 0-30 | 强烈卖出信号，建议止损离场 |

### 五维评分

| 维度 | 权重 | 核心指标 |
|------|------|----------|
| 趋势 | 30% | MA5/10/20/60/120/200 排列，金叉/死叉，价格偏离度 |
| 动量 | 25% | RSI(6/12/14/24), MACD(DIF/DEA/Hist), KDJ(K/D/J) |
| 量能 | 20% | OBV 趋势, 量比, 量价配合度 |
| 波动率 | 15% | BOLL 上下轨 + 带宽, ATR |
| 资金面 | 10% | 特大单/大单/中单/小单净流入, 卖空比例 |

### 多时间框架共振

同时分析日线、周线、月线三个时间框架的评级一致性：

- **strong_up** — 三周期全部看多，强共振，置信度 +15
- **aligned** — 多周期方向一致，共振确认，置信度 +8
- **mixed** — 多周期方向分歧，观望
- **aligned_down** — 多周期看空，共振确认，置信度 -8
- **strong_down** — 三周期全部看空，强共振，置信度 -15

### TD Sequential (9转信号) v2.3

- **TD买入序列**: 连续9根收盘价低于4根前 → 超卖反转信号
- **TD卖出序列**: 连续9根收盘价高于4根前 → 超买反转信号
- **TD Turn**: 第10根打破序列方向 → 反转确认
- 输出中显示：`[9转信号] TD买入序列完成(第9根)，当前计数=9`

### ADX趋势强度 v2.3

- ADX > 40: 强趋势，适合趋势跟踪
- ADX 25-40: 中等趋势，可跟踪
- ADX < 25: 低趋势，震荡市，慎用趋势策略
- +DI/-DI 方向判断多头/空头占优

### 支撑/阻力位

- **resistance_1/2**: 近期 swing 高点聚类 + 布林带上轨
- **support_1/2**: 近期 swing 低点聚类 + 布林带下轨
- **vwap**: 20 日成交量加权平均价
- 显示当前价格距各关键位的百分比距离

### 趋势阶段

| 阶段 | 判断条件 | 含义 |
|------|----------|------|
| accumulation | RSI 中性 + 波动率低 + OBV 平稳 | 吸筹阶段，底部整理 |
| early_rally | 价格 > MA200 + MA20 > MA60 | 上涨早期，趋势启动 |
| rally | MA20 > MA60 > MA200 | 上涨阶段，趋势明确 |
| distribution | RSI 高 + 波动率高 + OBV 见顶 | 派发阶段，顶部警示 |
| decline | 价格 << MA200 或 OBV 持续下降 | 下跌阶段，趋势走弱 |

### 交易计划

| 参数 | 说明 |
|------|------|
| entry_zone | 建议买入区间（最近支撑/MA20/VWAP 中最高者） |
| stop_loss | 止损位（次级支撑下方或 2xATR） |
| target_1 | 第一目标位（阻力位） |
| target_2 | 第二目标位（ATR 扩展） |
| risk_reward_ratio | 风险收益比，建议 > 2:1 |
| position_size_pct | 建议仓位比例 |

## 文件结构

```
stock-signals/
  pyproject.toml           # Python 包配置 (v2.3.3)
  README.md                # 项目说明文档
  SKILL.md                 # Codex skill 定义
  .gitignore
  stock_signals/
    __init__.py            # 包入口，公开 API
    config.py              # 配置系统
    indicators.py          # 技术指标计算 + K线获取 + 缓存
    scoring.py             # 五维评分引擎
    screener.py            # 多市场股票筛选器 (v2.3.2)
    reporter.py            # 推荐报告生成器 (v2.3.2)
    _resonance.py          # 多时间框架共振
    _sr.py                 # 支撑阻力 + 交易计划
    cli.py                 # 命令行入口 (analyze + scan 子命令)
  tests/
    test_stock_signals.py  # 单元测试 (17 tests)
```

## 依赖

- Python 3.10+
- pandas
- numpy
- futu-api >= 10.4.6408
- 富途 OpenD 服务运行中（默认 127.0.0.1:11111）

## 版本历史

### v2.3.3 (2026-08-15)
- **新增**: scan 命令交互式市场选择菜单（1.A股/2.港股/3.美股/4.全部）
- **改进**: CLI 重构为 analyze/scan 双子命令结构

### v2.3.2 (2026-08-15)
- **新增**: 多市场智能选股器（screener.py）
- **新增**: 每日推荐报告生成器（reporter.py）
- **新增**: scan 子命令，支持 --markets/--min-score/--max-picks/--delay 参数
- **新增**: A股/港股/美股三大市场股票池（约240只核心标的）
- **修复**: TD Sequential 计算逻辑缺失问题
- **修复**: cli.py 重复显示问题

### v2.3.1 (2026-08-15)
- **新增**: TD Sequential (9转信号) 买入/卖出序列 + Turn确认
- **修复**: TD计算逻辑缺失导致的测试失败
- **修复**: CLI输出重复显示问题

### v2.3.0 (2026-08-15)
- **新增**: ADX趋势强度指标（+DI/-DI方向判断）
- **新增**: MACD/RSI背离检测
- **新增**: K线形态识别（吞没、射击之星等）
- **新增**: 缺口分析（向上/向下缺口 + 回补状态）
- **新增**: 波动率市况分类（低/正常/高）
- **新增**: 动态权重调整（根据波动率市况）
- **新增**: 7个新单元测试

### v2.2.1 (2026-08-15)
- 全部CLI输出改为中文
- 提取模块级常量（颜色/中文标签映射）

### v2.2.0 (2026-08-14)
- 版本统一 + 中文输出

### v2.1.0 (2026-08-15)
- **新增**: Python 包结构重构 (stock_signals/)
- **新增**: 配置系统 (config.py)
- **新增**: K线数据缓存 (本地 pickle 缓存，5 分钟 TTL)
- **新增**: API 自动重试 (最多 3 次，指数退避)
- **新增**: 结构化日志系统 (logging)
- **新增**: 批量分析模式 (支持多股票代码)
- **新增**: CSV 导出功能 (--csv 参数)
- **新增**: 单元测试 (pytest)
- **新增**: pyproject.toml 标准化打包
- **改进**: 代码类型注解完善
- **改进**: 错误处理优化

### v2.0.0 (2026-08-14)
- 新增：多时间框架共振分析（日/周/月线）
- 新增：支撑阻力位检测（swing point 聚类）
- 新增：趋势阶段分类（5 阶段）
- 新增：交易计划生成（入场/止损/目标位）
- 修复：KDJ 金叉/死叉检测逻辑
- 修复：signal_summary 中文编码问题
- 优化：trade plan 入场点选择逻辑

### v1.1.0
- 初始版本：五维评分 + 买卖信号生成

## 免责声明

> 本工具仅供技术参考，不构成任何投资建议。股票市场存在风险，投资需审慎。请结合自身风险承受能力，结合基本面、消息面综合判断。
