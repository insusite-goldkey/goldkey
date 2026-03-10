
import subprocess

# 각 커밋별로 home 탭 크기 확인
commits = ['32bf174','09d393c','6037951','401b7db','01af2d1','2ea750f','f7d90d5','e632778','3201f5a','222ca43']

for c in commits:
    result = subprocess.run(['git', 'show', f'{c}:app.py'], capture_output=True)
    if result.returncode != 0:
        print(f"{c}: ERROR")
        continue
    data = result.stdout.decode('utf-8-sig', errors='replace')
    idx = data.find('    if cur == "home":')
    next_block = data.find('\n    # \u2550\u2550', idx + 100)
    if idx < 0:
        print(f"{c}: home 탭 없음")
        continue
    chunk = data[idx:next_block]
    lines = chunk.count('\n')
    print(f"{c}: home 탭 {lines}줄")
