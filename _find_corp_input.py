lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()

# GK-SEC-01 고객정보 입력 관련 위치
print("=== GK-SEC-01 고객정보 입력 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if any(k in s for k in ['고객명', 'c_name', 'client_name', '회사명', 'company_name', 'corp_name', '사업체', '고객 이름']):
        if any(k in s for k in ['text_input', 'input', 'session_state', 'gs_c_name']):
            print(f'L{i+1}: {s[:110]}')

print("\n=== GK-SEC-09 법인 상담 상호 입력 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if any(k in s for k in ['gk_sec09', 'sec09', '9900', '9910', '9920', '9930', '9940', '9950', '9960']):
        if any(k in s for k in ['text_input', '회사명', '상호', 'corp', 'company']):
            print(f'L{i+1}: {s[:110]}')

# gp200_company 관련 — 사이드바 전문가 브랜딩에 이미 자동완성 있는지 확인
print("\n=== gp200 브랜딩 입력 자동완성 현황 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if 'gp200' in s and any(k in s for k in ['text_input', 'autocomplete', 'suggestion', 'search_companies']):
        print(f'L{i+1}: {s[:110]}')

# _corp_autocomplete 또는 유사 함수 탐색
print("\n=== 기존 법인 자동완성 함수 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if any(k in s for k in ['corp_db', 'CORP_DB', 'corp_list', 'search_companies', 'gp200_search', 'autocomplete']):
        print(f'L{i+1}: {s[:110]}')
