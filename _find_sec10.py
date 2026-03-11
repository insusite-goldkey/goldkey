lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()

# GK-SEC-10 탭 라우터
print("=== GK-SEC-10 라우터 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if 'gk_sec10' in s.lower() or 'sec10' in s.lower() or '내보험다보여' in s or '마이데이터' in s:
        print(f'L{i+1}: {s[:110]}')

# SEC-01 구조 (입력 간소화 대상)
print("\n=== GK-SEC-01 라우터 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if 'gk_sec01' in s.lower() or 'sec_01' in s.lower():
        if any(k in s for k in ['cur ==', 'tab_key', 'def ', 'if cur']):
            print(f'L{i+1}: {s[:110]}')

# 탭 버튼 목록에서 sec10 찾기
print("\n=== 탭 버튼 목록 (TABS / tab_home_btn) ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if 'gk_sec' in s.lower() and any(k in s for k in ['"gk_sec', "'gk_sec", 'tab_key']):
        print(f'L{i+1}: {s[:110]}')
