# stock-signals

US stock technical analysis & buy/sell signal generator

## Core Features

### Technical Indicators (Universal Engine)
| Indicator | Description |
|------|------|
| MA/EMA | 5/10/20/60/120/200 day moving averages, golden/death cross detection |
| MACD | DIF/DEA/Hist, golden/death cross, divergence detection |
| RSI | 6/12/14/24 periods, overbought/oversold judgment |
| KDJ | K/D/J three lines, overbought/oversold |
| BOLL | Bollinger upper/mid/lower bands + width |
| ATR | 14-period true range, dynamic stop-loss |
| OBV | On-balance volume, capital flow direction |
| VWMA | Volume-weighted moving average |
| ADX | Trend strength, +DI/-DI direction |

### Advanced Signals
| Signal | Description |
|------|------|
| **VCP** Volatility Contraction | Mark Minervini SEPA strategy, detects 2-6 contraction cycles |
| **Episodic Pivot** Event-driven reversal | Kristjan Qullamaggie strategy, gap-up + volume spike breakout |
| **TD Sequential** 9-turn signal | 9 consecutive down bars buy / 9 consecutive up bars sell |
| **Multi-timeframe Resonance** | Daily/weekly/monthly alignment scoring with confidence boost |
| **Support & Resistance** | Swing point clustering + BOLL + MA clusters + VWAP |
| **Trend Phase Classification** | Accumulation / Early Rally / Rally / Distribution / Decline |
| **Trade Plan Generation** | Entry zone, stop-loss, dual targets, risk-reward ratio, position sizing |

### A-Share Specific
| Feature | Description |
|------|------|
| Limit-up/Down Protection | Auto-filters stocks hitting limit-up or limit-down |
| KDJ Overbought Filter | J>100 auto-intercept |
| Longhu Bang (Dragon Tiger List) | Institutional buy/sell direction + net amount |
| Northbound Capital | Real-time net inflow/outflow |
| Sector Heat | Industry linkage scoring |
| Bollinger Position | Lower band support / Upper band breakout |

### Smart Filtering (v2.5.0+)
- RSI(14) > 75 -> hard intercept for chasing highs
- Distance from high > -2% -> intercept chasing
- MA5/MA20 deviation > 8% -> score reduction
- MACD golden cross maturity -> bonus/penalty
- Pullback entry scoring -> pullback_score priority sorting

## Data Sources

| Market | K-line Data | Hot Stocks | Special Data |
|------|---------|--------|----------|
| A-share | Sina primary -> akshare fallback | Snowball heat ranking -> Sina -> Eastmoney | Longhu Board / Northbound flow / Sector heat |
| HK | akshare daily -> Tencent verify | Hang Seng + Hang Seng Tech static pool | Tencent real-time verification |
| US | akshare daily | Sina quotes sorted by volume | 371 blue-chip static pool |

Memory cache: K-line data cached by {code}_{num}, cache hit ~0.2s, first run ~75s (300 A-shares).

## Project Structure

stock_signals/
+- __init__.py            # v2.10.1, exports core API
+- _info.py               # Stock info database (Chinese name/sector/description)
+- _resonance.py          # Multi-timeframe resonance analysis (daily/weekly/monthly)
+- _sr.py                 # Support/resistance calculation + trade plan generation
+- _vcp.py                # VCP volatility contraction pattern detection
+- _episodic_pivot.py     # Episodic Pivot event-driven reversal detection
+- indicators.py          # Universal indicator calculation (MA/MACD/RSI/KDJ/BOLL/ATR/OBV/VWMA/ADX)
+- indicators_a.py        # A-share specific indicators (limit/counter/KDJ/Boll/KDJ_J/Longhu/North)
+- indicators_us.py       # US market specific indicators
+- scoring.py             # Universal scoring engine (trend/momentum/volume/volatility/capital, 5-dim weighted)
+- scoring_a.py           # A-share specific scoring (12 dimensions)
+- scoring_us.py          # US market specific scoring
+- screener.py            # Multimarket parallel scanning engine
+- screener_a.py          # A-share specific scanner
+- hot_fetcher.py         # Hot stock fetching (Snowball/Sina/Eastmoney/Tencent fallback chain)
+- cli.py                 # CLI entry (analyze/scan subcommands)
+- reporter.py            # Chinese scan report output
+- config.py              # Configuration management (memory cache/TTL/retry)
+- data_sources.py        # Data source interface wrapper
+- dynamic_pool.py        # Dynamic stock pool management
+- a_share/               # A-share submodules (backtest/scoring/screener wrappers)
+- us/                    # US submodules (backtest/scoring/screener/optimize wrappers)
tests/
+- test_stock_signals.py  # Unit tests
backtest_v2.py             # Full market backtest script
pyproject.toml             # Project config

