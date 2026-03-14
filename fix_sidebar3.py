"""
현재 상태:
  line 28698~28902: if not _is_auth_now: (메인 로그인폼, st.stop() 없음)
  line 28907~30712: with st.sidebar: ... st.stop()  ← if 밖에 있어서 항상 실행됨

수정:
  with st.sidebar 블록(28907~30712)을 if not _is_auth_now: 블록 안으로 이동
  즉 if not _is_auth_now: 블록 마지막(line 28902) 뒤에 삽입하고
  기존 28903~30712 자리는 삭제
"""

SRC = "D:/CascadeProjects/app.py"

with open(SRC, encoding="utf-8") as f:
    lines = f.readlines()

total = len(lines)
print(f"총 라인: {total}")

# ── 경계 확인 ──────────────────────────────────────────────────────────────
# if not _is_auth_now: 블록 끝: line 28902 (0-indexed 28901)
# with st.sidebar 블록 시작: line 28903 (0-indexed 28902) "    # ── 사이드바 (미인증..."
# with st.sidebar 블록 끝: line 30712 (0-indexed 30711) "        st.stop()"
# line 30713 (0-indexed 30712): 빈줄

# 검증
IF_BLOCK_END_IDX  = 28901   # 0-indexed, line 28902: st.error(f"변경 실패...")
SIDEBAR_START_IDX = 28902   # 0-indexed, line 28903: "    # ── 사이드바 (미인증..."
SIDEBAR_END_IDX   = 30713   # 0-indexed exclusive (line 30712=st.stop(), line 30713=빈줄 포함)

print(f"\n[IF_BLOCK_END]   line {IF_BLOCK_END_IDX+1}: {repr(lines[IF_BLOCK_END_IDX][:70])}")
print(f"[SIDEBAR_START]  line {SIDEBAR_START_IDX+1}: {repr(lines[SIDEBAR_START_IDX][:70])}")
print(f"[SIDEBAR_END-1]  line {SIDEBAR_END_IDX}:   {repr(lines[SIDEBAR_END_IDX-1][:70])}")
print(f"[SIDEBAR_END]    line {SIDEBAR_END_IDX+1}:   {repr(lines[SIDEBAR_END_IDX][:70])}")

# ── 사이드바 블록 추출 (SIDEBAR_START_IDX ~ SIDEBAR_END_IDX-1) ─────────────
# 단, 맨 앞 주석줄("    # ── 사이드바 (미인증 st.stop() 전 이동)") 제거
# 원래 블록은 "    # ── 사이드바 ──" 주석으로 시작하므로 그 줄부터 사용
sidebar_raw = lines[SIDEBAR_START_IDX:SIDEBAR_END_IDX]

# 첫 줄이 임시 주석인 경우 제거 (내용 확인)
print(f"\n사이드바 블록 첫 줄: {repr(sidebar_raw[0][:80])}")
print(f"사이드바 블록 마지막 줄: {repr(sidebar_raw[-1][:80])}")
print(f"사이드바 블록 라인 수: {len(sidebar_raw)}")

# 첫 줄이 "    # ── 사이드바 (미인증" 임시 주석이면 제거하고
# 원래 "    # ── 사이드바 ──" 주석은 유지
if "미인증 st.stop() 전 이동" in sidebar_raw[0]:
    sidebar_block = sidebar_raw[1:]  # 임시 주석 줄 제거
    print("임시 주석 첫 줄 제거")
else:
    sidebar_block = sidebar_raw
    print("첫 줄 그대로 사용")

print(f"최종 사이드바 블록 첫 줄: {repr(sidebar_block[0][:80])}")
print(f"최종 사이드바 블록 마지막 줄: {repr(sidebar_block[-1][:80])}")

# ── 새 들여쓰기: 사이드바 블록을 if not _is_auth_now: 안으로 들여쓰기 ─────
# 현재 with st.sidebar 블록의 들여쓰기: 4칸 (main() 최상위)
# if not _is_auth_now: 안으로 넣으면 8칸이어야 함
# → 각 줄 앞에 4칸 추가

def indent4(line):
    if line.strip() == "":
        return line  # 빈줄은 그대로
    return "    " + line

sidebar_indented = [indent4(ln) for ln in sidebar_block]

print(f"\n들여쓰기 후 첫 줄: {repr(sidebar_indented[0][:80])}")
print(f"들여쓰기 후 마지막 줄: {repr(sidebar_indented[-1][:80])}")

# ── 조립 ───────────────────────────────────────────────────────────────────
# before: 0 ~ IF_BLOCK_END_IDX (inclusive)
# middle: sidebar_indented
# after:  SIDEBAR_END_IDX ~ end (사이드바 블록 원래 자리 제거)
before = lines[:SIDEBAR_END_IDX]  # 일단 전체 앞부분 (SIDEBAR_START~END는 아직 포함)

# 실제 조립:
before_if  = lines[:IF_BLOCK_END_IDX + 1]  # if not _is_auth_now: 블록 포함
after_rest = lines[SIDEBAR_END_IDX:]        # 사이드바 블록 이후

new_lines = before_if + sidebar_indented + after_rest

print(f"\n최종 라인 수: {len(new_lines)}")
print(f"변화: {total} → {len(new_lines)} ({len(new_lines)-total:+d})")

# 삽입 지점 확인
insert_check_start = IF_BLOCK_END_IDX
print(f"\n[삽입 결과 확인] line {insert_check_start+1} ~ {insert_check_start+6}")
for i in range(insert_check_start, insert_check_start + 6):
    print(f"  [{i+1}] {repr(new_lines[i][:70])}")

# ── 저장 ──────────────────────────────────────────────────────────────────
with open(SRC, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("\n완료: app.py 저장됨")
