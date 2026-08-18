
import re

with open('stock_signals/indicators.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_fn = '''def fetch_kline(code: str, ktype: str = "1d", num: int = 300) -> pd.DataFrame:
    """获取K线数据 - baostock(A股) / akshare(HK/US)"""
    import pandas as pd
    import sys

    clean = code.split(".")[-1]

    if code.startswith("SH") or code.startswith("SZ"):
        try:
            import baostock as bs
            bs_code = code.lower()
            lg = bs.login()
            if lg.error_code != "0":
                print(f"[ERROR] baostock login failed: {lg.error_msg}", file=sys.stderr)
                return pd.DataFrame()
            freq = {"1d": "d", "1w": "w", "1M": "m"}.get(ktype, "d")
            rs = bs.query_history_k_data_plus(
                bs_code, fields="date,open,high,low,close,volume",
                start_date="2020-01-01", end_date="2026-12-31", frequency=freq
            )
            rows = []
            while (rs.error_code == "0") & rs.next():
                rows.append(rs.get_row_data())
            bs.logout()
            if not rows:
                return pd.DataFrame()
            df = pd.DataFrame(rows, columns=rs.fields)
            df = df.rename(columns={{"date": "time"}})
            df["time"] = pd.to_datetime(df["time"]).astype(str)
            for col in ("open", "high", "low", "close", "volume"):
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            return df.sort_values("time").tail(num).reset_index(drop=True)
        except Exception as e:
            print(f"[ERROR] baostock K线失败 {{code}}: {{e}}", file=sys.stderr)
            return pd.DataFrame()
    else:
        try:
            import akshare as ak
            if code.startswith("HK"):
                df = ak.stock_hk_hist(symbol=clean, period="daily", adjust="qfq")
            elif code.startswith("US"):
                df = ak.stock_us_hist(symbol=f"105.{{clean.upper()}}", period="daily", adjust="qfq")
            else:
                return pd.DataFrame()
            if df is not None and not df.empty:
                df = df.rename(columns={{"日期": "time", "开盘": "open", "最高": "high", "最低": "low", "收盘": "close", "成交量": "volume"}})
                df["time"] = pd.to_datetime(df["time"]).astype(str)
                for col in ("open", "high", "low", "close", "volume"):
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                return df.sort_values("time").tail(num).reset_index(drop=True)
        except Exception as e:
            print(f"[ERROR] akshare K线失败 {{code}}: {{e}}", file=sys.stderr)
            return pd.DataFrame()
    return pd.DataFrame()
'''

pattern = r'def fetch_kline\(.*?(?=\n(?:@dataclass|def |\Z))'
match = re.search(pattern, content, re.DOTALL)
if match:
    content = content[:match.start()] + new_fn + content[match.end():]
    print(f"Replaced fetch_kline")
else:
    print("ERROR: Could not find fetch_kline")

with open('stock_signals/indicators.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
