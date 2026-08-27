# tech-signal-skill

> **Codex Skill: 美股技术分析 & 买卖信号生成器**

基于技术指标（MA/MACD/RSI/KDJ/BOLL/ATR/OBV/ADX）+ 高级形态识别（VCP/事件驱动拐点/TD序列/多周期共振），自动生成评级、入场点、止损位和目标价。

**适用市场：美股 (US)**

## 快速开始

```bash
# 分析单只股票
python -m stock_signals.cli analyze US.NVDA
python -m stock_signals.cli analyze US.AAPL --timeframe 1w

# 全市场扫描（默认静态池 + 动态热门池（335只，10B市值门槛） + 板块热度分析）
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

| 过滤规则 | 阈值 | 效果 |
|---------|------|------|
| RSI(14) > 75 | 超买硬拦截 | 过滤追高股 |
| 距高点距离 > -2% | 拦截追高 | 过滤接近52周高点股 |
| MA5/MA20 偏离 > 8% | 评分下调 | 过滤过度延伸 |
| MACD 金叉成熟度 | 加分/扣分 | 新金叉谨慎，已确认加分 |
| 回踩入场评分 | pullback_score | 回调到位优先排序 |
| 价格 < MA200 | v2.14.1 硬拦截 | 过滤下跌趋势股 |
| RR < 2.0 | v2.14.1 硬拦截 | 过滤风险回报不足 |
| phase=decline | v2.13 硬拦截 | 过滤下跌阶段 |
| alignment=strong_down | v2.13 硬拦截 | 过滤强空头共振 |
| RSI(14) < 30 | v2.13 硬拦截 | 过滤超卖接飞刀(大盘股<5000亿放宽到25) |
| 基本面过滤 | v2.14.1 新增 | 毛利率≥20%, 净利率≥5%, 营收增长≥-10% |

### 基本面过滤 (v2.14.1 新增)

通过 akshare 获取美股财务指标，自动过滤财务质量差的股票：
- 毛利率 < 20% → 过滤（服务类公司如V/MA/SPGI毛利率100%自动豁免）
- 净利率 < 5% → 过滤
- 营收同比增长 < -10% → 过滤
- 数据不可用时放行（避免误杀）

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

## v2.13.2 (2026-08-23)
- **趋势质量硬过滤**: 新增 4 项过滤规则，过滤下跌趋势股票
  - phase=decline 的硬过滤（价格远低于MA200的下跌阶段）
  - lignment=strong_down 的硬过滤（多头排列被破坏）
  - RSI<30 的硬过滤（超卖接飞刀风险，大盘股MC>=5000亿跳过，中盘股MC>=1000亿放宽到25）
  - 价格低于MA200超过10% 的硬过滤（趋势过弱，从20%收紧）
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



## 专业选股建议 (v2.14)

### 市值分层策略
- **巨无霸 (>=500B)**: 防御性配置，低波动，如 AAPL, MSFT, NVDA
- **大盘 (200-500B)**: 核心持仓，稳定增长，如 AMZN, META, JPM
- **中大盘 (100-200B)**: 主力选股池，平衡风险收益，如 PGR, SPGI, HLT
- **中盘 (50-100B)**: 成长性机会，需严格过滤，如 UBER, MU, NXPI
- **小盘 (<50B)**: 高风险，不建议作为主力（本次已过滤）

### 当前配置
- MIN_MARKET_CAP = 50B（排除小盘股）
- 候选池：107 只
- 过滤后推荐：2-5 只高质量标的

### 未来改进方向
1. 集成实时基本面数据（PE、营收增长、利润率）
2. 增加板块轮动策略
3. 添加流动性筛选
4. 支持多因子评分（技术+基本面+资金流向）

详见 [PROFESSIONAL_GUIDE.md](PROFESSIONAL_GUIDE.md)


## v2.14.0 (2026-08-23)
- **小盘股过滤**: 最小市值从 10B 提升到 50B，排除小盘股风险
- **基本面过滤**: 新增毛利率、净利率、营收增长检查
- **新增模块**: fundamental.py - 基本面数据获取与过滤
- **推荐质量提升**: 过滤更多低质量股票


## 入场类型说明

扫描报告中的入场类型：

| 类型 | 含义 | 操作 |
|------|------|------|
| [现价附近入场] | 强股，可市价买入 | 直接买入 |
| [等待回调入场] | 普通股，等回踩支撑 | 挂单买入 |
| [突破入场] | 等突破阻力 | 条件单买入 |

判断标准：
- 强股：MACD金叉 + OBV上升 + RSI 50-70
- 普通股：等待支撑位（MA20/VWAP/支撑1）

## 交易计划解读

每只推荐股票包含：
- 入场价：建议买入价位
- 止损位：风险控制的退出价位
- 目标1/2：分批止盈价位
- 风险回报比：收益/风险比例，建议 >= 2:1
- 仓位建议：单笔建议仓位占比

## v2.14.1 (2026-08-24)
- **MA200 过滤收紧**: 价格低于 MA200 直接硬拦截（之前是低于10%才过滤）
- **目标1 风险回报检查**: 整体 RR < 2.0 时硬拦截（之前是<1.5）
- **RSI6 超买警告**: RSI6 > 75 时输出警告
- **基本面过滤生效**: 修复 check_fundamental 导入但未调用的 BUG，现在正确过滤财务质量差的股票
  - 毛利率≥20%、净利率≥5%、营收增长≥-10%
  - 服务类公司（V/MA/SPGI等毛利率100%）自动豁免
- **筛选效果**: 过滤更多低质量股票，推荐质量提升

## v2.14.2 (2026-08-24)
- **BUG 修复 - 格式化字符串**: 修复 screener.py 第330行 .1f 被当作字符串拼接的 BUG
  - 修复前: 日志输出 价格低于MA200 .1f%（.1f 被当作文本）
  - 修复后: 日志正确输出 价格低于MA200 -4.3%
- **BUG 修复 - 基本面过滤 Symbol 前缀**: 修复 fundamental.py 中 akshare 接口调用参数格式错误
  - akshare 需要纯代码（如 AAPL），不接受 US.AAPL 格式
  - 修复: 添加 symbol.replace('US.', '').replace('.', '')
- **全面 BUG 扫描**: 对所有 Python 文件进行静态分析和运行时测试
  - 发现并修复 2 个关键 BUG
  - 验证所有过滤规则（MA200/RR/基本面/RSI/phase）正确工作


## v2.15.0 (2026-08-25)
- **Futu OpenD 实时报价集成**: 新增 utu_api.py 模块，通过 Futu OpenD 获取美股实时价格
- **修正 akshare 数据滞后问题**: 扫描时自动用实时价格覆盖 akshare 历史收盘价
  - 解决 MA200 过滤误杀问题（如 PGR 因昨日收盘价低于 MA200 被错误过滤）
  - 修正 52 周高低点距离计算
  - 修正 trend_template_pass 判断
- **Futu API 状态**: OpenD 运行于 127.0.0.1:11111，订阅 QUOTE 类型后获取实时报价
- **回退机制**: Futu 连接失败时自动回退到 akshare，不影响扫描流程



## v2.16.1 (2026-08-27)
- **入场类型字段 (entry_type)**: 扫描结果中显式标注入场方式
  - `现价入场`: 价格偏离 < 2%, 适合市价直接买入
  - `回调入场`: 价格低于当前市价, 等待回踩支撑后分批建仓
  - `突破入场`: 价格高于当前市价, 等待突破阻力后跟进
- **交易计划文本优化**: 买入策略说明增加偏离幅度
  - 示例: `市价直接入场(现价附近, 偏离 1.0%)`
  - 示例: `回调入场, 等待价格回落至 47.32 (-1.0%) 附近分批建仓`

## v2.16.0 (2026-08-25)
- **Futu API 批处理优化**: 改用 get_market_snapshot 批量获取实时报价（25只/批，0.3秒间隔）
  - 300只股票扫描时间从 ~2.5分钟 降至 ~6秒（25倍提速）
  - 批次间隔 0.3s 避免 Futu OpenD 限流
- **市值门槛调整**: MIN_MARKET_CAP 从 50B 降至 10B（用户要求），扩大选股范围
- **股票池扩充**: hot_fetcher.py 静态池从 ~100只扩充至 179只，补充缺失的市值数据
  - 新增医疗/工业/保险/国际制药等板块市值数据
  - 静态池 + 动态热门池合并后约 166只（通过10B过滤）
- **SCAN 性能**: 300只股票扫描估算
  - 首次连接: 2.0s（连接缓存后不再重复）
  - 批量获取: 12批 x 0.3s = 3.6s
  - 总计: ~6秒（cached），~8.6秒（首次）
- **hot_fetcher.py 清理**: 移除重复的 fetch_hot_stocks 函数定义

## 详细使用文档

参见 [USAGE.md](USAGE.md) 获取完整的命令参考、参数说明和常见问题。

### 每日推荐流程

`ash
# 1. 早盘前扫描（并行模式，3-5分钟）
python -m stock_signals.cli scan --markets US --max-picks 10 --parallel

