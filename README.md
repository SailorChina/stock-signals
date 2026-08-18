# stock-signals

股票买卖信号分析系统 — 三市场（A股/港股/美股）技术指标扫描

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
| VWMA | 成交量加权均线 |

### 高级信号
| 信号 | 说明 |
|------|------|
| **VCP** 波动率收缩 | Mark Minervini SEPA 策略，检测2-6次收缩循环 |
| **Episodic Pivot** 事件性转折 | 跳空高开 + 量能放大突破 |
| **TD Sequential** 9转信号 | 9连阴买入 / 9连阳卖出 |
| **多时间框架共振** | 日/周/月线联动评分 |

## 数据源 (v2.1)

| 市场 | 热门股获取 | K线数据 |
|------|-----------|---------|
| A股 | 雪球热度榜 (akshare) | Sina优先, akshare fallback |
| 港股 | 静态池+Tencent验证 | akshare daily |
| 美股 | 静态池 (知名蓝筹) | akshare daily |

## 扫描速度

| 市场 | 股票数 | 首次扫描 | 缓存命中 |
|------|--------|----------|----------|
| A股 | 300 | ~75s | ~0.2s |
| 港股 | 20 | ~12s | - |
| 美股 | 25 | ~15s | - |

## 安装

```bash
pip install -e .
```

依赖：
- akshare >= 1.18
- pandas >= 2.0
- numpy >= 1.24

## 使用方法

```python
from stock_signals.hot_fetcher import fetch_hot_stocks
from stock_signals.indicators import fetch_kline, compute_indicators
from stock_signals.scoring import compute_rating

# 获取热门股
a_hot = fetch_hot_stocks('A', 300)
hk_hot = fetch_hot_stocks('HK', 300)
us_hot = fetch_hot_stocks('US', 300)

# 扫描单只股票
df = fetch_kline('SH.600519')
ind = compute_indicators(df, 'SH.600519')
rat = compute_rating(ind)
print(f"评级: {rat['rating']}, 分数: {rat['score']}")
```

## API说明

### fetch_kline(code, ktype='1d', num=300)
获取K线数据
- code格式: SH.600519, SZ.000001, HK.00700, US.AAPL
- 返回DataFrame: time, open, high, low, close, volume

### compute_indicators(df, code, ktype)
计算技术指标，返回Indicators对象

### compute_rating(ind)
计算综合评分，返回评级字典

### fetch_hot_stocks(market, top_n=300)
获取热门股列表
- market: 'A', 'HK', 'US'

## 评级说明

| 评级 | 分数范围 | 含义 |
|------|----------|------|
| Buy | 75-100 | 强烈买入 |
| Overweight | 60-74 | 优于大盘 |
| Hold | 40-59 | 持有观望 |
| Underweight | 25-39 | 弱于大盘 |
| Sell | 0-24 | 建议卖出 |

## 项目结构

```
stock_signals/
├── indicators.py    # K线获取+指标计算
├── hot_fetcher.py   # 热门股获取
├── scoring.py       # 评分引擎
├── screener.py      # 扫描引擎
├── config.py        # 配置
└── data_sources.py  # 数据源接口
```

## 变更日志

### v2.1 (2026-08-18)
- 移除Futu OpenAPI依赖（CET兼容问题）
- 使用Sina+akshare双数据源
- 添加内存缓存机制
- 优化热门股获取：A股使用雪球热度榜
- 修复扫描速度问题

### v2.0
- 支持三市场扫描
- 使用Futu OpenAPI获取K线

## 许可证

MIT
