# 美股策略改进方案 — 专业交易员视角

## 一、当前状态
- A股回测: 209.83%毛收益 / 169.84%净收益 (2024-01~2026-08, 1394笔, 46.9%胜率, 28.57%回撤)
- 美股扫描: 17只候选 (静态池43只, 评分>=46+距高点>=8%+RR>=2:1)
- P5市场过滤已验证失败, 已回退

## 二、专业交易员视角: 5大缺口

### 缺口1: 数据源质量不足(最关键)
现状: akshare stock_us_daily, ~10000条日K, 拆股调整不精确
建议: 切换yfinance (已装v1.6.0), adjust='both'含split+dividend, 50+年历史

### 缺口2: 策略参数未针对美股优化
美股vsA股差异:
- 日均波动: A股2-3% vs 美股1-2% (但美股无涨跌停保护, 跳空风险更大)
- 趋势持续性: A股政策驱动强 vs 美股基本面驱动中
- 做空: A股困难 vs 美股容易
- 流动性: A股分散 vs 美股集中(大盘股)

参数调整建议:
- 止损: 1.2xATR -> 1.5-2.0xATR
- 持仓上限: 5天 -> 7-10天
- 评分门槛: 46 -> 50
- RR门槛: 2.0 -> 2.5
- 新增: 市值过滤(<50亿美金剔除)

### 缺口3: A股特有因子在美股失效
- capital(超大单资金流向) -> 美股无实时数据
- short_pct(融券比例) -> 数据来源不同(FINRA SHORC)
- 建议: 美股独立评分, 去掉capital/short维度
- 新增维度: earnings_momentum, sector_rotation

### 缺口4: 缺少美股特有信号
- Earnings Play: 财报前信号
- Sector Rotation: 行业轮动timing
- VIX Regime: 波动率环境调整
- Dollar Strength: 美元指数影响

### 缺口5: 回测框架不支持美股
现状: backtest_v2.py用Sina API仅支持A股
建议: 新建backtest_us.py, 基于yfinance, 2018-2026回测

## 三、改进方案(4阶段)
Phase1: 数据层改造(新增indicators_us.py + screener_us.py + scoring_us.py, A股不动)
Phase2: 回测框架(backtest_us.py, $1M初始, 道指30+SP500前200)
Phase3: 参数调优(网格搜索+Walk-forward验证)
Phase4: 新增信号(VIX过滤, 市值过滤, 行业分散, 财报日期过滤)

## 四、不改动
- A股 indicators.py / screener.py / scoring.py
- A股 backtest_v2.py + backtest_result.json
- A股测试

## 五、需要确认
1. 是否先做Phase1+2(数据改造+回测), 验证美股策略可行后再做调优?
2. 回测期间是否包含2020年COVID crash? (关键压力测试)
3. 是否考虑加入做空逻辑? (美股允许做空)
