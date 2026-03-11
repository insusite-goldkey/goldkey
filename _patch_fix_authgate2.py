# -*- coding: utf-8 -*-
"""
_render_report_send_ui 함수 본문(4칸)이 _auth_gate + main() 전체를 삼키고 있음.
수정: _render_report_send_ui 본문 끝(L30709 빈줄) 이후 4칸으로 시작하는
주석 블록 + 'def _auth_gate' 를 0칸으로 dedent 하여 top-level로 복원.

실제 문제:
- L30638 def _render_report_send_ui(  ← 0칸 (top-level)
- L30639~L30708 본문  ← 4칸 (정상)
- L30709 빈줄
- L30710~L30713 주석  ← 4칸 (아직 함수 본문 안)
- L30714 '    def _auth_gate(…):'  ← 4칸 → 중첩 함수가 됨
- L30715 '    """docstring"""'   ← 4칸 → def 선언과 같은 줄 수준 → 오류

해결: L30710 이후 전체를 4칸 dedent (즉 4칸 → 0칸, 8칸 → 4칸 …)
범위: L30710 ~ (main() 시작 직전 또는 파일 끝)
단 main() 내부는 건드리면 안 되므로, _auth_gate 블록이 끝나는 지점까지만.
"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

# _render_report_send_ui 함수 끝 이후 첫 번째 4칸-시작 주석 라인 찾기
# = L30710 (0-based: 30709)
DEDENT_START = 30709  # 0-based (L30710)

# dedent 범위 끝: main() 함수 정의 라인 찾기 (0칸 'def main():')
main_line = None
for i in range(DEDENT_START, len(lines)):
    if lines[i].startswith('def main():') or lines[i].startswith('def main() ->'):
        main_line = i
        break

if main_line is None:
    # fallback: _run_safe 찾기
    for i in range(DEDENT_START, len(lines)):
        if lines[i].startswith('def _run_safe('):
            main_line = i
            break

if main_line is None:
    print("ERROR: main() not found")
    exit(1)

print(f"DEDENT range: L{DEDENT_START+1} ~ L{main_line} (0-based {DEDENT_START}~{main_line-1})")
print(f"main() at: L{main_line+1}")

# 범위 내 모든 줄을 4칸 dedent
# 조건: 줄이 4칸 이상으로 시작할 때만 4칸 제거
# 빈 줄은 그대로
fixed_lines = []
for i in range(DEDENT_START, main_line):
    ln = lines[i]
    if ln.strip() == '':
        fixed_lines.append('\n')
    elif ln.startswith('    '):
        fixed_lines.append(ln[4:])
    else:
        # 이미 0칸이거나 다른 들여쓰기 → 그대로
        fixed_lines.append(ln)

lines = lines[:DEDENT_START] + fixed_lines + lines[main_line:]

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("DONE: dedent applied to _auth_gate block")
