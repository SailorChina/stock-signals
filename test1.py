
print('测试开始')
from futu import OpenQuoteContext, ScrMarket
ctx = OpenQuoteContext('127.0.0.1', 11111)
print('连接中...')
ret, data = ctx.get_top_movers_rank(ScrMarket.US, count=5)
print(f'返回: ret={ret}')
if data is not None:
    print(f'行数: {len(data)}')
    print(data.head())
else:
    print('data=None')
ctx.close()
print('测试完成')
