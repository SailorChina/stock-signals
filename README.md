# stock-signals v2.8.0 — 多市场股票技术分析 & 买卖信号生成器

基于富途 OpenAPI 的多时间框架技术分析 skill，支持美股 / A股 / 港股实时扫描与选股。

> **36/36 单元测试全部通过** | GitHub: [SailorChina/stock-signals](https://github.com/SailorChina/stock-signals)

---

## 核心功能

### 技术指标
| 指标 | 说明 |
|------|------|
| MA/EMA | 5/10/20/60/120/200 日均线，金叉/死叉检测 |
| MACD | DIF/DEA/Hist，金叉/死叉，背离检测 |
| RSI | 6/12/14/24 周期，超买超卖判断 |
| KDJ | K/D/J 三线，超买超卖 |
| BOLL | 布林带上中下轨 + 宽度 |
| ATR | 14周期真实波幅，动态止损 |
| OBV | 能量潮，资金流向判断 |
| ADX | 趋势强度（+DI/-DI），趋势 vs 震荡分类 |
| VWMA | 成交量加权均线 |

### 高级信号
| 信号 | 说明 |
|------|------|
| **VCP** 波动率收缩 | Mark Minervini SEPA 策略，检测2-6次收缩循环 + 量能萎缩 |
| **Episodic Pivot** 事件性转折 | Kristjan Qullamaggie 策略，跳空高开 + 量能放大突破 |
| **TD Sequential** 9转信号 | 9连阴买入 / 9连阳卖出，Turn 确认反转 |
| **多时间框架共振** | 日/周/月线联动评分，共振看多 +8 分 |
| **趋势阶段判断** | 吸筹 / 上涨早期 / 上涨 / 派发 / 下跌 |
| **支撑阻力位** | Swing Point 聚类 + VWAP + 布林带 |
| **ATR 动态止损** | 1.5×ATR 止损 + 7.5% 硬上限（Minervini 规则） |
| **RS 相对强度** | 1-99 相对强度评分，RS≥90 加5分 |

### 智能过滤（v2.5+）
| 规则 | 阈值 | 效果 |
|------|------|------|
| RSI 极端超买 | RSI(14) > 75 | 硬拦截 |
| 距高点过近 | > -2% | 拦截追高 |
| MA5/MA20 延伸 | > 8% | 拦截过度延伸 |
| 风险收益比 | RR < 2.0 | 硬拦截 |
| TD 卖出 Turn | sell_turn | 跳过 |
| MACD 看跌背离 | bearish | 跳过 |
| 看跌K线形态 | 吞没/流星线 | 跳过 |

### 黑名单过滤（v2.7+）
- 自动过滤银行股（A股/港股/美股）和 ETF
- 涵盖 SPY/QQQ/VTI 等主流 ETF 及 JPM/BAC/工行/中行 等银行

### 动态热门股（v2.8+）
- 扫描时自动从 Futu API 获取每日热门股 TOP 100
- 与静态池合并去重，补充候选股票
- API 超时自动降级，不影响扫描

---

## 快速开始

### 1. 环境准备
```bash
pip install futu-api>=10.4.6408 pandas numpy
# 启动富途 OpenD（默认端口 11111）
```

### 2. 安装 Skill
```bash
cp -r stock-signals ~/.codex/skills/
```

---

## 使用方法

### analyze — 分析单只/多只股票
```bash
python -m stock_signals.cli analyze US.NVDA
python -m stock_signals.cli analyze US.QCOM --timeframe 1w
python -m stock_signals.cli analyze SH.600519
python -m stock_signals.cli analyze HK.00700
python -m stock_signals.cli analyze US.NVDA US.AAPL --json
python -m stock_signals.cli analyze US.NVDA US.AAPL --csv results.csv
```

### scan — 智能选股（推荐）
```bash
# 交互式选择市场（推荐）
python -m stock_signals.cli scan

# 命令行指定市场
python -m stock_signals.cli scan --markets US
python -m stock_signals.cli scan --markets A
python -m stock_signals.cli scan --markets HK
python -m stock_signals.cli scan --markets US,HK

# 调整参数
python -m stock_signals.cli scan --markets US --min-score 55 --max-picks 5
python -m stock_signals.cli scan --markets US --json --output report.json
```

**参数说明：**
| 参数 | 默认 | 说明 |
|------|------|------|
| `--markets, -m` | A,US,HK | 市场：A=沪深, US, HK |
| `--min-score` | 60.0 | 推荐门槛（越高越严格） |
| `--max-picks` | 3 | 每市场最多推荐数 |
| `--delay` | 1.0 | API 间隔（秒） |
| `--json, -j` | - | JSON 格式输出 |
| `--output, -o` | - | 保存结果到文件 |

---

## 输出解读

### analyze 输出
显示评级、综合得分、五维评分条、技术指标详情、多时间框架共振、交易计划（入场/止损/目标/RR比/仓位）、入场条件提示、风险提示。

### scan 输出示例
```
============================================================
  每日股票推荐报告  2026-08-16
============================================================
  扫描时间: 2026-08-16 21:46:38
  分析 43 只 | 推荐 5 只 | 观察 0 只

────────────────────────────────────────────────────────────
  美股
────────────────────────────────────────────────────────────
  推荐（5只）:
  1. US.MU 美光科技 · 存储芯片  现价: 971.66
      评级: Overweight (偏多) · 分: 63.5 · 共振: 共振看多
      入场: 890.05 (-8.4%)  止损: 923.08 (-5.0%)
      目标1: 1132.16 (+16.5%)  目标2: 1327.07 (+36.6%)
      风险回报: 4.5:1  仓位建议: 3.0%
      等待条件: MACD金叉确认，多头动能较强 | OBV资金持续流入
      指标: MA5/MA10 金叉, MACD 金叉, OBV 上升，资金流入
```

---

## 每日使用流程

```bash
# 1. 扫描推荐
python -m stock_signals.cli scan --markets US --min-score 55 --max-picks 5

# 2. 深入分析感兴趣的股票
python -m stock_signals.cli analyze US.QCOM
python -m stock_signals.cli analyze US.MU --timeframe 1w

# 3. 保存报告
python -m stock_signals.cli scan --markets US --json --output daily_scan.json
```

---

## 技术架构

```
stock_signals/
├── __init__.py          # 包入口，版本 v2.8.0
├── cli.py               # 命令行接口 (analyze/scan)
├── indicators.py        # 技术指标计算
├── scoring.py           # 五维评分引擎
├── screener.py          # 筛选引擎 (股票池+热门股+黑名单)
├── reporter.py          # 报告生成器
├── _sr.py               # 支撑阻力位 + 交易计划
├── _resonance.py        # 多时间框架共振
├── _vcp.py              # VCP 波动率收缩检测
├── _episodic_pivot.py   # Episodic Pivot 检测
├── _info.py             # 股票信息库 (中文名/板块/简介)
└── config.py            # 配置管理
```

---

## 常见问题

**Q: 连接失败 `Connection refused to 127.0.0.1:11111`**
A: 启动富途 OpenD 服务。

**Q: API 限流**
A: 增加 `--delay` 参数，如 `--delay 1.5`。

**Q: 无推荐股票**
A: 降低 `--min-score` 到 50 或扫描更大范围。

**Q: 热门股获取失败**
A: 自动降级到静态池，不影响扫描。

---

## 免责声明

本工具仅供技术参考，不构成任何投资建议。股票市场存在风险，投资需谨慎。
