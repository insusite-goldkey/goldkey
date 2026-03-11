lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()

# main() 함수 L22045부터 indent 추적
main_start = 22044  # 0-indexed
print("=== main() 내 indent=0 코드 블록 (탈출 후보) ===")
prev_ind4_line = None
for i in range(main_start + 1, min(main_start + 12000, len(lines))):
    ln = lines[i]
    stripped = ln.strip()
    if not stripped:
        continue
    # CSS 내용(멀티라인 문자열 안)은 건너뜀
    ind = len(ln) - len(ln.lstrip())
    if ind == 0 and not stripped.startswith('#'):
        # 실제 파이썬 코드인지 확인
        if any(stripped.startswith(kw) for kw in ['if ', 'def ', 'class ', 'for ', 'while ', 'try:', 'with ']):
            print(f'L{i+1}: {stripped[:100]}')
            if i+1 > 32380:
                # 이 범위면 출력 계속
                pass

# L32340~32346 — tab_home_btn 정의 확인
print("\n=== tab_home_btn 함수 컨텍스트 ===")
for i in range(32335, 32350):
    print(f'L{i+1} ind={len(lines[i])-len(lines[i].lstrip())}: {lines[i].rstrip()}')

# gk_sec09 라우터 위치 — cur == "gk_sec09" 탐색
print("\n=== cur == gk_sec09 라우터 위치 ===")
for i, ln in enumerate(lines):
    if 'cur == "gk_sec09"' in ln:
        ind = len(ln) - len(ln.lstrip())
        print(f'L{i+1} ind={ind}: {ln[:100].rstrip()}')