## Installation

\\ash
pip install -e .

Dependencies:
- Python >= 3.10
- pandas >= 2.0
- numpy >= 1.24
- akshare >= 1.18 (K-line data)
- futu-api >= 10.4.6408 (capital/short data, optional)

## Usage

### CLI

\\ash
# Analyze single stock
python -m stock_signals.cli analyze US.NVDA
python -m stock_signals.cli analyze US.NVDA
python -m stock_signals.cli analyze US.AAPL

# Multi-timeframe analysis
python -m stock_signals.cli analyze US.NVDA --timeframe 1w
python -m stock_signals.cli analyze US.NVDA --timeframe 1m

# Full market scan
python -m stock_signals.cli scan                    # interactive market selection
python -m stock_signals.cli scan --markets US       # US only
python -m stock_signals.cli scan --markets A        # A-share only
python -m stock_signals.cli scan --markets A,US,HK  # all markets
python -m stock_signals.cli scan --min-score 55 --max-picks 5 --parallel

# Export
python -m stock_signals.cli scan --markets US --json --output report.json
python -m stock_signals.cli analyze US.NVDA --csv results.csv

### Python API

\\python
from stock_signals.indicators import fetch_kline, compute_indicators
from stock_signals.scoring import compute_rating
from stock_signals._resonance import compute_timeframe_resonance
from stock_signals._sr import compute_support_resistance, generate_trade_plan
from stock_signals.screener import scan_parallel, ScanConfig

df = fetch_kline('US.NVDA', ktype='1d', num=300)
ind = compute_indicators(df, 'US.NVDA', '1d')
result = compute_rating(ind)
print('Rating:', result['rating'], 'Score:', result['score'])
resonance = compute_timeframe_resonance('US.NVDA', ind)
print('Resonance:', resonance.alignment, 'Boost:', resonance.confidence_boost)
\
## Rating Scale

| Rating | Score Range | Meaning |
|------|----------|------|
| Buy | 75-100 | Strong buy |
| Overweight | 60-74 | Better than market |
| Hold | 40-59 | Hold/watch |
| Underweight | 25-39 | Weaker than market |
| Sell | 0-24 | Sell recommended |

## Dynamic Weights (v2.6.0+)

Automatically adjusts dimension weights based on volatility regime:
- Low volatility: momentum/volume weights increase, trend weight decreases
- High volatility: trend/momentum weights increase, volume/capital weights decrease

## Tests

\\ash
pytest tests/ -v

## Changelog

### v2.10.1 (2026-08-21)
- Restructured A-share/US strategies into independent submodules (a_share/, us/)
- Fixed US cache bug, expanded US stock pool to 371 stocks
- Fixed A-share backtest index bug

### v2.8.5
- CLI supports parallel scanning (--parallel 3-5x speed boost)
- Smart filtering system: RSI/deviation/MACD maturity/pullback entry
- A-share scanner integrated Longhu Board + Northbound flow + Sector heat

### v2.5.0
- VCP volatility contraction detection (Minervini SEPA)
- Episodic Pivot event-driven reversal detection (Qullamaggie)
- Multi-timeframe resonance analysis (daily/weekly/monthly alignment)
- Support/resistance clustering + trade plan generation

### v2.1
- Removed Futu OpenAPI K-line dependency, using Sina+akshare dual data sources
- Added memory cache mechanism (cache hit ~0.2s)
- A-share hot stock: Snowball heat ranking -> Sina -> Eastmoney fallback

### v2.0
- Supports three-market scanning
- Uses Futu OpenAPI for K-line data

## Disclaimer

This tool is for technical reference only and does not constitute investment advice. Stock market investment carries risks. Please make decisions based on your own risk tolerance and comprehensive analysis.
