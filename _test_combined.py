
import urllib.request
import json
import time

print("=" * 70)
print("综合测试 - 港股/美股数据源")
print("=" * 70)

# ========== 港股 ==========
print("\n[港股] 实时行情")
urls_hk = [
    ("腾讯", "https://qt.gtimg.cn/q=hk00700,hk00001,hk0939,hk09988"),
    ("Sina", "http://hq.sinajs.cn/list=hk00700,hk00001,hk0939"),
]
for name, url in urls_hk:
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
        resp = urllib.request.urlopen(req, timeout=10)
        dt = time.time() - t0
        data = resp.read().decode('gbk' if 'sina' in url else 'utf-8')
        print(f"  {name}: {dt:.2f}s, len={len(data)}")
        if len(data) > 100:
            print(f"    数据: {data[:200]}")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")

print("\n[港股] K线数据")
kline_urls = [
    ("Sina HK_StockData", "http://stock.finance.sina.com.cn/hkstock/api/json_v2.php/HK_StockData.getKLineData?symbol=hk00700&type=daily&num=10"),
    ("Sina SinaHK", "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol=hk00700&scale=240&datalen=10"),
    ("Sina CN_market", "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=hk00700&scale=240&ma=no&datalen=10"),
]
for name, url in kline_urls:
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
        resp = urllib.request.urlopen(req, timeout=10)
        dt = time.time() - t0
        data = resp.read().decode()
        if data and data.strip() and data.strip() not in ('null', '[]'):
            items = json.loads(data)
            print(f"  {name}: OK, {dt:.2f}s, {len(items)} rows")
            if items:
                print(f"    最新: {items[-1]}")
        else:
            print(f"  {name}: empty")
    except Exception as e:
        print(f"  {name}: ERROR - {str(e)[:60]}")

print("\n[港股] 排行/列表")
rank_urls = [
    ("Sina hk_hy_c", "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=50&sort=changepercent&asc=0&node=hk_hy_c"),
]
for name, url in rank_urls:
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "http://finance.sina.com.cn/"})
        resp = urllib.request.urlopen(req, timeout=10)
        dt = time.time() - t0
        data = resp.read().decode()
        items = json.loads(data)
        print(f"  {name}: {dt:.2f}s, {len(items)} stocks")
        for item in items[:3]:
            print(f"    {item.get('code')}: {item.get('name')} - {item.get('trade')}")
    except Exception as e:
        print(f"  {name}: ERROR - {str(e)[:60]}")

# ========== 美股 ==========
print("\n" + "=" * 70)
print("[美股] 实时行情")
urls_us = [
    ("腾讯", "https://qt.gtimg.cn/q=usAAPL,usGOOGL,usMSFT,usTSLA"),
    ("Sina", "http://hq.sinajs.cn/list=usAAPL,usGOOGL,usMSFT"),
]
for name, url in urls_us:
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
        resp = urllib.request.urlopen(req, timeout=10)
        dt = time.time() - t0
        data = resp.read().decode('gbk' if 'sina' in url else 'utf-8')
        print(f"  {name}: {dt:.2f}s, len={len(data)}")
        if len(data) > 100:
            print(f"    数据: {data[:200]}")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")

print("\n[美股] K线数据")
kline_urls_us = [
    ("Sina US_StockData", "http://stock.finance.sina.com.cn/usstock/api/json_v2.php/US_StockData.getKLineData?symbol=usAAPL&type=daily&num=10"),
    ("Sina SinaUS", "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol=usAAPL&scale=240&datalen=10"),
]
for name, url in kline_urls_us:
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
        resp = urllib.request.urlopen(req, timeout=10)
        dt = time.time() - t0
        data = resp.read().decode()
        if data and data.strip() and data.strip() not in ('null', '[]'):
            items = json.loads(data)
            print(f"  {name}: OK, {dt:.2f}s, {len(items)} rows")
        else:
            print(f"  {name}: empty")
    except Exception as e:
        print(f"  {name}: ERROR - {str(e)[:60]}")

print("\n[美股] 排行/列表")
rank_urls_us = [
    ("Sina us_main", "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=50&sort=changepercent&asc=0&node=us_main"),
]
for name, url in rank_urls_us:
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "http://finance.sina.com.cn/"})
        resp = urllib.request.urlopen(req, timeout=10)
        dt = time.time() - t0
        data = resp.read().decode()
        items = json.loads(data)
        print(f"  {name}: {dt:.2f}s, {len(items)} stocks")
        for item in items[:3]:
            print(f"    {item.get('code')}: {item.get('name')} - {item.get('trade')}")
    except Exception as e:
        print(f"  {name}: ERROR - {str(e)[:60]}")
