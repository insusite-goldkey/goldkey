lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()

# main() 함수 내부에서 indent=0 인 라인 (함수 탈출 지점) 찾기
# main()은 L22045부터 시작
main_start = 22044  # 0-indexed
in_main = False
print("=== main() 내부에서 indent=0 코드 라인 (탈출 지점) ===")
count = 0
for i in range(main_start, len(lines)):
    ln = lines[i]
    stripped = ln.strip()
    if not stripped or stripped.startswith('#'):
        continue
    ind = len(ln) - len(ln.lstrip())
    if i == main_start:
        continue  # def main(): 자체 건너뜀
    if ind == 0 and stripped:
        print(f'L{i+1} ind=0: {stripped[:100]}')
        count += 1
        if count >= 20:
            print("... (truncated)")
            break

# tab_home_btn 함수 위치
print("\n=== tab_home_btn 정의/끝 ===")
for i, ln in enumerate(lines):
    if 'def tab_home_btn' in ln:
        print(f'def L{i+1}: {ln[:80].rstrip()}')
    if i+1 in range(32355, 32390):
        ind = len(ln) - len(ln.lstrip())
        if ind <= 4 and ln.strip():
            print(f'L{i+1} ind={ind}: {ln[:80].rstrip()}')
