# -*- coding: utf-8 -*-
"""탭 라우터에 gk_sec07 진입점 연결 + home 네비게이션에 GK-SEC-07 버튼 패치"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

# ── 1. 탭 라우터에 gk_sec07 진입점 추가 ─────────────────────────────────────
# war_room 라우터 블록 직후에 삽입
ANCHOR_ROUTER = (
    "    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
    "    # [GP100/110/120] life_defense \ub77c\uc6b0\ud130 \u2014 \ub098\uc758 \uc778\uc0dd \ubc29\uc5b4 \uc0ac\ub839\ubd80\n"
    "    # \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"
    "    if cur == \"life_defense\":"
)

if ANCHOR_ROUTER not in content:
    print("ERROR: life_defense anchor not found, trying fallback...")
    # 폴백: war_room stop 이후 첫 번째 주석 블록 찾기
    ANCHOR_ROUTER2 = '    if cur == "life_defense":'
    if ANCHOR_ROUTER2 not in content:
        print("ERROR: fallback anchor also not found")
        exit(1)
    ANCHOR_ROUTER = ANCHOR_ROUTER2

INSERT_ROUTER = '''    # ══════════════════════════════════════════════════════════════════════
    # [GK-SEC-07] 자동차보험 전술 상담 센터 라우터
    # ══════════════════════════════════════════════════════════════════════
    if cur == "gk_sec07":
        if not _auth_gate("gk_sec07"): st.stop()
        _render_gk_sec07()
        st.stop()

    '''

idx = content.find(ANCHOR_ROUTER)
content = content[:idx] + INSERT_ROUTER + content[idx:]
print("Router gk_sec07 inserted OK")

# ── 2. home 화면 네비게이션에 GK-SEC-07 버튼 삽입 ───────────────────────────
# _sec_anchor_map에 gk_sec07 앵커 추가
ANCHOR_HOME_MAP = '"_home_scroll_to_sec01": "gk-sec-01-anchor"'
if ANCHOR_HOME_MAP in content:
    # sec_anchor_map이 있는 위치 근처에서 _go_tab("gk_sec07") 버튼 삽입 위치 탐색
    print("Home anchor map found")
else:
    print("WARNING: home anchor map not found — skipping home button patch")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE: tab router patched")
