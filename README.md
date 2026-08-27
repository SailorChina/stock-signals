# tech-signal-skill

> **Codex Skill: 美股技术分析 & 买卖信号生成器**

基于技术指标（MA/MACD/RSI/KDJ/BOLL/ATR/OBV/ADX）+ 高级形态识别（VCP/事件驱动拐点/TD序列/多周期共振），自动生成评级、入场点、止损位和目标价。

**适用市场：美股 (US)**

## 安装

### 方式一：pip 安装（推荐）

```bash
pip install tech-signal-FUTU-skill
```

### 方式二：从源码安装

```bash
git clone https://github.com/SailorChina/tech-signal-FUTU-skill.git
cd tech-signal-skill
pip install -e .
```

### 依赖

- Python >= 3.10
- pandas >= 2.0
- numpy >= 1.24
- akshare >= 1.18（K 线数据，必选）
- futu-api >= 10.4.6408（实时报价，可选）

**Futu OpenD** 需在 127.0.0.1:11111 运行（免费客户端，[官网下载](https://openapi.futunn.com)）

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
| **交易计划生成** | 入场区间 + 止损 + 双目标 + 风险回报比 + 仓位建议 |

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

### 入场类型 (v2.16.1 新增)

扫描结果显式标注入场方式：

| 类型 | 说明 | 操作建议 |
|------|------|----------|
| `现价入场` | 价格偏离 < 2% | 市价直接买入 |
| `回调入场` | 价格低于现价 | 等待回踩支撑后分批建仓 |
| `突破入场` | 价格高于现价 | 等待突破阻力后跟进 |

交易计划文本示例：
- `市价直接入场（现价附近，偏离 1.0%）`
- `回调入场，等待价格回落至 47.32 (-1.0%) 附近分批建仓`

### Meme 股票追踪 (v2.11.1)

```bash
python -m stock_signals.cli meme list
python -m stock_signals.cli meme add US.NVDA
python -m stock_signals.cli meme scan
```

- 默认 watchlist 包含猫姐常提的10只股票
- meme 股票评分加成 +5%
- 自动抓取接口预留（X/Twitter + YouTube）

## 数据源

| 数据 | 来源 |
|------|------|
| K 线 | akshare `stock_us_daily`（daily/weekly/monthly） |
| 热门股 | Sina 成交量排序，静态池 335 只蓝筹 |
| 卖空比例 | futu-api（可选） |

Futu OpenD 实时报价覆盖 akshare 历史数据滞后问题。Futu 连接失败时自动回退到 akshare。

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
+- dynamic_pool.py        # 动态股池管理
+- fundamental.py         # 基本面数据获取（毛利率/净利率/营收增长）
+- futu_api.py            # Futu OpenD 实时报价接口
+- us/                    # 美股专用模块
  +- backtest_us.py       # 美股回测引擎
  +- indicators_us.py     # 美股指标计算
  +- optimize_us.py       # 参数优化
  +- scoring_us.py        # 美股评分引擎
  +- screener_us.py       # 美股筛选器
  +- us_pool_full.txt     # 300 只蓝筹完整列表
tests/
+- test_stock_signals.py  # 单元测试
pyproject.toml             # 项目配置
```

## 过滤规则优先级

1. **硬过滤**（直接排除）: 黑名单、市值<10B、价格<MA200、phase=decline、strong_down共振、RSI<30超卖、RR<2.0、基本面不达标、追高(距高点<8%)、VCP无量、TD卖出确认、MACD顶背离、看跌K线形态
2. **软过滤**（扣分/警告）: RSI>75超买警告、MA5/MA20偏离>8%

## 性能

- 扫描 300 只热股: ~6-10 分钟（串行 Futu 批处理）
- 单只分析: ~0.2s（缓存命中）
- 无需外部 API Key

## BUG 修复

### v2.16.1 (2026-08-27)
- **入场类型字段 (entry_type)**: 扫描结果显式标注入场方式
- **交易计划文本优化**: 买入策略说明增加偏离幅度

### v2.14.3 (2026-08-24)
- 修复 screener.py:330 格式化字符串 BUG（.1f 被当作字符串拼接）
- 修复 fundamental.py symbol 前缀 BUG（akshare 需要纯代码）
- 全面扫描验证所有过滤规则正确工作

### v2.15.0 (2026-08-25)
- Futu OpenD 实时报价集成，修正 akshare 数据滞后问题
- 回退机制：Futu 连接失败自动使用 akshare

### v2.16.0 (2026-08-25)
- Futu API 批处理优化，300只扫描从 ~2.5分钟降至 ~6秒
- 市值门槛从 50B 降至 10B，股票池扩充至 335只
- hot_fetcher.py 清理重复函数定义

## 免责声明

本工具仅供技术分析参考，不构成投资建议。股市投资有风险，请根据自身风险承受能力综合判断，独立决策。
