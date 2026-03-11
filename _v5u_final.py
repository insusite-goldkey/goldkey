# -*- coding: utf-8 -*-
"""
[V5-ULTIMATE FINAL] 강화 스크립트
1. _risk_badge_html: font 1.55rem, weight 900, border-radius 12px, shadow 강화
2. _render_gk_risk 헤더를 flex top-right 배지 고정 레이아웃으로 교체
3. SECTOR_CODES에서 2700(gk_risk)이 0300 이전에 오도록 보장
4. _fss_get_key()에서 전체 FSS 키 사용 확인 (secrets 기반 — 이미 업데이트됨)
5. 전역 CSS에 .risk-sector-header 클래스 추가
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
n0 = len(src.split('\n'))
print(f"원본: {n0}줄")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. _risk_badge_html 완전 교체 (font 1.55rem, weight 900, radius 12px)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_BADGE = (
    'def _risk_badge_html(grade: str, large: bool = True) -> str:\n'
    '    """위험등급 배지 HTML — large=True 시 150% 크기"""\n'
    '    _cfg = {\n'
    '        "RED":     {"bg": "#dc2626", "color": "#fff",    "border": "#b91c1c",'
    ' "label": "🚨 심각 (HIGH RISK)", "shadow": "0 6px 28px rgba(220,38,38,0.6)"},\n'
    '        "YELLOW":  {"bg": "#f59e0b", "color": "#fff",    "border": "#d97706",'
    ' "label": "⚠️ 주의 (CAUTION)",   "shadow": "0 6px 28px rgba(245,158,11,0.6)"},\n'
    '        "GREEN":   {"bg": "#16a34a", "color": "#fff",    "border": "#15803d",'
    ' "label": "✅ 안전 (SAFE)",       "shadow": "0 6px 28px rgba(22,163,74,0.5)"},\n'
    '        "UNKNOWN": {"bg": "#6b7280", "color": "#fff",    "border": "#4b5563",'
    ' "label": "❓ 미입력",            "shadow": "none"},\n'
    '    }\n'
    '    c = _cfg.get(grade, _cfg["UNKNOWN"])\n'
    '    fs = "1.35rem" if large else "0.82rem"\n'
    '    pad = "10px 22px" if large else "4px 12px"\n'
    '    return (\n'
    '        f"<div style=\'background:{c[\'bg\']};color:{c[\'color\']};"\n'
    '        f"border:2px solid {c[\'border\']};border-radius:8px;"\n'
    '        f"padding:{pad};font-size:{fs};font-weight:bold;"\n'
    '        f"box-shadow:{c[\'shadow\']};display:inline-block;"\n'
    '        f"letter-spacing:0.03em;word-break:keep-all;\'>"\n'
    '        f"{c[\'label\']}</div>"\n'
    '    )'
)

NEW_BADGE = (
    'def _risk_badge_html(grade: str, large: bool = True) -> str:\n'
    '    """위험등급 배지 HTML — V5-ULTIMATE: 1.55rem / weight:900 / radius:12px"""\n'
    '    _cfg = {\n'
    '        "RED":     {"bg": "#dc2626", "color": "#fff", "border": "#b91c1c",\n'
    '                    "label": "🚨 심각 (HIGH RISK)",\n'
    '                    "shadow": "0 6px 32px rgba(220,38,38,0.75), 0 0 0 3px #fff, 0 0 0 5px #dc2626"},\n'
    '        "YELLOW":  {"bg": "#f59e0b", "color": "#fff", "border": "#d97706",\n'
    '                    "label": "⚠️ 주의 (CAUTION)",\n'
    '                    "shadow": "0 6px 32px rgba(245,158,11,0.75), 0 0 0 3px #fff, 0 0 0 5px #f59e0b"},\n'
    '        "GREEN":   {"bg": "#16a34a", "color": "#fff", "border": "#15803d",\n'
    '                    "label": "✅ 안전 (SAFE)",\n'
    '                    "shadow": "0 6px 32px rgba(22,163,74,0.65), 0 0 0 3px #fff, 0 0 0 5px #16a34a"},\n'
    '        "UNKNOWN": {"bg": "#6b7280", "color": "#fff", "border": "#4b5563",\n'
    '                    "label": "❓ 미입력", "shadow": "none"},\n'
    '    }\n'
    '    c = _cfg.get(grade, _cfg["UNKNOWN"])\n'
    '    fs  = "1.55rem" if large else "0.88rem"\n'
    '    fw  = "900"     if large else "800"\n'
    '    pad = "12px 28px" if large else "5px 14px"\n'
    '    return (\n'
    '        f"<div style=\'background:{c[\'bg\']};color:{c[\'color\']};"\n'
    '        f"border:2px solid {c[\'border\']};border-radius:12px;"\n'
    '        f"padding:{pad};font-size:{fs};font-weight:{fw};"\n'
    '        f"box-shadow:{c[\'shadow\']};display:inline-block;"\n'
    '        f"letter-spacing:0.05em;word-break:keep-all;"\n'
    '        f"text-shadow:0 1px 3px rgba(0,0,0,0.25);\'>"  \n'
    '        f"{c[\'label\']}</div>"\n'
    '    )'
)

cnt = src.count(OLD_BADGE)
if cnt == 1:
    src = src.replace(OLD_BADGE, NEW_BADGE, 1)
    print("✓ _risk_badge_html V5-ULTIMATE 교체")
else:
    # 부분 교체: font-size/pad/border-radius 라인만 교체
    src = src.replace(
        '    fs = "1.35rem" if large else "0.82rem"\n'
        '    pad = "10px 22px" if large else "4px 12px"',
        '    fs  = "1.55rem" if large else "0.88rem"\n'
        '    fw  = "900"     if large else "800"\n'
        '    pad = "12px 28px" if large else "5px 14px"',
        1,
    )
    src = src.replace(
        '        f"border:2px solid {c[\'border\']};border-radius:8px;"',
        '        f"border:2px solid {c[\'border\']};border-radius:12px;"',
        1,
    )
    src = src.replace(
        '        f"padding:{pad};font-size:{fs};font-weight:bold;"',
        '        f"padding:{pad};font-size:{fs};font-weight:{fw};"',
        1,
    )
    src = src.replace(
        '        f"letter-spacing:0.03em;word-break:keep-all;\'>"',
        '        f"letter-spacing:0.05em;word-break:keep-all;\'"'
        '\n        f"text-shadow:0 1px 3px rgba(0,0,0,0.25);\'>"\n'
        '        # V5U',
        1,
    )
    print(f"⚠ 부분 교체 방식 적용 (OLD count={cnt})")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. _render_gk_risk 헤더를 top-right 배지 고정 레이아웃으로 교체
#    기존: 타이틀 div 아래 별도로 배지 노출
#    신규: 타이틀+배지를 flex justify-content:space-between 한 줄로
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_HEADER = (
    "    st.markdown(\n"
    "        \"<div style='background:linear-gradient(135deg,#7f1d1d 0%,#991b1b 60%,#dc2626 100%);\"\n"
    "        \"border-radius:14px;padding:20px 28px;margin-bottom:10px;border:1px solid #ef4444;'>\"\n"
    "        \"<div style='font-size:1.35rem;font-weight:900;color:#fef2f2;letter-spacing:0.04em;'>\"\n"
    "        \"🚨 전략적 위험 분석 사령부 — STRATEGIC RISK CENTER</div>\"\n"
    "        \"<div style='font-size:0.85rem;color:#fca5a5;margin-top:6px;line-height:1.6;'>\"\n"
    "        \"KCD 질병코드 · 직업 위험등급 · 건강보험료 역산 통합 위험도 산출 &nbsp;·&nbsp; \"\n"
    "        \"<span style='background:#fef2f2;color:#7f1d1d;border-radius:6px;\"\n"
    "        \"padding:1px 8px;font-weight:800;font-size:0.78rem;'>⚡ 사령관 최우선 확인</span>\"\n"
    "        \"</div>\"\n"
    "        \"</div>\", unsafe_allow_html=True\n"
    "    )"
)

NEW_HEADER = (
    "    # ── V5U: 헤더 + 종합 위험배지 top-right 고정 (flex layout) ────────────\n"
    "    _hdr_kcd  = st.session_state.get('scan_client_kcd_code', '') or st.session_state.get('risk_kcd_code', '')\n"
    "    _hdr_job  = st.session_state.get('gs_job_grade', 0)\n"
    "    _hdr_sick = st.session_state.get('home_si_sick', '해당 없음')\n"
    "    _hdr_kgrade  = _risk_assess_kcd(_hdr_kcd)\n"
    "    _hdr_jgrade  = 'RED' if _hdr_job >= 4 else ('YELLOW' if _hdr_job >= 2 else 'GREEN')\n"
    "    _hdr_sgrade  = 'RED' if _hdr_sick and _hdr_sick not in ('해당 없음','없음','') else 'GREEN'\n"
    "    _hdr_overall = max([_hdr_kgrade, _hdr_jgrade, _hdr_sgrade],\n"
    "                       key=lambda g: {'RED':3,'YELLOW':2,'GREEN':1,'UNKNOWN':0}.get(g,0))\n"
    "    _hdr_badge = _risk_badge_html(_hdr_overall, large=True)\n"
    "    st.markdown(\n"
    "        f\"<div style='background:linear-gradient(135deg,#7f1d1d 0%,#991b1b 60%,#dc2626 100%);\"\n"
    "        f\"border-radius:14px;padding:20px 28px;margin-bottom:10px;border:1px solid #ef4444;\"\n"
    "        f\"display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;'>\"\n"
    "        f\"<div style='flex:1;min-width:200px;'>\"\n"
    "        f\"<div style='font-size:1.45rem;font-weight:900;color:#fef2f2;letter-spacing:0.04em;'>\"\n"
    "        f\"🚨 전략적 위험 분석 사령부 — STRATEGIC RISK CENTER</div>\"\n"
    "        f\"<div style='font-size:0.85rem;color:#fca5a5;margin-top:4px;line-height:1.6;'>\"\n"
    "        f\"KCD 질병코드 · 직업 위험등급 · 건강보험료 역산 통합 위험도 산출 &nbsp;·&nbsp;\"\n"
    "        f\"<span style='background:#fef2f2;color:#7f1d1d;border-radius:6px;\"\n"
    "        f\"padding:1px 8px;font-weight:800;font-size:0.78rem;'>⚡ 사령관 최우선 확인</span>\"\n"
    "        f\"</div></div>\"\n"
    "        f\"<div style='flex-shrink:0;text-align:center;'>\"\n"
    "        f\"<div style='font-size:0.68rem;color:#fca5a5;font-weight:700;margin-bottom:6px;\">종합 위험등급</div>\"\n"
    "        f\"{_hdr_badge}\"\n"
    "        f\"</div>\"\n"
    "        f\"</div>\",\n"
    "        unsafe_allow_html=True,\n"
    "    )"
)

cnt2 = src.count(OLD_HEADER)
if cnt2 == 1:
    src = src.replace(OLD_HEADER, NEW_HEADER, 1)
    print("✓ 헤더 top-right 배지 고정 레이아웃 교체")
else:
    print(f"⚠ 헤더 교체 스킵 (count={cnt2})")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. SECTOR_CODES — 2700(gk_risk)을 0300(war_room) 앞에 배치
#    현재: 0100, 0200, 0300, ..., 2700
#    목표: 0100, 0200, 2700(최우선), 0300, ...
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2700 블록 찾아서 0200 바로 뒤로 이동
lines = src.split('\n')

# 2700 블록 위치 찾기
line_2700_start = line_2700_end = -1
for i, l in enumerate(lines):
    if '"2700":' in l and 'gk_risk' in l:
        # 블록 시작 (앞 주석 포함)
        j = i - 1
        while j >= 0 and (lines[j].strip().startswith('#') or lines[j].strip() == ''):
            j -= 1
        line_2700_start = j + 1
        # 블록 끝 (다음 코드 라인 직전)
        k = i + 1
        while k < len(lines) and (lines[k].strip() == '' or lines[k].strip().startswith('"') or lines[k].strip().startswith('#')):
            if lines[k].strip().startswith('"') and '"tab_key"' not in lines[k] and '2700' not in lines[k]:
                break
            k += 1
        line_2700_end = k
        break

print(f"2700 블록: {line_2700_start}~{line_2700_end}")

# 0200(claim_scanner) 블록 끝 위치 찾기
line_0200_end = -1
for i, l in enumerate(lines):
    if '"0200":' in l and 'claim_scanner' in l:
        # 다음 라인이 0300이나 주석인 위치까지
        k = i + 1
        while k < len(lines) and lines[k].strip() == '':
            k += 1
        line_0200_end = k  # 여기에 삽입
        break

print(f"0200 블록 끝: {line_0200_end}")

if line_2700_start > 0 and line_0200_end > 0 and line_2700_start > line_0200_end:
    # 2700 블록 추출
    block_2700 = lines[line_2700_start:line_2700_end]
    print(f"2700 블록 내용 ({len(block_2700)}줄): {repr(block_2700[0][:60])}")

    # 2700 블록 제거
    new_lines = lines[:line_2700_start] + lines[line_2700_end:]

    # 0200 위치 재계산 (2700 제거 후 앞에 있으므로 그대로)
    new_0200_end = line_0200_end  # 2700이 뒤에 있었으므로 그대로

    # 0200 뒤에 2700 삽입
    final_lines = new_lines[:new_0200_end] + block_2700 + new_lines[new_0200_end:]
    src = '\n'.join(final_lines)
    print("✓ SECTOR_CODES 2700(gk_risk) 최상단 배치 (0200 다음)")
else:
    if line_2700_start <= line_0200_end:
        print("이미 2700이 앞에 위치 — 순서 변경 불필요")
    else:
        print(f"⚠ 위치 파악 실패: 2700={line_2700_start}, 0200_end={line_0200_end}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 전역 CSS에 .risk-sector-header 추가 (S12 블록 끝에)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CSS_LOSS_END = '"    -webkit-overflow-scrolling: touch !important; scrollbar-color: #dc2626 transparent !important;"'
CSS_SYN_MARKER = '"/* [GP-V3] SYNERGY PANEL */"'

if src.count(CSS_SYN_MARKER) == 1:
    CSS_INSERT = (
        '"/* [V5U] RISK SECTOR HEADER TOP-RIGHT BADGE */"\n'
        '            ".risk-sector-hdr {"\n'
        '            "    display: flex !important;"\n'
        '            "    align-items: center !important;"\n'
        '            "    justify-content: space-between !important;"\n'
        '            "    flex-wrap: wrap !important;"\n'
        '            "    gap: 12px !important;"\n'
        '            "    background: linear-gradient(135deg,#7f1d1d 0%,#dc2626 100%) !important;"\n'
        '            "    border-radius: 14px !important;"\n'
        '            "    padding: 18px 24px !important;"\n'
        '            "    margin-bottom: 12px !important;"\n'
        '            "    border: 1px solid #ef4444 !important;"\n'
        '            "}"\n'
        '            ".risk-sector-hdr-badge { flex-shrink: 0 !important; text-align: center !important; }"\n'
        '            "@media (max-width: 600px) {"\n'
        '            "    .risk-sector-hdr { flex-direction: column !important; }"\n'
        '            "    .risk-sector-hdr-badge { width: 100% !important; }"\n'
        '            "}"\n'
        '            '
    )
    src = src.replace(CSS_SYN_MARKER, CSS_INSERT + CSS_SYN_MARKER, 1)
    print("✓ .risk-sector-header CSS 추가")
else:
    print(f"⚠ CSS 삽입점 미발견 (count={src.count(CSS_SYN_MARKER)})")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
n1 = len(src.split('\n'))
print(f"OK total lines: {n1} (+{n1-n0})")
