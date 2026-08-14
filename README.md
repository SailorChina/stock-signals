# stock-signals — 股票技术分析 & 买卖信号生成器

> 支持美股 / A股 / 港股的多时间框架技术分析 skill，基于富途 OpenAPI 获取实时行情数据。

## 功能概览

- **5 级买卖评级**：Buy / Overweight / Hold / Underweight / Sell
- **多时间框架共振**：日线 + 周线 + 月线联动分析
- **支撑阻力位**：基于 swing point 聚类 + 布林带 + 均线检测
- **趋势阶段判断**：吸筹 / 上涨早期 / 上涨 / 派发 / 下跌
- **交易计划生成**：建议买入区间、止损位、目标位、风险收益比
- **五维评分引擎**：趋势(30%) + 动量(25%) + 量能(20%) + 波动率(15%) + 资金面(10%)
- **纯确定性计算**：不依赖 LLM，结果可复现

## 支持的股票市场

| 市场 | 前缀 | 示例 |
|------|------|------|
| 美股 | US. | US.NVDA, US.AAPL, US.DRAM |
| A股 | SH. / SZ. | SH.600519, SZ.000001 |
| 港股 | HK. | HK.00700, HK.00700.HK |

## 安装方法

### 1. 安装富途 OpenAPI

`ash
pip install futu-api>=10.4.6408
`

### 2. 启动富途 OpenD

确保富途牛牛 OpenD 服务正在运行（默认端口 11111）。

### 3. 安装本 Skill

`ash
# 将 skill 复制到 Codex skills 目录
cp -r stock-signals ~/.codex/skills/
`

或在 Codex 中使用：
`
/plugin install SailorChina/stock-signals
`

## 使用方法

### 命令行分析

`ash
# 美股分析
python analyze_signals.py US.NVDA

# 带 JSON 输出
python analyze_signals.py US.NVDA --json

# 周线分析
python analyze_signals.py US.NVDA --timeframe 1w

# A股
python analyze_signals.py SH.600519

# 港股
python analyze_signals.py HK.00700
`

### Codex Skill 调用

直接在 Codex 中输入：
`
/stock-signals:analyze US.DRAM
`

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
| 量能 | 20% | OBV 趋势, 量比, 价量配合度 |
| 波动率 | 15% | BOLL 上下轨 + 带宽, ATR |
| 资金面 | 10% | 特大单/大单/中单/小单净流入, 卖空比例 |

### 多时间框架共振

同时分析日线、周线、月线三个时间框架的评级一致性：

- **strong_up** — 三周期全部看多，强共振，置信度 +15
- **aligned** — 多周期方向一致，共振确认，置信度 +8
- **mixed** — 多周期方向分歧，观望
- **aligned_down** — 多周期看空，共振确认，置信度 -8
- **strong_down** — 三周期全部看空，强共振，置信度 -15

### 支撑/阻力位

- **resistance_1/2**：近期 swing 高点聚类 + 布林带上轨
- **support_1/2**：近期 swing 低点聚类 + 布林带下轨
- **vwap**：20 日成交量加权平均价
- 显示当前价格距各关键位的百分比距离

### 趋势阶段

| 阶段 | 判断条件 | 含义 |
|------|----------|------|
| accumulation | RSI 中性 + 波动率低 + OBV 平稳 | 吸筹阶段，底部整理 |
| early_rally | 价格 > MA200 + MA20 > MA60 | 上涨早期，趋势启动 |
| rally | MA20 > MA60 > MA200 | 上涨阶段，趋势明确 |
| distribution | RSI 高 + 波动率高 + OBV 见顶 | 派发阶段，顶部警示 |
| decline | 价格 << MA200 或 OBV 持续下降 | 下跌阶段，趋势弱势 |

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

`
stock-signals/
* SKILL.md              # Codex skill 定义
* README.md             # 项目说明文档
* .gitignore
* scripts/
    * analyze_signals.py   # 主分析脚本（入口）
    * indicators.py        # 技术指标计算
    * scoring.py           # 五维评分引擎
    * _sr.py               # 支撑阻力 + 交易计划
    * _resonance.py        # 多时间框架共振
`

## 依赖

- Python 3.10+
- pandas
- numpy
- futu-api >= 10.4.6408
- 富途 OpenD 服务运行中（默认 127.0.0.1:11111）

## 免责声明

> 本工具仅供技术参考，不构成任何投资建议。股票市场存在风险，投资需谨慎。请结合自身风险承受能力，结合基本面、消息面综合判断。

## 更新日志

### v2.0.0 (2026-08-14)

- 新增：多时间框架共振分析（日/周/月线）
- 新增：支撑/阻力位检测（swing point 聚类）
- 新增：趋势阶段分类（5 阶段）
- 新增：交易计划生成（入场/止损/目标位）
- 修复：KDJ 金叉/死叉检测逻辑
- 修复：signal_summary 中文编码问题
- 优化：trade plan 入场点选择逻辑

### v1.1.0

- 初始版本：五维评分 + 买卖信号生成
