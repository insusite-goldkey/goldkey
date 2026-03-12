content = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

# 이미지에서 보이는 버튼들: 새로고침, 시니어, 고객검색
# 실제 버튼 렌더링 라인 (L37000 이후 집중 탐색)
keywords = [
    'btn_cust_search',   # 새로고침 버튼 키
    '🔍 새로고침',
    '🔍 고객',
    '돋보기',
    '시니어',
    'gk-rb-btn',
]

for kw in keywords:
    idx = 0
    while True:
        idx = content.find(kw, idx)
        if idx == -1:
            break
        line = content[:idx].count('\n') + 1
        if line >= 37000:
            snip = content[idx:idx+200].replace('\n', ' ')
            print(f'L{line} [{kw}]: {snip}')
        idx += len(kw)
