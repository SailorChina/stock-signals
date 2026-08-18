
import os
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k)
import baostock as bs
lg = bs.login()
print(f'login: {lg.error_code}')
rs = bs.query_history_kline_plus(start='2025-01-01', end='2025-08-18', code='sz.600519', frequency='d')
print(f'query: code={rs.error_code} msg={rs.error_msg}')
rows = []
while (rs.error_code == '0') & rs.next(): rows.append(rs.get_row_data())
print(f'rows={len(rows)}')
if rows: print(f'first={rows[0]}')
bs.logout()
