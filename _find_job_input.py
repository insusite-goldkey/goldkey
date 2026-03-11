lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()

# 직업 관련 입력 필드
print("=== 직업 관련 text_input/selectbox ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if any(k in s for k in ['직업', 'job', 'occupation', '급수', 'risk_grade', 'job_grade']):
        if any(k in s for k in ['text_input', 'selectbox', 'session_state', 'radio', 'select']):
            print(f'L{i+1}: {s[:110]}')

# GK-SEC-01 구조 파악 — t0 탭 시작
print("\n=== t0 탭 구조 (직업 입력 포함 가능) ===")
in_t0 = False
for i, ln in enumerate(lines):
    s = ln.strip()
    if 'cur == "t0"' in s:
        in_t0 = True
    if in_t0:
        if any(k in s for k in ['직업', 'job', 'occupation', '급수', 'text_input', 'selectbox']):
            print(f'L{i+1}: {s[:110]}')
        if i > 34500:
            break

# _GP200_SEARCH_LIST 상단 구조 파악
print("\n=== _GP200_SEARCH_LIST L619 근방 ===")
for i in range(615, 665):
    print(f'L{i+1}: {lines[i].rstrip()[:110]}')
