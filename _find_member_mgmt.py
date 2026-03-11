lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()
# 회원 관리 / 총 회원수 관련 위치 찾기
for i, ln in enumerate(lines):
    lo = ln.lower()
    if any(k in ln for k in ['총 회원', '회원수', '회원 수', 'total_member', 'member_count',
                               '회원가입', 'register_user', 'save_user', '_user_list',
                               'user_count', '회원 관리']):
        if any(k in lo for k in ['def ', 'metric', 'len(', 'count', 'insert', 'upsert', 'session_state']):
            print(f'L{i+1}: {ln[:120].rstrip()}')
