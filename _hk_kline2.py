
import os, sys, time
sys.path.insert(0, '.')
for k in list(os.environ.keys()):
    if 'PROXY' in k.upper(): os.environ.pop(k, None)
import urllib.request, json

print('=== 港股 K线 更多测试 ===')

# 1. 尝试新浪港股 K线不同端点
print('Test1: Sina 港股K线(不同端点)')
endpoints = [
    'http://stock2.finance.sina.com.cn/api/json_v2.php/StockHkHistoryService.getHistoryKline',
    'http://hq.sinajs.cn/list=hk00700',
]
# 尝试不同的 K线端点
for sym in ['hk00700', '00700']:
    # 尝试 daily K线
    url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={sym}&scale=240&ma=no&datalen=20'
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10)
        data = json.loads(resp.read().decode())
        print(f'  {sym} daily: {len(data) if data else 0} rows')
    except Exception as e:
        print(f'  {sym} daily: ERR {str(e)[:60]}')

# 2. 尝试东方财富港股 K线
print('Test2: 东方财富港股K线')
try:
    import akshare as ak
    t = time.time()
    df = ak.stock_hk_hist(symbol='00700', period='daily', adjust='qfq')
    print(f'  00700: {len(df)} rows in {time.time()-t:.1f}s')
except Exception as e:
    err = str(e)
    if 'PROXY' in err.upper() or 'proxy' in err.lower():
        print(f'  代理问题，尝试其他方式...')
    else:
        print(f'  ERR: {err[:200]}')

# 3. 尝试新浪财经港股实时数据获取代码列表
print('Test3: Sina 港股列表')
url3 = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=100&sort=symbol&asc=1&node=hk_h'
try:
    resp3 = urllib.request.urlopen(urllib.request.Request(url3, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'http://finance.sina.com.cn/'}), timeout=10)
    data3 = json.loads(resp3.read().decode())
    print(f'  OK: {len(data3) if data3 else 0} stocks')
    if data3:
        print(f'  Sample: {data3[0].get("code", "?")}')
except Exception as e:
    print(f'  ERR: {str(e)[:200]}')
