import requests, json, os

token = os.environ.get('GITHUB_TOKEN')
if not token:
    print("ERROR: GITHUB_TOKEN not set. Set it before running.")
    exit(1)

repo = 'SailorChina/tech-signal-skill'
tag = 'v2.16.1'

body = """## 新增
- **entry_type 字段**: 扫描结果显式标注入场方式（现价入场/回调入场/突破入场）
- **交易计划文本优化**: 买入策略说明增加偏离幅度
- **SKILL.md 规范化**: 添加 YAML frontmatter，符合 Codex Skill 标准格式

## 修复
- **格式化字符串 BUG**: screener.py .1f 被当作字符串拼接的问题已修复
- **基本面过滤 Symbol 前缀**: akshare 接口需要纯代码的问题已修复

## 依赖更新
- pyproject.toml version 更新至 2.16.1
- 移除 A股/港股支持，专注美股
- 清理遗留 debug 脚本和临时文件

## 快速开始
```bash
pip install tech-signal-skill
python -m stock_signals.cli scan --max-picks 5 --parallel
```

---
**完整文档**: https://github.com/SailorChina/tech-signal-skill
"""

url = 'https://api.github.com/repos/' + repo + '/releases'
headers = {
    'Authorization': 'token ' + token,
    'Content-Type': 'application/json',
}
data = {
    'tag_name': tag,
    'target_commitish': 'main',
    'name': 'tech-signal-skill ' + tag[1:],
    'body': body,
    'draft': False,
    'prerelease': False,
}
resp = requests.post(url, headers=headers, json=data, timeout=30)
print('Status:', resp.status_code)
if resp.status_code == 201:
    release = resp.json()
    print('Release URL:', release['html_url'])
else:
    print('Error:', resp.text[:500])
