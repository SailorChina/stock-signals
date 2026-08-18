
import baostock as bs
lg = bs.login()
print(f'login: {lg.error_code}')
rs = bs.query_history_k_data_plus(code='sz.600519', fields='date,close', start_date='2025-01-01', end_date='2025-08-18', frequency='d')
print(f'query: {rs.error_code}')
rows = []
while (rs.error_code == '0') & rs.next(): rows.append(rs.get_row_data())
print(f'rows: {len(rows)}')
bs.logout()
