lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()

# GK-SEC-09 탭 시작 위치
print("=== GK-SEC-09 탭 라우터 위치 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if 'gk_sec09' in s and 'cur ==' in s:
        print(f'L{i+1}: {s[:100]}')

# SEC-09 내 text_input 위치들
print("\n=== GK-SEC-09 내 text_input ===")
in_sec09 = False
for i, ln in enumerate(lines):
    s = ln.strip()
    if 'cur == "gk_sec09"' in s:
        in_sec09 = True
    if in_sec09 and 'text_input' in s:
        print(f'L{i+1}: {s[:120]}')
    if in_sec09 and i > 30200:
        break

# GK-SEC-01 내 회사명/법인명 입력 필드
print("\n=== GK-SEC-01 내 회사명 입력 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if any(k in s for k in ['법인명', '회사명', 'company', 'corp_name', 'se_company', 'company_name']):
        if 'text_input' in s:
            print(f'L{i+1}: {s[:120]}')

# gp200_search_companies 함수 - 현재 DB 구조 파악
print("\n=== _GP200_SEARCH_LIST 초기화 위치 ===")
for i, ln in enumerate(lines):
    if '_GP200_SEARCH_LIST' in ln.strip():
        print(f'L{i+1}: {ln.strip()[:100]}')
