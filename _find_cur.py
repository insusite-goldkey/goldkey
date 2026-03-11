lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()
# cur = 정의 위치 탐색
for i, ln in enumerate(lines):
    stripped = ln.strip()
    if stripped.startswith('cur =') or stripped.startswith('cur='):
        print(f'DEF L{i+1}: {ln[:120].rstrip()}')
    if i+1 == 32382:
        print(f'\n=== L32382 context ===')
        for j in range(max(0,i-5), min(len(lines), i+5)):
            print(f'L{j+1}: {lines[j].rstrip()}')
