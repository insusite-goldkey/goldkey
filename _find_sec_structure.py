lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()

# SECTOR_CODES 에서 sec 탭 목록 찾기
print("=== SECTOR_CODES 내 SEC 항목 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if any(k in s for k in ['1100', '1200', '1300', '0100', '0200', '0300', 'gk-sec-01', 'gk-sec-10', 'sec01', 'sec_01', 'sec10']):
        if 'sec' in s.lower() or 'SEC' in s or '진단' in s:
            print(f'L{i+1}: {s[:110]}')

# tab_home_btn 전체 목록
print("\n=== tab_home_btn 정의부 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if 'tab_home_btn' in s and ('def ' in s or '=' in s):
        print(f'L{i+1}: {s[:110]}')

# TABS 딕셔너리 상단 - 탭 전체 목록
print("\n=== TABS/GK 섹터 탭 네비게이션 리스트 (L8180~8220) ===")
for i in range(8180, 8230):
    print(f'L{i+1}: {lines[i].rstrip()[:110]}')

# 탭 버튼 렌더링 위치 (사이드바 탭 목록 내 GK-SEC 항목들)
print("\n=== 사이드바 탭 버튼 GK-SEC 목록 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if any(k in s for k in ['GK-SEC', 'gk_sec', '진단', '내보험']):
        if any(k in s for k in ['button', 'tab_key', 'label', '"name"', "'name'"]):
            print(f'L{i+1}: {s[:110]}')

# 기존 if cur == "gk_sec..." 라우터 블록 전체
print("\n=== if cur == gk_sec 라우터 전체 목록 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if s.startswith('if cur ==') and 'gk_sec' in s:
        print(f'L{i+1}: {s[:110]}')
