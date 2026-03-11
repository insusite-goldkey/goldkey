lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()

# L32142부터 main() 끝(L51865)까지 indent=0인 실제 코드 블록 파악
print("=== indent=0 탈출 코드 블록 (L32142~) ===")
for i in range(32141, len(lines)):
    ln = lines[i]
    stripped = ln.strip()
    if not stripped or stripped.startswith('#'):
        continue
    ind = len(ln) - len(ln.lstrip())
    if ind == 0:
        if any(stripped.startswith(kw) for kw in ['def ', 'if ', 'class ', 'for ', 'while ', 'try:', 'with ', '@']):
            print(f'L{i+1}: {stripped[:90]}')

# main() 내부 마지막 실제 실행 코드 (L32141 직전)
print("\n=== main() 마지막 실행 코드 (L32126~32142) ===")
for i in range(32125, 32143):
    print(f'L{i+1} ind={len(lines[i])-len(lines[i].lstrip())}: {lines[i].rstrip()[:100]}')
