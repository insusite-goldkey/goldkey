lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()

# cur 정의 위치 L27117의 들여쓰기 확인
line = lines[27116]
indent = len(line) - len(line.lstrip())
print(f'L27117 indent={indent}: {line[:80].rstrip()}')

# L32382 바로 앞 30줄 들여쓰기 패턴 확인
print("\n=== L32350~32385 indent pattern ===")
for i in range(32349, 32385):
    ln = lines[i]
    ind = len(ln) - len(ln.lstrip())
    stripped = ln.strip()
    if stripped:
        print(f'L{i+1} ind={ind}: {stripped[:80]}')

# main() 함수 시작/끝 찾기
print("\n=== def main() positions ===")
for i, ln in enumerate(lines):
    if ln.strip().startswith('def main(') or ln.strip() == 'main()':
        print(f'L{i+1}: {ln[:80].rstrip()}')
