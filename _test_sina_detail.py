
import urllib.request
import json

print("=== Sina 详细接口测试 ===")

# 1. 测试Sina港股详细接口
print("\n[1] Sina 港股详细行情")
try:
    url = "http://hq.sinajs.cn/list=hk00700,hk00001,hk0939,hk09988,hk02382"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode('gbk')
    print(f"返回: {data}")
    
    lines = data.strip().split(';')
    for line in lines:
        if '=' in line:
            var_name, content = line.split('=', 1)
            content = content.strip('\"')
            parts = content.split(',')
            if len(parts) > 3:
                print(f"  {parts[0]}: 当前={parts[3]}, 涨跌={parts[4]}, 开盘={parts[5]}, 最高={parts[6]}, 最低={parts[7]}")
except Exception as e:
    print(f"ERROR: {e}")

# 2. 测试Sina美股详细接口
print("\n[2] Sina 美股详细行情")
try:
    url = "http://hq.sinajs.cn/list=usAAPL,usGOOGL,usMSFT,usTSLA"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode('gbk')
    print(f"返回: {data}")
    
    lines = data.strip().split(';')
    for line in lines:
        if '=' in line and len(line.split('=', 1)[1].strip('\"')) > 10:
            var_name, content = line.split('=', 1)
            content = content.strip('\"')
            parts = content.split(',')
            if len(parts) > 3:
                print(f"  {parts[0]}: 当前={parts[1]}, 时间={parts[2]}")
except Exception as e:
    print(f"ERROR: {e}")

# 3. 测试Sina A股K线
print("\n[3] Sina A股K线格式")
try:
    url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh600519&scale=240&ma=no&datalen=5"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "http://finance.sina.com.cn/"})
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode()
    print(f"返回: {data[:500]}")
    
    items = json.loads(data)
    for item in items[-3:]:
        print(f"  {item}")
except Exception as e:
    print(f"ERROR: {e}")
