
from futu import OpenQuoteContext, ScrMarket
import logging
logging.basicConfig(level=logging.INFO)
ctx = OpenQuoteContext('127.0.0.1', 11111)
print('连接成功')
ret, data = ctx.get_top_movers_rank(ScrMarket.US, count=10)
print(f'API返回: ret={ret}')
if data is not None:
    print(f'数据形状: {data.shape}')
    print(data.head(10))
else:
    print('数据为空')
ctx.close()
print('测试完成')
