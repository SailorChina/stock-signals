
import os
import time
import urllib.request
import json

# 清除代理
for k in list(os.environ.keys()):
    if 'proxy' in k.lower():
        os.environ.pop(k)

print("=" * 70)
print("港股/美股 API 完整测试")
print("=" * 70)

results = {}

# ========== 港股测试 ==========
print("\n" + "=" * 70)
print("港股 API 测试")
print("=" * 70)

# 1. 腾讯港股实时
print("\n[1] 腾讯 港股实时")
try:
    t0 = time.time()
    url = "https://qt.gtimg.cn/q=hk00700,hk00001,hk0939,hk09988,hk02382"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode('gbk')
    lines = data.strip().split('\n')
    valid = sum(1 for l in lines if '~' in l and len(l.split('~')) > 40)
    results['tencent_hk_realtime'] = valid > 0
    print(f"  {'OK' if results['tencent_hk_realtime'] else 'FAIL'}: {dt:.2f}s, {valid}/{len(lines)} valid")
    if valid > 0:
        for line in lines[:3]:
            if '~' in line:
                parts = line.split('~')
                if len(parts) > 40:
                    print(f"    {parts[1]}: 当前={parts[3]}, 涨跌幅={parts[32]}%")
except Exception as e:
    results['tencent_hk_realtime'] = False
    print(f"  FAIL: {e}")

# 2. Sina港股实时
print("\n[2] Sina 港股实时")
try:
    t0 = time.time()
    url = "http://hq.sinajs.cn/list=hk00700,hk00001,hk0939"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode('gbk')
    lines = data.strip().split(';')
    valid = sum(1 for l in lines if '=' in l and len(l.split('=', 1)[1].strip('\"')) > 50)
    results['sina_hk_realtime'] = valid > 0
    print(f"  {'OK' if results['sina_hk_realtime'] else 'FAIL'}: {dt:.2f}s, {valid}/{len(lines)} valid")
except Exception as e:
    results['sina_hk_realtime'] = False
    print(f"  FAIL: {e}")

# 3. Sina港股K线
print("\n[3] Sina 港股K线")
kline_urls = [
    ("HK_StockData", "http://stock.finance.sina.com.cn/hkstock/api/json_v2.php/HK_StockData.getKLineData?symbol=hk00700&type=daily&num=5"),
    ("SinaHK_api", "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol=hk00700&scale=240&datalen=5"),
]
for name, url in kline_urls:
    try:
        t0 = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
        resp = urllib.request.urlopen(req, timeout=10)
        dt = time.time() - t0
        data = resp.read().decode()
        if data and data.strip() and data.strip() not in ('null', '[]', ''):
            items = json.loads(data)
            if isinstance(items, list) and len(items) > 0:
                results[f'sina_hk_kline_{name}'] = True
                print(f"  {name}: OK, {dt:.2f}s, {len(items)} rows")
                break
            else:
                results[f'sina_hk_kline_{name}'] = False
        else:
            results[f'sina_hk_kline_{name}'] = False
    except Exception as e:
        results[f'sina_hk_kline_{name}'] = False
        print(f"  {name}: FAIL - {str(e)[:50]}")

# 4. 腾讯港股列表
print("\n[4] 腾讯 港股列表")
try:
    t0 = time.time()
    url = "https://qt.gtimg.cn/q=hk_all"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode('gbk')
    lines = data.strip().split('\n')
    valid = sum(1 for l in lines if '~' in l)
    results['tencent_hk_list'] = valid > 100
    print(f"  {'OK' if results['tencent_hk_list'] else 'FAIL'}: {dt:.2f}s, {valid} stocks")
except Exception as e:
    results['tencent_hk_list'] = False
    print(f"  FAIL: {e}")

# 5. Sina港股排行
print("\n[5] Sina 港股排行")
try:
    t0 = time.time()
    url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData?page=1&num=100&sort=changepercent&asc=0&node=hk_hy_c"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode()
    items = json.loads(data)
    results['sina_hk_rank'] = len(items) > 50
    print(f"  {'OK' if results['sina_hk_rank'] else 'FAIL'}: {dt:.2f}s, {len(items)} stocks")
except Exception as e:
    results['sina_hk_rank'] = False
    print(f"  FAIL: {e}")

# ========== 美股测试 ==========
print("\n" + "=" * 70)
print("美股 API 测试")
print("=" * 70)

