
import subprocess

# 01af2d1 이전 버전(2ea750f)의 home 탭 내용 추출
result = subprocess.run(['git', 'show', '2ea750f:app.py'], capture_output=True)
data = result.stdout.decode('utf-8-sig', errors='replace')
idx = data.find('    if cur == "home":')
next_block = data.find('\n    # \u2550\u2550', idx + 100)
chunk = data[idx:next_block]

# 구조 파악
lines = chunk.splitlines()
print(f"총 {len(lines)}줄\n")
for i, line in enumerate(lines):
    stripped = line.strip()
    if (stripped.startswith('# ──') or stripped.startswith('# ══') or 
        stripped.startswith('st.subheader') or stripped.startswith('st.header') or
        stripped.startswith('## ') or 'gk-g220' in stripped or
        stripped.startswith('_scan_left') or stripped.startswith('_pc') or
        ('columns' in stripped and 'st.' in stripped)):
        print(f"L{i:04d}: {line[:120]}")
