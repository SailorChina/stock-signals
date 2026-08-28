import urllib.request, re, os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10809'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10809'
queries = [
    'trading journal app features equity curve win rate by sector',
    'streamlit dashboard best practices 2024 charts metrics',
    'best trading journal UI design examples features',
]
for q in queries:
    url = f'https://html.duckduckgo.com/html/?q={urllib.request.quote(q)}'
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    r = urllib.request.urlopen(req, timeout=15)
    html = r.read().decode('utf-8')
    snippets = re.findall(r'class=\ result__snippet\[^>]*>([^<]+)', html)
    titles = re.findall(r'result__title[^>]*>([^<]+)<', html)
    print(f'=== {q} ===')
    for t, s in zip(titles[:5], snippets[:5]):
        print(f'Title: {t.strip()}')
        print(f'Snippet: {s.strip()[:250]}')
        print('---')