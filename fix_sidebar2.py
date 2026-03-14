"""
사이드바 전체 블록(line 32134~33941)을 미인증 st.stop()(line 28906) 앞으로 이동.

현재 문제:
  line 28903~28906: with st.sidebar: render_goldkey_sidebar() + st.stop()
  line 32134~33941: 실제 사이드바 로그인 폼 전체 (with st.sidebar: ... )
  → st.stop()이 먼저 실행되어 로그인 폼이 절대 렌더되지 않음

수정 후:
  line 28698~28906 영역: 사이드바 전체 블록 먼저 렌더 → st.stop()
  line 32134~33941: 삭제 (이미 앞으로 이동됨)
"""

SRC = "D:/CascadeProjects/app.py"

with open(SRC, encoding="utf-8") as f:
    lines = f.readlines()

total = len(lines)
print(f"총 라인: {total}")

# ── 경계 확인 ──────────────────────────────────────────────────────────────
# 사이드바 블록 시작: line 32134 (0-indexed: 32133) "    # ── 사이드바 ──"
# 사이드바 블록 끝:   line 33941 (0-indexed: 33940) "                # ── [GP200 §4] 끝"
# 이후 빈줄 1개(33941, 0-indexed: 33941)도 포함해서 제거

SIDEBAR_START = 32133   # 0-indexed inclusive  (line 32134: "    # ── 사이드바 ──")
SIDEBAR_END   = 33941   # 0-indexed exclusive  (line 33942: 빈줄, line 33943: "    # ── [절대 생존 구조]")

# 삽입 위치: 임시 3줄(★근본수정 주석+with st.sidebar+render) 바로 앞
# line 28903~28905 (0-indexed 28902~28904) = 임시 3줄
# line 28906 (0-indexed 28905) = "        st.stop()\n"  → 유지
INSERT_AT = 28902  # 0-indexed — "        # ── [★근본수정]..." 줄

print(f"사이드바 블록: line {SIDEBAR_START+1} ~ {SIDEBAR_END} ({SIDEBAR_END - SIDEBAR_START} 라인)")
print(f"삽입 위치:     line {INSERT_AT+1}")

# 경계 검증
print(f"\n[SIDEBAR_START] {repr(lines[SIDEBAR_START])}")
print(f"[SIDEBAR_END-1] {repr(lines[SIDEBAR_END-1])}")
print(f"[INSERT_AT]     {repr(lines[INSERT_AT])}")
print(f"[INSERT_AT+3]   {repr(lines[INSERT_AT+3])}")  # st.stop()

# ── 블록 추출 ──────────────────────────────────────────────────────────────
sidebar_block = lines[SIDEBAR_START:SIDEBAR_END]
print(f"\n추출된 사이드바 블록 라인 수: {len(sidebar_block)}")

# ── 블록 제거 ──────────────────────────────────────────────────────────────
remaining = lines[:SIDEBAR_START] + lines[SIDEBAR_END:]
print(f"블록 제거 후 라인 수: {len(remaining)}")

# ── INSERT_AT은 블록 제거 후 인덱스가 그대로 (INSERT_AT < SIDEBAR_START) ──
assert INSERT_AT < SIDEBAR_START, "삽입 위치가 블록보다 앞이어야 함"

# ── 이전에 삽입한 임시 3줄 제거 (이미 with st.sidebar: render_goldkey_sidebar() 존재)
# remaining[INSERT_AT] = "        # ── [★근본수정]..."
# remaining[INSERT_AT+1] = "        with st.sidebar:\n"
# remaining[INSERT_AT+2] = "            render_goldkey_sidebar()\n"
# remaining[INSERT_AT+3] = "        st.stop()\n"
# → 임시 3줄(INSERT_AT ~ INSERT_AT+2) 제거하고 sidebar_block 삽입 후 st.stop()

print(f"\n[제거 대상 임시줄]")
for i in range(INSERT_AT, INSERT_AT+4):
    print(f"  [{i+1}] {repr(remaining[i])}")

# 임시 3줄 제거: INSERT_AT, INSERT_AT+1, INSERT_AT+2 (★근본수정 주석 + with st.sidebar + render_goldkey_sidebar)
before = remaining[:INSERT_AT]
after  = remaining[INSERT_AT+3:]  # INSERT_AT+3부터 = "        st.stop()\n" 유지

# sidebar_block 앞에 빈줄 구분 추가
separator = "    # ── 사이드바 (미인증 st.stop() 전 이동) ─────────────────────────────\n"
new_lines = before + [separator] + sidebar_block + after

print(f"\n최종 라인 수: {len(new_lines)}")
print(f"[삽입 후 확인]")
for i in range(INSERT_AT, INSERT_AT+5):
    print(f"  [{i+1}] {repr(new_lines[i])}")

# ── 저장 ──────────────────────────────────────────────────────────────────
with open(SRC, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("\n완료: app.py 저장됨")
