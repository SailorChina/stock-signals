---
name: stock-signals
description: >-
  多市场股票技术分析 & 买卖信号生成器。支持美股(US.XXXX)、A股(SH.600519/SZ.000001)、港股(HK.00700)。
  生成5级评级(Buy/Overweight/Hold/Underweight/Sell)及置信度分数，基于确定性技术指标计算(无LLM)。

  功能(v2.4.0):
  - 多时间框架共振分析(日线/周线/月线联动)
  - 支撑阻力位检测(swing点聚类+BOLL+均线)
  - 趋势阶段分类(吸筹/上涨早期/上涨/派发/下跌)
  - 交易计划生成(入场区间、止损、目标位、风险收益比)
  - 五维评分引擎(趋势30%+动量25%+量能20%+波动率15%+资金面10%)
  - TD Sequential(9转信号): 买入/卖出序列检测 + Turn确认
  - ADX趋势强度: +DI/-DI方向判断
  - MACD/RSI背离检测
  - K线形态识别(吞噬、射击之星等)
  - 缺口分析(向上/向下缺口+回补状态)
  - 波动率市况分类(低/正常/高波动率自动判断)
  - 智能股票筛选器: 多市场自动扫描，推荐最佳入场机会
  - K线缓存 & API重试
  - 全中文输出
  - 批量分析 & CSV导出

  适用场景: 用户询问买卖信号、技术分析、技术指标、趋势判断、买入卖出建议、
  股票分析、信号生成、MACD/RSI/KDJ/BOLL分析、股票筛选、选股、9转信号、
  或任何需要结构化买卖信号/多市场推荐的请求。

  触发关键词: analyze, signals, technical analysis, 买卖信号, 技术分析,
  股票分析, 信号, MACD, RSI, KDJ, 布林带, 趋势, 买入, 卖出, 持仓建议, scan, 筛选, 选股.
metadata:
  version: 2.4.0
  author: SailorChina
allowed-tools: Bash
---

# Stock Signals v2.4.0 — 股票技术分析 & 买卖信号生成

## 使用方法

### analyze — 分析单只/多只股票

```bash
# 分析单只美股
python -m stock_signals.cli analyze US.NVDA

# JSON输出
python -m stock_signals.cli analyze US.NVDA --json

# 周线分析
python -m stock_signals.cli analyze US.NVDA --timeframe 1w

# A股分析
python -m stock_signals.cli analyze SH.600519
python -m stock_signals.cli analyze SZ.000001

# 港股分析
python -m stock_signals.cli analyze HK.00700

# 批量分析多只
python -m stock_signals.cli analyze US.NVDA US.AAPL SH.600519 --json

# 导出CSV
python -m stock_signals.cli analyze US.NVDA US.AAPL --csv results.csv
```

### scan — 多市场智能选股（推荐每日使用）

```bash
# 交互式选择市场（推荐）
python -m stock_signals.cli scan

# 只扫描美股
python -m stock_signals.cli scan --markets US

# 只扫描A股
python -m stock_signals.cli scan --markets A

# 只扫描港股
python -m stock_signals.cli scan --markets HK

# 全市场扫描
python -m stock_signals.cli scan --markets A,US,HK

# 调整参数
python -m stock_signals.cli scan --min-score 55 --max-picks 5 --delay 1.5
python -m stock_signals.cli scan --json --output report.json
```

## 股票代码格式

| 市场 | 前缀 | 示例 |
|------|------|------|
| 美股 | US. | US.NVDA, US.AAPL, US.DRAM |
| A股-沪 | SH. | SH.600519, SH.688981 |
| A股-深 | SZ. | SZ.000001, SZ.300750 |
| 港股 | HK. | HK.00700, HK.09988 |

## 输出说明

### 评级 (Rating)
5级评级：Buy / Overweight / Hold / Underweight / Sell
综合得分 0-100，置信度 high/medium/low

### 五维评分
| 维度 | 权重 | 指标 |
|------|------|------|
| 趋势 | 30% | MA5/10/20/60/120/200, 金叉/死叉, 均线排列, 价格偏离度 |
| 动量 | 25% | RSI(6/12/14/24), MACD(DIF/DEA/Hist), KDJ(K/D/J) |
| 量能 | 20% | OBV趋势, 量比, 量价配合 |
| 波动率 | 15% | BOLL上下轨, 带宽, ATR |
| 资金面 | 10% | 特大单/大单/中单/小单净流入, 卖空比例 |

### 多时间框架共振
同时分析日线/周线/月线三个时间框架的评级一致性：
- **strong_up**: 三周期全部看多，强共振，置信度+15
- **aligned**: 多周期方向一致，共振确认，置信度+8
- **mixed**: 多周期方向分歧，观望
- **strong_down**: 三周期全部看空，强共振，置信度-15
- **aligned_down**: 多周期看空，共振确认，置信度-8

### TD Sequential (9转信号)
- **TD买入序列**: 连续9根收盘价低于4根前收盘 → 超卖反转
- **TD卖出序列**: 连续9根收盘价高于4根前收盘 → 超买反转
- **TD Turn**: 第10根打破序列方向 → 反转确认信号

### ADX趋势强度
- ADX>40: 强趋势 | ADX 25-40: 中等 | ADX<25: 震荡市
- +DI/-DI 判断多空方向

### 支撑/阻力位
- **resistance_1/2**: 近期swing高点聚类 + BOLL上轨
- **support_1/2**: 近期swing低点聚类 + BOLL下轨
- 显示当前价格距各关键位的百分比

### 趋势阶段
- accumulation（吸筹）/ early_rally（上涨早期）/ rally（上涨）
- distribution（派发）/ decline（下跌）

### 交易计划
| 参数 | 说明 |
|------|------|
| entry_zone | 建议买入区间（最近支撑/MA20/VWAP中最高者） |
| stop_loss | 止损位（次级支撑下方或2xATR） |
| target_1 | 第一目标位（阻力位） |
| target_2 | 第二目标位（ATR扩展） |
| risk_reward_ratio | 风险收益比，建议>2:1 |
| position_size_pct | 建议仓位比例 |

### scan 选股报告
- 每市场1-5只推荐 + 观察名单
- 含入场区间、止损、目标、风险收益比、推荐理由
- 支持 JSON 输出和文件保存

## 依赖
- Python 3.10+, pandas, numpy, futu-api >= 10.4.6408
- Futu OpenD 运行中（默认 127.0.0.1:11111）

## 日常使用建议

### 每日早盘前（9:00-9:30）
```bash
# 全市场扫描，找当天机会
python -m stock_signals.cli scan --markets A,US,HK --min-score 55 --max-picks 5

# 或只扫感兴趣的市场
python -m stock_signals.cli scan --markets US --min-score 60 --max-picks 3
```

### 关注个股时
```bash
# 分析你持有的股票
python -m stock_signals.cli analyze SH.600519
python -m stock_signals.cli analyze US.NVDA --timeframe 1w

# 批量分析候选池
python -m stock_signals.cli analyze US.NVDA US.AAPL US.TSLA --json
```

### 导出报告
```bash
# 保存扫描结果到JSON
python -m stock_signals.cli scan --markets US --json --output daily_scan.json

# 导出分析结果到CSV
python -m stock_signals.cli analyze US.NVDA US.AAPL --csv analysis.csv
```

## 注意事项
- Futu OpenD 必须运行才能获取实时数据
- API限制：30秒内最多60次请求，扫描时会自动限速
- 结果仅供技术参考，不构成投资建议
- 部分港股代码可能需要完整格式（如 HK.00700.HK）
