# -*- coding: utf-8 -*-
"""
라인 30600~30603의 잘못된 주석 잔재 제거 +
_rag_annotate_report 함수 위치 수정 (main() 밖으로)
"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

# ── 문제 구조 ────────────────────────────────────────────────────────────────
# 30599: 빈줄
# 30600:     # ══ [GP240조] 보고서 발송 공통 UI 헬퍼 ══
# 30601:     # ══ ...
# 30602:     # ══ ...
# 30603:     (빈줄)
# 30604: def _rag_annotate_report(...)   ← 4칸 들여쓰기 없이 삽입됨 (OK)
# ...
# 30641: def _render_report_send_ui(     ← 역시 0들여쓰기 (OK)
# ...
# 30713:     # [아키텍처 — 중앙 인증 게이트]  ← 4칸 (main() 내부)
# 30717:     def _auth_gate(...)          ← 4칸 들여쓰기 (main() 내부 중첩 함수)

# 오류 원인: 30600~30603의 4칸 주석 블록이
# _render_report_send_ui 안에 남아 있어서
# Python이 그 뒤의 def _rag_annotate_report를
# 함수 본문 안이라고 착각 → unindent error

# 해결: 30600~30603 주석 블록을 삭제 (이 주석들은 _render_report_send_ui 위에 있어야 함)

# 0-based index
idx_start = None
for i, line in enumerate(lines):
    if '# [GP240조] 보고서 발송 공통 UI 헬퍼' in line:
        idx_start = i
        break

if idx_start is None:
    print("ERROR: GP240 comment not found")
    exit(1)

print(f"Found GP240 comment at line {idx_start+1}")
print(repr(lines[idx_start]))
print(repr(lines[idx_start-1]))
print(repr(lines[idx_start+1]))

# 이 주석 블록이 4칸 들여쓰기로 시작하는지 확인
if lines[idx_start].startswith('    #'):
    # 4칸 들여쓰기 → 주석 2줄 + 구분선까지 찾아서 삭제
    # 찾기: idx_start-1부터 빈줄이나 def가 나올 때까지의 주석 블록
    block_start = idx_start
    # 바로 앞 줄이 빈줄이면 포함
    if lines[idx_start-1].strip() == '':
        block_start = idx_start - 1

    block_end = idx_start
    while block_end < len(lines) and (
        lines[block_end].strip().startswith('#') or
        lines[block_end].strip() == ''
    ):
        block_end += 1
        # 다음 줄이 def 또는 비어있지 않은 코드면 중단
        if block_end < len(lines) and not lines[block_end].strip().startswith('#') and lines[block_end].strip() != '':
            break

    print(f"Removing lines {block_start+1}~{block_end} (0-based {block_start}~{block_end-1})")
    for ln in lines[block_start:block_end]:
        print("  DEL:", repr(ln))

    # 삭제
    lines = lines[:block_start] + lines[block_end:]
    print("Lines removed OK")
else:
    print("Comment is NOT 4-space indented — no removal needed")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("DONE: indent fix applied")
