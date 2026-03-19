"""
현재 구조 (잘못됨):
  line 28698~30711: if not _is_auth_now:
    메인화면 로그인폼 (28699~28902)
    with st.sidebar: 로그인폼 전체 (28903~30711)  ← 인증자는 사이드바 없음!
  line 30713~: 인증자 메인 앱

목표 구조 (올바름):
  line 28698~: if not _is_auth_now:
    메인화면 로그인폼만
    st.stop()  ← 미인증 차단
  line ~: with st.sidebar:  ← 인증/미인증 공통 (단, 이미 st.stop()으로 미인증 차단됨)
    ...사이드바 로그인폼 포함...
  line ~: 인증자 메인 앱

작업:
  1) if not _is_auth_now 블록에서 with st.sidebar 블록(28903~30711) 제거
  2) if not _is_auth_now 블록 끝에 st.stop() 추가 (8칸 들여쓰기)
  3) with st.sidebar 블록을 if not _is_auth_now 블록 바로 다음에 삽입 (4칸 들여쓰기, 원래 수준)
"""

SRC = "D:/CascadeProjects/app.py"

with open(SRC, encoding="utf-8") as f:
    lines = f.readlines()

total = len(lines)
print(f"총 라인: {total}")

# ── 경계 확인 ──────────────────────────────────────────────────────────────
# if not _is_auth_now: 블록: line 28698~30711 (0-indexed 28697~30710)
# 메인화면 로그인폼: line 28699~28902 (0-indexed 28698~28901)
# with st.sidebar 블록 (indent=4): line 28903~30711 (0-indexed 28902~30710)
# 블록 뒤 빈줄: line 30712 (0-indexed 30711)

AUTH_IF_LINE     = 28697   # 0-indexed: "    if not _is_auth_now:\n"
MAIN_FORM_END    = 28901   # 0-indexed: line 28902 — st.error(f"변경 실패: {_e_nm}")
SIDEBAR_START    = 28902   # 0-indexed: line 28903 — "        # ── 사이드바 ──" (indent=8)
SIDEBAR_END_EXCL = 30712   # 0-indexed exclusive: line 30712=st.stop(), line 30713=빈줄 포함
AFTER_BLOCK      = 30712   # 0-indexed: 빈줄(line 30713) 포함해서 제거

# 검증
print(f"\n[AUTH_IF_LINE]    [{AUTH_IF_LINE+1}] {repr(lines[AUTH_IF_LINE][:70])}")
print(f"[MAIN_FORM_END]   [{MAIN_FORM_END+1}] {repr(lines[MAIN_FORM_END][:70])}")
print(f"[SIDEBAR_START]   [{SIDEBAR_START+1}] {repr(lines[SIDEBAR_START][:70])}")
print(f"[SIDEBAR_END_EXCL-1] [{SIDEBAR_END_EXCL}] {repr(lines[SIDEBAR_END_EXCL-1][:70])}")
print(f"[AFTER_BLOCK]     [{AFTER_BLOCK+1}] {repr(lines[AFTER_BLOCK][:70])}")

# ── 사이드바 블록 추출 (indent=8 → 4로 내려야 함) ─────────────────────────
sidebar_block_indented = lines[SIDEBAR_START:SIDEBAR_END_EXCL]
print(f"\n사이드바 블록 라인 수: {len(sidebar_block_indented)}")
print(f"첫 줄: {repr(sidebar_block_indented[0][:70])}")
print(f"마지막 줄: {repr(sidebar_block_indented[-1][:70])}")

# indent=8 → indent=4 (4칸 제거)
def dedent4(line):
    if line.strip() == "":
        return line
    if line.startswith("        "):   # 8칸 이상
        return line[4:]               # 앞 4칸 제거
    elif line.startswith("    "):     # 4칸 (현재 블록 최상위, "    # ── 사이드바" 등)
        return line                   # 그대로 — 이미 4칸이면 올바른 수준
    return line

sidebar_dedented = [dedent4(ln) for ln in sidebar_block_indented]
print(f"\n들여쓰기 조정 후 첫 줄: {repr(sidebar_dedented[0][:70])}")
print(f"들여쓰기 조정 후 2번째 줄: {repr(sidebar_dedented[1][:70])}")

# ── 조립 ───────────────────────────────────────────────────────────────────
# before: 0 ~ MAIN_FORM_END (inclusive) — if not _is_auth_now + 메인 로그인폼
# insert: st.stop() (8칸 들여쓰기, if 블록 안)
# then:   빈줄
# then:   sidebar_dedented (4칸 들여쓰기, if 블록 밖)
# after:  SIDEBAR_END_EXCL ~ end (원래 sidebar 블록 제거, 빈줄 포함)

stop_line  = "        st.stop()\n"   # 8칸: if not _is_auth_now 블록 안
blank_line = "\n"

before  = lines[:MAIN_FORM_END + 1]
after   = lines[SIDEBAR_END_EXCL:]   # 빈줄(30711) 포함부터

new_lines = before + [stop_line, blank_line] + sidebar_dedented + after

print(f"\n최종 라인 수: {len(new_lines)}")
print(f"변화: {total} → {len(new_lines)} ({len(new_lines)-total:+d})")

# 삽입 결과 확인
check_start = MAIN_FORM_END
print(f"\n[삽입 결과 확인] line {check_start+1} ~ {check_start+10}")
for i in range(check_start, min(check_start+10, len(new_lines))):
    indent = len(new_lines[i]) - len(new_lines[i].lstrip())
    print(f"  [{i+1}] i={indent} {repr(new_lines[i][:65])}")

# ── 저장 ──────────────────────────────────────────────────────────────────
with open(SRC, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("\n완료: app.py 저장됨")
