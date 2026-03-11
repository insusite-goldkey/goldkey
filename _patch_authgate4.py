with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

# _auth_gate 함수 시작 찾기
ag_start = None
for i, ln in enumerate(lines):
    if ln.startswith('def _auth_gate('):
        ag_start = i
        break

if ag_start is None:
    print("ERROR: _auth_gate not found")
    exit(1)

print(f"_auth_gate at L{ag_start+1}")

# 함수 본문 범위: ag_start+1 부터 다음 top-level def/class 직전까지
ag_end = None
for i in range(ag_start + 1, len(lines)):
    ln = lines[i]
    if ln.strip() == '':
        continue
    if not ln[0].isspace() and (ln.startswith('def ') or ln.startswith('class ') or ln.startswith('@')):
        ag_end = i
        break

if ag_end is None:
    print("ERROR: _auth_gate end not found")
    exit(1)

print(f"_auth_gate body: L{ag_start+2}~L{ag_end} (next def at L{ag_end+1})")
print("First body lines:")
for ln in lines[ag_start+1:ag_start+5]:
    print(repr(ln))

# 본문 첫 줄 들여쓰기 확인
first_body = lines[ag_start + 1]
indent = len(first_body) - len(first_body.lstrip()) if first_body.strip() else 0
print(f"Body indent: {indent}")

if indent == 4:
    print("Already 4-indented — no fix needed")
    exit(0)

# 0칸 본문 → 4칸으로 변환
fixed_body = []
for i in range(ag_start + 1, ag_end):
    ln = lines[i]
    if ln.strip() == '':
        fixed_body.append('\n')
    else:
        fixed_body.append('    ' + ln)

lines = lines[:ag_start + 1] + fixed_body + lines[ag_end:]

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("DONE: _auth_gate body re-indented to 4 spaces")
