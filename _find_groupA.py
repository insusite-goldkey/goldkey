content = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

keywords = [
    '그룹 A', '그룹A', '고객 기본 정보', '액션 그리드', '액션그리드',
    '시니어', 'senior', '새로고침', '고객선택', '이름검색',
    'gs_c_name', 'c_name', '성명', '직업', '생년월일',
    'action_grid', 'group_a', 'groupA'
]

for kw in keywords:
    idx = content.find(kw)
    if idx != -1:
        line = content[:idx].count('\n') + 1
        snip = content[idx:idx+100].replace('\n', ' ')
        print(f'[{kw}] L{line}: {snip}')
