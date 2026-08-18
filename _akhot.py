
import akshare as ak
import sys
sys.stdout.reconfigure(line_buffering=True)
print("=== A股 ===")
try:
    df = ak.stock_zh_a_spot_em()
    print("A股实时行情:", len(df), "只")
    df_sorted = df.sort_values("涨跌幅", ascending=False).head(15)
    for _, row in df_sorted.iterrows():
        print(" ", row["代码"], row["名称"], row["涨跌幅"], "%")
except Exception as e:
    print("A股spot error:", e)
print()
print("=== 港股 ===")
try:
    df2 = ak.stock_hk_spot_em()
    print("港股实时行情:", len(df2), "只")
    df2_sorted = df2.sort_values("涨跌幅", ascending=False).head(15)
    for _, row in df2_sorted.iterrows():
        print(" ", row.get("代码","?"), row.get("名称","?"), row.get("涨跌幅","?"))
except Exception as e:
    print("港股spot error:", e)
print()
print("=== 美股 ===")
try:
    df3 = ak.stock_us_spot_em()
    print("美股实时行情:", len(df3), "只")
    df3_sorted = df3.sort_values("涨跌幅", ascending=False).head(15)
    for _, row in df3_sorted.iterrows():
        print(" ", row.get("代码","?"), row.get("名称","?"), row.get("涨跌幅","?"))
except Exception as e:
    print("美股spot error:", e)
print("DONE")