# 6. 腾讯美股实时
print("\n[6] 腾讯 美股实时")
try:
    t0 = time.time()
    url = "https://qt.gtimg.cn/q=usAAPL,usGOOGL,usMSFT,usTSLA,usAMZN"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode('gbk')
    lines = data.strip().split('\n')
    valid = sum(1 for l in lines if '~' in l and len(l.split('~')) > 40)
    results['tencent_us_realtime'] = valid > 0
    print(f"  {'OK' if results['tencent_us_realtime'] else 'FAIL'}: {dt:.2f}s, {valid}/{len(lines)} valid")
    if valid > 0:
        for line in lines[:3]:
            if '~' in line:
                parts = line.split('~')
                if len(parts) > 40:
                    print(f"    {parts[1]}: 当前={parts[3]}, 涨跌幅={parts[32]}%")
except Exception as e:
    results['tencent_us_realtime'] = False
    print(f"  FAIL: {e}")

# 7. 腾讯美股列表
print("\n[7] 腾讯 美股列表")
try:
    t0 = time.time()
    url = "https://qt.gtimg.cn/q=us_all"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode('gbk')
    lines = data.strip().split('\n')
    valid = sum(1 for l in lines if '~' in l)
    results['tencent_us_list'] = valid > 100
    print(f"  {'OK' if results['tencent_us_list'] else 'FAIL'}: {dt:.2f}s, {valid} stocks")
except Exception as e:
    results['tencent_us_list'] = False
    print(f"  FAIL: {e}")

# 8. Sina美股实时
print("\n[8] Sina 美股实时")
try:
    t0 = time.time()
    url = "http://hq.sinajs.cn/list=usAAPL,usGOOGL,usMSFT"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode('gbk')
    has_data = len(data.strip('\";')) > 100
    results['sina_us_realtime'] = has_data
    print(f"  {'OK' if results['sina_us_realtime'] else 'FAIL'}: {dt:.2f}s, len={len(data)}")
except Exception as e:
    results['sina_us_realtime'] = False
    print(f"  FAIL: {e}")

# 9. Yahoo Finance
print("\n[9] Yahoo Finance")
try:
    import yfinance as yf
    t0 = time.time()
    ticker = yf.Ticker("AAPL")
    hist = ticker.history(period="5d")
    dt = time.time() - t0
    results['yfinance_us'] = len(hist) > 0
    print(f"  {'OK' if results['yfinance_us'] else 'FAIL'}: {dt:.2f}s, {len(hist)} rows")
except Exception as e:
    results['yfinance_us'] = False
    print(f"  FAIL: {e}")

# 10. Google Finance
print("\n[10] Google Finance")
try:
    t0 = time.time()
    url = "https://www.google.com/finance/quote/AAPL:NASDAQ"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    resp = urllib.request.urlopen(req, timeout=10)
    dt = time.time() - t0
    data = resp.read().decode()
    import re
    prices = re.findall(r'data-last-price="([^"]+)"', data)
    results['google_finance'] = len(prices) > 0
    print(f"  {'OK' if results['google_finance'] else 'FAIL'}: {dt:.2f}s, prices={prices[:3]}")
except Exception as e:
    results['google_finance'] = False
    print(f"  FAIL: {e}")

# ========== 汇总 ==========
print("\n" + "=" * 70)
print("测试结果汇总")
print("=" * 70)

hk_ok = [k for k, v in results.items() if v and 'hk' in k.lower()]
us_ok = [k for k, v in results.items() if v and 'us' in k.lower()]
all_ok = [k for k, v in results.items() if v]

print(f"\n港股可用 ({len(hk_ok)}):")
for k in hk_ok:
    print(f"  - {k}")

print(f"\n美股可用 ({len(us_ok)}):")
for k in us_ok:
    print(f"  - {k}")

print(f"\n总计: {len(all_ok)}/{len(results)} 个API可用")

# ========== 推荐方案 ==========
print("\n" + "=" * 70)
print("推荐方案")
print("=" * 70)

print("""
A股:
  - 实时行情: Sina API (0.1s)
  - K线数据: Sina API (0.1s/batch)
  - 热门股: akshare stock_hot_follow_xq (13s)

港股:
  - 实时行情: 腾讯 API (0.1s) ✅ 推荐
  - 实时行情: Sina API (0.1s) ✅ 备选
  - 股票列表: 腾讯 hk_all (0.1s) ✅ 推荐
  - K线数据: 需进一步测试 (暂无免费可靠来源)

美股:
  - 实时行情: 腾讯 API (0.1s) ✅ 推荐
  - 股票列表: 腾讯 us_all (0.1s) ✅ 推荐
  - K线数据: Yahoo Finance (yfinance) ✅ 推荐
  - K线数据: Google Finance scraping (备选)
""")
