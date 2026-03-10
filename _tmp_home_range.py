
data = open('app.py', encoding='utf-8-sig').read()
lines = data.splitlines()

# cur == "home" 블록 시작/끝 라인 번호 찾기
start_line = None
end_line = None
for i, line in enumerate(lines):
    if '    if cur == "home":' in line and start_line is None:
        start_line = i + 1  # 1-indexed
for i, line in enumerate(lines):
    if i > (start_line or 0) and line.startswith('    # \u2550\u2550'):
        end_line = i + 1
        break

print(f"home 탭: line {start_line} ~ {end_line}")
print(f"총 {end_line - start_line}줄")

# 기존에 사용되는 핵심 함수/변수 키 파악
chunk = '\n'.join(lines[start_line-1:end_line-1])
import re

# 세션 키 목록
keys = set(re.findall(r'session_state\[[\'"]([\w_]+)[\'"]\]', chunk))
print("\n사용 세션 키:")
for k in sorted(keys):
    print(f"  {k}")

# 호출 함수 목록
funcs = set(re.findall(r'(\b_\w+)\s*\(', chunk))
print("\n주요 내부 함수 호출:")
for f in sorted(funcs)[:30]:
    print(f"  {f}")
