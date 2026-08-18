
import sys
print("检查 Futu OpenAPI 安装状态...")

# 检查 Python 包
try:
    import futu
    print("  OK: futu 模块已安装")
except ImportError as e:
    print("  FAIL: futu 模块未安装: " + str(e))
    print("")
    print("建议安装命令:")
    print("  pip install futu-api")
    sys.exit(1)

# 检查 OpenD
import os
print("")
print("检查 Futu OpenD...")
opend_paths = [
    r'C:\Program Files\FutuOpenD\FutuOpenD.exe',
    r'C:\FutuOpenD\FutuOpenD.exe',
    r'D:\FutuOpenD\FutuOpenD.exe',
]

found = False
for p in opend_paths:
    if os.path.exists(p):
        print("  OK: 找到 OpenD: " + p)
        found = True
        break

if not found:
    print("  WARN: 未找到 OpenD 可执行文件")
    print("")
    print("建议:")
    print("  1. 下载 FutuOpenD: https://www.futunn.com/open")
    print("  2. 安装后运行 OpenD")
    print("  3. 默认端口: 11111")

# 测试连接
print("")
print("测试 Futu 连接...")
try:
    sys.path.insert(0, 'C:\\Users\\Administrator\\.codex\\skills\\futuapi\\scripts')
    from common import create_quote_context, check_ret, safe_close, RET_OK
    
    ctx = create_quote_context()
    print("  OK: 连接成功")
    
    # 测试港股K线
    print("")
    print("测试港股K线...")
    try:
        ret, data, _ = ctx.request_history_kline(
            "HK.00700", 
            ktype=ctx.K_1D, 
            autype=ctx.AU_QFQ, 
            max_count=10
        )
        if ret == 0 and data is not None and not data.empty:
            print("  OK: 港股K线成功: " + str(len(data)) + " rows")
            print("  最新: " + str(data.iloc[-1].to_dict()))
        else:
            print("  FAIL: 港股K线失败: ret=" + str(ret))
    except Exception as e:
        print("  FAIL: 港股K线异常: " + str(e))
    
    # 测试美股K线
    print("")
    print("测试美股K线...")
    try:
        ret, data, _ = ctx.request_history_kline(
            "US.AAPL", 
            ktype=ctx.K_1D, 
            autype=ctx.AU_QFQ, 
            max_count=10
        )
        if ret == 0 and data is not None and not data.empty:
            print("  OK: 美股K线成功: " + str(len(data)) + " rows")
            print("  最新: " + str(data.iloc[-1].to_dict()))
        else:
            print("  FAIL: 美股K线失败: ret=" + str(ret))
    except Exception as e:
        print("  FAIL: 美股K线异常: " + str(e))
    
    ctx.close()
    
except Exception as e:
    print("  FAIL: 连接失败: " + str(e))
    print("")
    print("可能原因:")
    print("  1. OpenD 未启动")
    print("  2. 端口 11111 被占用")
    print("  3. 防火墙阻止连接")
