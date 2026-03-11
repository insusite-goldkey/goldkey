# -*- coding: utf-8 -*-
"""V7-RARE: CSS keyframes + badge_override 패치 (앵커 충돌 회피)"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
n0  = len(src.split('\n'))
print(f"원본: {n0}줄")

# ─── 1. CSS @keyframes flash-red 추가 ────────────────────────────────────────
OLD_CSS = (
    "@media (max-width: 900px) {\n"
    "    .risk-wrap { padding: 14px 12px; }\n"
    "    .risk-panel { padding: 12px 14px; }\n"
    "    .risk-badge-wrap { min-height: 100px; padding: 12px 10px; }\n"
    "}\n"
    "</style>"
)
NEW_CSS = (
    "@media (max-width: 900px) {\n"
    "    .risk-wrap { padding: 14px 12px; }\n"
    "    .risk-panel { padding: 12px 14px; }\n"
    "    .risk-badge-wrap { min-height: 100px; padding: 12px 10px; }\n"
    "}\n"
    "@keyframes flash-red-pulse {\n"
    "    0%   { background:#dc2626; box-shadow:0 0 0 0 rgba(220,38,38,0.8); }\n"
    "    40%  { background:#ff0000; box-shadow:0 0 0 14px rgba(220,38,38,0); }\n"
    "    70%  { background:#b91c1c; box-shadow:0 0 0 0 rgba(220,38,38,0); }\n"
    "    100% { background:#dc2626; box-shadow:0 0 0 0 rgba(220,38,38,0); }\n"
    "}\n"
    ".risk-badge-flash {\n"
    "    animation: flash-red-pulse 1.1s infinite;\n"
    "    border-radius: 12px;\n"
    "    display: inline-block;\n"
    "}\n"
    ".rare-drug-card {\n"
    "    border: 2px solid #d97706 !important;\n"
    "    background: linear-gradient(135deg, #fffbeb, #fff7ed) !important;\n"
    "}\n"
    "</style>"
)
cnt = src.count(OLD_CSS)
print(f"CSS anchor count: {cnt}")
assert cnt == 1
src = src.replace(OLD_CSS, NEW_CSS, 1)
print("✓ @keyframes flash-red-pulse CSS 추가")

# ─── 2. badge_override FLASH_RED 처리 ────────────────────────────────────────
OLD_BADGE = (
    "    _hdr_overall = max([_hdr_kgrade, _hdr_jgrade, _hdr_sgrade],\n"
    "                       key=lambda g: {'RED':3,'YELLOW':2,'GREEN':1,'UNKNOWN':0}.get(g,0))\n"
    "    _hdr_badge = _risk_badge_html(_hdr_overall, large=True)"
)
NEW_BADGE = (
    "    _hdr_overall = max([_hdr_kgrade, _hdr_jgrade, _hdr_sgrade],\n"
    "                       key=lambda g: {'RED':3,'YELLOW':2,'GREEN':1,'UNKNOWN':0}.get(g,0))\n"
    "    # [V7] 희귀의약품 감지 시 FLASH_RED 오버라이드\n"
    "    _badge_override = st.session_state.get('risk_badge_override', '')\n"
    "    _badge_reason   = st.session_state.get('risk_badge_reason', '')\n"
    "    if _badge_override == 'FLASH_RED':\n"
    "        _hdr_overall = 'RED'\n"
    "        _hdr_badge = (\n"
    "            \"<div class='risk-badge-flash'>\"\n"
    "            + _risk_badge_html('RED', large=True)\n"
    "            + \"</div>\"\n"
    "            + (f\"<div style='font-size:0.66rem;color:#fca5a5;font-weight:800;\"\n"
    "               f\"margin-top:5px;text-align:center;word-break:keep-all;'>\"\n"
    "               f\"\U0001f6a8 희귀약 감지: {_badge_reason}</div>\" if _badge_reason else \"\")\n"
    "        )\n"
    "    else:\n"
    "        _hdr_badge = _risk_badge_html(_hdr_overall, large=True)"
)
cnt2 = src.count(OLD_BADGE)
print(f"BADGE anchor count: {cnt2}")
assert cnt2 == 1
src = src.replace(OLD_BADGE, NEW_BADGE, 1)
print("✓ badge_override FLASH_RED 처리")

open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
n1 = len(src.split('\n'))
print(f"OK total lines: {n1} (+{n1-n0})")
