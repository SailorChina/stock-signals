
import baostock as bs
lg = bs.login()
for code in ['sz.600519', 'sh.600519', 'sz.000001']:
    rs = bs.query_history_k_data_plus(code=code, fields='date,close', start_date='2024-01-01', end_date='2024-01-31', frequency='d')
    rows = []
    while (rs.error_code == '0') & rs.next(): rows.append(rs.get_row_data())
    print(f'{code}: {len(rows)} rows')
bs.logout()