# 2. 对感兴趣的股票深入分析
python -m stock_signals.cli analyze US.PGR
python -m stock_signals.cli analyze US.MU --timeframe 1w

# 3. 查看猫姐追踪股票
python -m stock_signals.cli meme scan

# 4. 查看板块热度
python -m stock_signals.cli sector
`

### 参数速查

| 参数 | 默认值 | 说明 |
|------|--------|------|
| --markets | US | 市场: US/A/HK 或组合 |
| --min-score | 55 | 最低评分门槛 |
| --max-picks | 10 | 每市场最大推荐数 |
| --parallel | 否 | 并行扫描（提速3-5倍） |
| --delay | 1.0 | API间隔秒数 |
| --json | 否 | 输出JSON格式 |
| --output | - | JSON输出文件路径 |
| --timeframe | 1d | 分析周期: 1d/1w/1m |

### 过滤规则优先级

1. **硬过滤**（直接排除）: 黑名单、市值<10B、价格<MA200、phase=decline、strong_down共振、RSI<30超卖、RR<2.0、基本面不达标、追高(距高点<8%)、VCP无量、TD卖出确认、MACD顶背离、看跌K线形态
2. **软过滤**（扣分/警告）: RSI>75超买警告、MA5/MA20偏离>8%

## v2.14.3 更新
- 静态池从166扩充到335只，覆盖更多行业（房地产、公用事业、材料）
- 移除 screener.py 中的假ticker（US.AAB-UEF）
- 热门池从190扩充到279只真实大市值股票
- 市值门槛统一为100亿美元（>=10B）

## BUG 扫描报告 (v2.14.2)

| 问题 | 文件 | 行号 | 状态 |
|------|------|------|------|
| 格式化字符串 .1f 被拼接 | screener.py | 330 | 已修复 |
| 基本面过滤 symbol 前缀 | fundamental.py | 37 | 已修复 |
| bare except (低优先级) | meme_tracker.py | 53 | 已知，不影响核心 |

## 免责声明

本工具仅供技术分析参考，不构成投资建议。股市投资有风险，请根据自身风险承受能力综合判断，独立决策。
