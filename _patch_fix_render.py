# -*- coding: utf-8 -*-
"""
_render_report_send_ui 함수 본문 들여쓰기 수정
def 선언은 0칸인데 본문이 8칸 → 4칸으로 조정
함수 끝은 next top-level def/class 앞까지
"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

# 함수 시작 라인 찾기 (0-based)
func_start = None
for i, ln in enumerate(lines):
    if ln.startswith('def _render_report_send_ui('):
        func_start = i
        break

if func_start is None:
    print("ERROR: func not found")
    exit(1)

print(f"func_start (0-based): {func_start}, line {func_start+1}")
print(repr(lines[func_start]))
print(repr(lines[func_start+1]))  # 첫 번째 본문 줄

# 함수 끝 찾기: 다음 top-level def/class (들여쓰기 0칸)
func_end = None
for i in range(func_start + 1, len(lines)):
    ln = lines[i]
    if ln and not ln[0].isspace() and ln.strip() and not ln.strip().startswith('#'):
        # top-level 코드 발견
        func_end = i
        break

if func_end is None:
    print("ERROR: func end not found")
    exit(1)

print(f"func_end (0-based): {func_end}, line {func_end+1}")
print(repr(lines[func_end]))

# 함수 본문 들여쓰기 확인
body_lines = lines[func_start+1 : func_end]
# 비어있지 않은 첫 줄의 들여쓰기 측정
first_nonempty = next((l for l in body_lines if l.strip()), None)
if first_nonempty is None:
    print("ERROR: no body lines")
    exit(1)

indent_count = len(first_nonempty) - len(first_nonempty.lstrip())
print(f"Body indent: {indent_count} spaces")

if indent_count == 4:
    print("Body indent is already 4 — no change needed")
    exit(0)

if indent_count == 8:
    # 8칸 → 4칸으로 축소
    print("Fixing 8-space indent → 4-space indent")
    fixed_body = []
    for ln in body_lines:
        if ln.strip() == '':
            fixed_body.append('\n')
        elif ln.startswith('        '):  # 8칸 이상
            fixed_body.append(ln[4:])   # 4칸 제거
        elif ln.startswith('    '):      # 4칸 (예: 내부 주석)
            fixed_body.append(ln)       # 그대로
        else:
            fixed_body.append(ln)
    lines = lines[:func_start+1] + fixed_body + lines[func_end:]
    print("Done fixing indent")
else:
    print(f"Unexpected indent {indent_count} — manual check needed")
    exit(1)

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("SAVED")
