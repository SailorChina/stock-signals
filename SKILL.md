# tech-signal-skill Skill

> 美股技术分析 & 买卖信号生成器 | Codex Skill v2.14.3

基于技术指标（MA/MACD/RSI/KDJ/BOLL/ATR/OBV/ADX）+ 高级形态识别（VCP/事件驱动拐点/TD序列/多周期共振），自动生成评级、入场点、止损位和目标价。

**适用市场：美股 (US) — 已移除 A 股和港股支持\n\n## 板块热度分析\n\n`ash\n# 查看板块热度排名\npython -m stock_signals.cli sector\npython -m stock_signals.cli sector --top 10 --json\n`\n\n- 21个美股板块ETF实时热度排名\n- 热门板块股票评分加成 +10%，冷僻板块 -5%\n- 数据源: Sina 实时报价 + akshare 历史K线**

## 功能

1. **K 线获取**: akshare 获取美股日/周/月 K 线数据（支持前复权）
2. **技术指标计算**: MA/MACD/RSI/KDJ/BOLL/ATR/OBV/VWMA/ADX
3. **信号识别**: VCP 波动率收缩、事件驱动拐点、TD 序列、多周期共振
4. **交易计划**: 支撑阻力聚类 + 入场区间 + 止损 + 双目标 + 风险回报比
5. **评分引擎**: 5 维加权（趋势/动量/量能/波动/卖空）+ 动态权重

## Meme 股票追踪 (v2.11.1)

`ash
python -m stock_signals.cli meme list
python -m stock_signals.cli meme add US.NVDA
python -m stock_signals.cli meme scan
`

- 默认 watchlist 包含猫姐常提的10只股票
- meme 股票评分加成 +5%
- 自动抓取接口预留（X/Twitter + YouTube）

## 数据源

- **K 线**: akshare `stock_us_daily`
- **热门股**: Sina 成交量排序，静态池 335 只蓝筹 (>=10B市值)
- **卖空比例**: futu-api（可选）

## 使用方式

```bash
# 安装
pip install -e .

# 分析单只股票
python -m stock_signals.cli analyze US.NVDA
python -m stock_signals.cli analyze US.AAPL --timeframe 1w

# 全市场扫描
python -m stock_signals.cli scan
python -m stock_signals.cli scan --min-score 55 --max-picks 5 --parallel

# 导出
python -m stock_signals.cli scan --json --output report.json
python -m stock_signals.cli analyze US.NVDA --csv results.csv
```

```python
# Python API
from stock_signals.indicators import fetch_kline, compute_indicators
from stock_signals.scoring import compute_rating
from stock_signals._resonance import compute_timeframe_resonance
from stock_signals._sr import compute_support_resistance, generate_trade_plan

df = fetch_kline('US.NVDA', '1d', 300)
ind = compute_indicators(df, 'US.NVDA', '1d')
result = compute_rating(ind)
resonance = compute_timeframe_resonance('US.NVDA', ind)
sr = compute_support_resistance(df)
plan = generate_trade_plan(ind, sr)
```

## 性能

- 扫描 300 只热股: ~2-5 分钟（串行）/ ~30-60 秒（并行）
- 单只分析: ~0.2s（缓存命中）
- 无需外部 API Key

## 过滤规则 (v2.14.1)

- 市值 >= 100亿美金 (10B)（排除小盘股）
- 价格 > MA200（排除下跌趋势）
- RR >= 2.0（风险回报比）
- 基本面：毛利率>=20% 或 服务类公司，净利率>=5%，营收增长>=-10%
- phase != decline，alignment != strong_down
- RSI(14) 不在超卖区间（<30，大盘股<25）
- 距52周高点 > 8%（不追高）

## 依赖

- Python 3.10+
- akshare >= 1.18
- pandas >= 2.0
- numpy >= 1.24

## BUG 修复 (v2.14.3)
- 修复 screener.py:330 格式化字符串 BUG（.1f 被当作字符串拼接）
- 修复 fundamental.py symbol 前缀 BUG（akshare 需要纯代码）
- 全面扫描验证所有过滤规则正确工作

## v2.14.3 更新
- 静态池从166扩充到335只，覆盖更多行业（房地产、公用事业、材料）
- 移除 screener.py 中的假ticker（US.AAB-UEF）
- 市值门槛统一为100亿美元（>=10B）
- 热门池从190扩充到279只真实大市值股票
