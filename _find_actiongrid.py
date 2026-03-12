content = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

keywords = [
    '시니어', 'senior_mode', '시니어 모드', '시니어버튼', 'gk-rb-btn',
    '액션 그리드', 'action_grid', 'rb_btn', 'gk_rb',
    '새로고침', 'btn_refresh', 'refresh',
]

for kw in keywords:
    idx = 0
    count = 0
    while True:
        idx = content.find(kw, idx)
        if idx == -1 or count > 5:
            break
        line = content[:idx].count('\n') + 1
        snip = content[idx:idx+120].replace('\n', ' ')
        print(f'[{kw}] L{line}: {snip}')
        idx += len(kw)
        count += 1
    if count == 0:
        print(f'[{kw}] NOT FOUND')
