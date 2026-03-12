content = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

# gk-rb-btn div 래퍼와 시니어 버튼 실제 렌더링 찾기
keywords = [
    'gk-rb-btn',
    '시니어',
    'senior',
    'btn_senior',
    'btn_refresh_client',
    '고객 검색',
    '고객검색',
]

results = []
for kw in keywords:
    idx = 0
    while True:
        idx = content.find(kw, idx)
        if idx == -1:
            break
        line = content[:idx].count('\n') + 1
        if line > 29000:  # CSS 이후 실제 코드 범위
            snip = content[idx:idx+150].replace('\n', ' ')
            results.append((line, kw, snip))
        idx += len(kw)

results.sort()
for line, kw, snip in results:
    print(f'L{line} [{kw}]: {snip}')
