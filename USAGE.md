# tech-signal-skill 使用文档

## 快速开始

### 前置条件
1. 安装富途 OpenD（[install-futu-opend skill](https://github.com/SailorChina/install-futu-opend)）
2. 确保 OpenD 运行在 `127.0.0.1:11111`
3. Python 3.10+ 环境

### 安装
```bash
git clone https://github.com/SailorChina/tech-signal-skill.git
cd tech-signal-skill
pip install -e ".[dev]"
```

---

## 核心命令

### 1. 分析单只股票
```bash
# 美股
python -m stock_signals.cli analyze US.NVDA
python -m stock_signals.cli analyze US.QCOM

# A股
python -m stock_signals.cli analyze SH.600519
python -m stock_signals.cli analyze SZ.000001

# 港股
python -m stock_signals.cli analyze HK.00700

# 周线/月线分析
python -m stock_signals.cli analyze US.NVDA --timeframe 1w
python -m stock_signals.cli analyze SH.600519 --timeframe 1m

# JSON 输出（适合程序调用）
python -m stock_signals.cli analyze US.NVDA --json

# 批量分析
python -m stock_signals.cli analyze US.NVDA US.QCOM SH.600519 --json

# 导出 CSV
python -m stock_signals.cli analyze US.NVDA US.AAPL --csv results.csv
```

### 2. 智能选股扫描
```bash
# 交互式选择市场（推荐）
python -m stock_signals.cli scan

# 指定市场
python -m stock_signals.cli scan --markets US    # 美股
python -m stock_signals.cli scan --markets A     # A股
python -m stock_signals.cli scan --markets HK    # 港股

# 全市场
python -m stock_signals.cli scan --markets A,US,HK

# 调整参数
python -m stock_signals.cli scan --min-score 55 --max-picks 5 --delay 1.5

# JSON 输出
python -m stock_signals.cli scan --markets US --json --output report.json
```

---

## 股票代码格式

| 市场 | 前缀 | 示例 |
|------|------|------|
| 美股 | `US.` | `US.NVDA`, `US.QCOM`, `US.MU` |
| A股-沪 | `SH.` | `SH.600519`, `SH.688981` |
| A股-深 | `SZ.` | `SZ.000001`, `SZ.300750` |
| 港股 | `HK.` | `HK.00700` (腾讯), `HK.09988` (快手) |

---

## 输出解读

### analyze 输出
```
================================================================
  US.QCOM  技术分析 & 买卖信号
  时间: 2026-08-14 00:00:00
================================================================

  评级: Overweight (偏多)
  综合得分: 59.8/100
  置信度: medium (中)

  各维度评分
    趋势: [████████░░░░░░░░] 52  (40%)
      价格低于MA60 5.1%; MA5/MA10 金叉
    动量: [███████████░░░░░] 72  (30%)
      MACD柱为正，多头动能; MACD金叉
    量能: [███████████░░░░░] 70  (15%)
      OBV上升，资金持续流入
    波动率: [███████░░░░░░░░░] 45  (10%)
      ATR=3.66，波动较大
    资金面: [██████████░░░░░░] 65  (5%)
      特大单流入、小单流出

  技术指标
    最新价: 165.79  MA5=162.13 MA10=158.42 MA20=155.30 MA60=174.20
    MACD: DIF=-1.2469 DEA=-2.2511 Hist=2.0084
    RSI:  14=57.1
    KDJ:  K=76.5 D=66.8 J=96.1
    BOLL: 上=170.35 中=155.01 下=139.68
    ADX:  23.4  +DI=1.3 -DI=0.8 (多)
    9转信号: TD卖出序列完成(第9根)

  多时间框架共振
    日线: Overweight (60.6)  周线: Hold (55.5)  月线: Hold (50.0)
    共振: aligned (共振看多)  置信度调整: +8

  交易计划
    建议入场: 165.70
    止损位:   152.99
    第一目标: 242.48
    第二目标: 255.18
    风险收益比: 7.0:1
    建议仓位:   3.0%
```

### scan 输出
```
============================================================
  每日股票推荐报告  2026-08-15
============================================================
  扫描时间: 2026-08-15 22:22:46
  分析 43 只 | 推荐 5 只 | 观察 0 只

────────────────────────────────────────────────────────────
  美股
────────────────────────────────────────────────────────────
  推荐（5只）:
  1. US.LLY  价格: 1180.16
      评级: Overweight (偏多) · 分: 64.8 · 共振: 共振看多
      入场: 1177.50  止损: 1096.13  目标1: 1215.56  目标2: 1296.93  RR: 1.5:1
      理由: 回调入场机会(距高点-5.4%), MA5/MA10 金叉, MACD 金叉

  2. US.MU  价格: 971.66
      评级: Overweight (偏多) · 分: 61.5 · 共振: 共振看多
      入场: 890.05  止损: 825.91  目标1: 1132.16  目标2: 1262.10  RR: 5.8:1
      理由: MA5/MA10 金叉, MACD 金叉, OBV 上升，资金流入

  ...
```

---

## v2.5.0 新特性

### 智能过滤（自动拦截追高风险股）
| 过滤规则 | 阈值 | 效果 |
|---------|------|------|
| RSI 极端超买 | RSI(14) > 75 | 硬拦截 |
| 距高点过近 | 距离 > -2% | 拦截追高 |
| MA5/MA20 延伸 | 偏离 > 8% | 拦截过度延伸 |
| MA60 偏离超买 | 价格 > MA60 +10% | 扣分 |
| MA60 健康位置 | -5% ≤ 偏离 ≤ 5% | 加分 |

### 回调入场评分
| 条件 | pullback_score | 说明 |
|------|---------------|------|
| 距高点 -5%~-15%，RSI<65 | +5 | 回调到位 |
| 距高点 -15%~-30%，RSI<55 | +10 | 健康回调 |

### MACD 金叉成熟度
| 金叉距今 | 加分 | 说明 |
|---------|------|------|
| ≤2 根 | +5 | 刚发生，谨慎追高 |
| 3-10 根 | +8 | 已确认，趋势稳健 |
| >10 根 | +3 | 可能衰减 |

---

## 扫描策略建议

### 每日早盘前（推荐流程）
```bash
# 第一步：全市场快速扫描
python -m stock_signals.cli scan --min-score 55 --max-picks 5

# 第二步：对感兴趣的股票深入分析
python -m stock_signals.cli analyze US.QCOM
python -m stock_signals.cli analyze US.MU --timeframe 1w

# 第三步：保存报告
python -m stock_signals.cli scan --markets US --json --output daily_scan.json
```

### 参数调整指南
| 参数 | 保守 | 激进 | 说明 |
|------|------|------|------|
| `--min-score` | 65 | 50 | 评分门槛，越高越严格 |
| `--max-picks` | 3 | 10 | 每市场推荐数 |
| `--delay` | 1.5 | 0.5 | API间隔（秒），越少越快但易限流 |

### 注意
- 富途 API 限制：30秒内最多 60 次请求
- 扫描 43 只美股约需 3-5 分钟
- 首次运行需要安装富途 OpenD

---

## 常见问题

### Q: 连接失败
```
Connection refused to 127.0.0.1:11111
```
**A:** 启动富途 OpenD 服务。

### Q: API 限流
```
获取K线失败: 获取历史K线频率太高
```
**A:** 增加 `--delay` 参数，如 `--delay 1.5`。

### Q: 无推荐股票
**A:** 当前市场可能没有符合条件的股票，降低 `--min-score` 到 50 或扫描更大范围。

### Q: 股票不在池中
**A:** 当前仅包含指数成分股精选，如需分析其他股票请使用 `analyze` 命令直接查询。

---

## 免责声明

本工具仅供技术参考，不构成任何投资建议。股票市场存在风险，投资需谨慎。请结合自身风险承受能力，结合基本面、消息面综合判断。
