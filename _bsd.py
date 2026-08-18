
import baostock as bs
lg = bs.login()
print(f'login: {lg.error_code}')
rs = bs.query_history_k_data_plus(code='sz.600519', fields='date,close', start_date='2024-01-01', end_date='2024-12-31', frequency='d')
rows = []
while (rs.error_code == '0') & rs.next(): rows.append(rs.get_row_data())
print(f'2024 rows: {len(rows)}')
if rows: print(f'  first: {rows[0]}')
rs2 = bs.query_history_k_data_plus(code='sz.600519', fields='date,close', start_date='2020-01-01', end_date='2020-12-31', frequency='d')
rows2 = []
while (rs2.error_code == '0') & rs2.next(): rows2.append(rs2.get_row_data())
print(f'2020 rows: {len(rows2)}')
if rows2: print(f'  first: {rows2[0]}')
bs.logout()
