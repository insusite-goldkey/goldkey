# -*- coding: utf-8 -*-
"""
두 가지 문제를 한 번에 수정:
1. _render_report_send_ui 이후 4칸 주석+def _auth_gate 블록이
   여전히 4칸으로 남아 있음 → 이 블록들을 0칸으로 dedent
2. _auth_gate 본문(docstring 포함)이 0칸으로 잘려 있음 → 4칸으로 복원
"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

# ── 1. _render_report_send_ui 함수 마지막 줄 찾기 (함수 본문 끝) ─────────────
# 함수 시작
func_start = None
for i, ln in enumerate(lines):
    if ln.startswith('def _render_report_send_ui('):
        func_start = i
        break

print(f"_render_report_send_ui start: L{func_start+1}")

# 함수 끝: 다음 0칸 def/class/non-comment 코드
# _render_report_send_ui 본문은 4칸 들여쓰기
# 함수 끝 이후에 4칸으로 시작하는 주석+def _auth_gate 가 있음
# → 이들을 0칸으로 변환하면서 _auth_gate 본문을 4칸으로 보장

# 현재 상황 스캔: func_start 이후 첫 번째 top-level 구조 찾기
print("\n=== 주요 라인 덤프 (30705~30740) ===")
for i in range(30704, min(30740, len(lines))):
    ln = lines[i]
    indent = len(ln) - len(ln.lstrip()) if ln.strip() else -1
    print(f"L{i+1}({indent:2d}): {repr(ln[:80])}")

print("\n=== 분석 완료 ===")
