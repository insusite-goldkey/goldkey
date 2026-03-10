
data = open('app.py', encoding='utf-8-sig').read()
# cur == "home" 블록 전체 찾기
idx = data.find('    if cur == "home":')
# 다음 최상위 if 블록 찾기
next_block = data.find('\n    # ══', idx + 100)
chunk = data[idx:next_block]
print(f"home 탭 코드 길이: {len(chunk)} chars, lines: {chunk.count(chr(10))}")
# 내용 구조 파악 (주석줄만 추출)
for i, line in enumerate(chunk.splitlines()):
    stripped = line.strip()
    if stripped.startswith('#') or stripped.startswith('def ') or stripped.startswith('if ') or stripped.startswith('with ') or stripped.startswith('st.markdown') or stripped.startswith('st.subheader') or stripped.startswith('st.columns'):
        print(f"  L{i}: {line[:100]}")
