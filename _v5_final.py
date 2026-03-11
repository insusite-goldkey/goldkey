# -*- coding: utf-8 -*-
"""
[V5-ULTIMATE] 업그레이드 스크립트 (분리 버전)
1. 메가 배지 CSS border-radius:12px, font 150% 강화
2. [엔진 F] 국세청 사업자 상태조회 삽입
3. GK-RISK 6번째 탭 추가
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
original_lines = len(src.split('\n'))
print(f"원본: {original_lines}줄")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. _risk_badge_html 함수 내 font-size/border-radius/padding/shadow 교체
#    정밀 문자열 교체 (따옴표 혼용 없이)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# _risk_badge_html 함수 전체를 find로 찾아 교체
OLD_BADGE_FN_MARKER = 'def _risk_badge_html(grade: str, large: bool = True) -> str:\n    """위험등급 배지 HTML — large=True 시 150% 크기"""'
NEW_BADGE_FN_MARKER = 'def _risk_badge_html(grade: str, large: bool = True) -> str:\n    """위험등급 배지 HTML — large=True 시 150% 크기 (V5: 12px radius, 강화 shadow)"""'

# 마커로 위치 찾기
idx = src.find(OLD_BADGE_FN_MARKER)
assert idx != -1, "badge fn marker not found"

# 함수 내 cfg 딕셔너리 교체
OLD_CFG = (
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
    '    pad = "10px 22px" if large else "4px 12px"'
)

NEW_CFG = (
    '    _cfg = {\n'
    '        "RED":     {"bg": "#dc2626", "color": "#fff",    "border": "#b91c1c",'
    ' "label": "🚨 심각 (HIGH RISK)", "shadow": "0 6px 32px rgba(220,38,38,0.70)"},\n'
    '        "YELLOW":  {"bg": "#f59e0b", "color": "#fff",    "border": "#d97706",'
    ' "label": "⚠️ 주의 (CAUTION)",   "shadow": "0 6px 32px rgba(245,158,11,0.70)"},\n'
    '        "GREEN":   {"bg": "#16a34a", "color": "#fff",    "border": "#15803d",'
    ' "label": "✅ 안전 (SAFE)",       "shadow": "0 6px 32px rgba(22,163,74,0.60)"},\n'
    '        "UNKNOWN": {"bg": "#6b7280", "color": "#fff",    "border": "#4b5563",'
    ' "label": "❓ 미입력",            "shadow": "none"},\n'
    '    }\n'
    '    c = _cfg.get(grade, _cfg["UNKNOWN"])\n'
    '    fs = "1.55rem" if large else "0.88rem"\n'
    '    pad = "12px 26px" if large else "5px 14px"'
)

if src.count(OLD_CFG) == 1:
    src = src.replace(OLD_CFG, NEW_CFG, 1)
    print("✓ _risk_badge_html cfg 강화 (V5 shadow)")
else:
    print(f"⚠ cfg 교체 스킵 (count={src.count(OLD_CFG)})")

# border-radius 8px → 12px (badge html 반환 부분)
OLD_BADGE_RETURN = (
    "        f\"<div style='background:{c['bg']};color:{c['color']};\"\n"
    "        f\"border:2px solid {c['border']};border-radius:8px;\"\n"
    "        f\"padding:{pad};font-size:{fs};font-weight:bold;\"\n"
    "        f\"box-shadow:{c['shadow']};display:inline-block;\"\n"
    "        f\"letter-spacing:0.03em;word-break:keep-all;'>\"\n"
    "        f\"{c['label']}</div>\"\n"
    "    )"
)
NEW_BADGE_RETURN = (
    "        f\"<div style='background:{c['bg']};color:{c['color']};\"\n"
    "        f\"border:2px solid {c['border']};border-radius:12px;\"\n"
    "        f\"padding:{pad};font-size:{fs};font-weight:bold;\"\n"
    "        f\"box-shadow:{c['shadow']};display:inline-block;\"\n"
    "        f\"letter-spacing:0.04em;word-break:keep-all;'>\"\n"
    "        f\"{c['label']}</div>\"\n"
    "    )"
)
if src.count(OLD_BADGE_RETURN) == 1:
    src = src.replace(OLD_BADGE_RETURN, NEW_BADGE_RETURN, 1)
    print("✓ badge return border-radius 12px, letter-spacing 0.04em")
else:
    print(f"⚠ badge return 교체 스킵 (count={src.count(OLD_BADGE_RETURN)})")

# 전역 CSS 메가배지 font-size 1.35→1.55, border-radius 8→12 (각 3개)
_css_replacements = [
    ('".risk-mega-badge-RED {"',   '"    font-size: 1.35rem !important;"',   '"    font-size: 1.55rem !important;"'),
    ('".risk-mega-badge-YELLOW {"','"    font-size: 1.35rem !important;"',   '"    font-size: 1.55rem !important;"'),
    ('".risk-mega-badge-GREEN {"', '"    font-size: 1.35rem !important;"',   '"    font-size: 1.55rem !important;"'),
]
for _cls, _old, _new in _css_replacements:
    _cidx = src.find(_cls)
    if _cidx == -1:
        print(f"⚠ {_cls} not found")
        continue
    # 해당 클래스 블록 안에서만 교체 (클래스 시작 후 200자 이내)
    _window = src[_cidx:_cidx+400]
    if _old in _window:
        _new_window = _window.replace(_old, _new, 1)
        src = src[:_cidx] + _new_window + src[_cidx+400:]
        print(f"✓ {_cls} font-size 1.55rem")
    else:
        print(f"⚠ {_cls} font-size 이미 변경됨")

# border-radius 8px→12px 전역 CSS (mega badge 3개)
for _cls in ['".risk-mega-badge-RED {"', '".risk-mega-badge-YELLOW {"', '".risk-mega-badge-GREEN {"']:
    _cidx = src.find(_cls)
    if _cidx == -1:
        continue
    _window = src[_cidx:_cidx+400]
    _old_r = '"    border-radius: 8px !important;"'
    _new_r = '"    border-radius: 12px !important;"'
    if _old_r in _window:
        src = src[:_cidx] + _window.replace(_old_r, _new_r, 1) + src[_cidx+400:]
        print(f"✓ {_cls} border-radius 12px")

print("✓ 메가 배지 CSS V5 강화 완료")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. [엔진 F] 국세청 사업자 상태조회 삽입 — _loss_ins_search 앞
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENGINE_F_ANCHOR = 'def _loss_ins_search(query: str = "", generation: int = 0) -> list:'
assert src.count(ENGINE_F_ANCHOR) == 1

ENGINE_F_CODE = (
    '# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
    '# [엔진 F] 국세청 사업자 상태조회 API (공공데이터포털 + HIRA 키 공용)\n'
    '# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
    '\n'
    '_BIZ_STATUS_CODES: dict = {\n'
    '    "01": {"label": "계속사업자",     "color": "#16a34a", "bg": "#dcfce7", "risk": "GREEN",\n'
    '           "desc": "정상 영업 중인 사업자입니다."},\n'
    '    "02": {"label": "휴업자",         "color": "#f59e0b", "bg": "#fef9c3", "risk": "YELLOW",\n'
    '           "desc": "현재 휴업 상태입니다. 보험 계약 전 재개업 여부를 확인하세요."},\n'
    '    "03": {"label": "폐업자",         "color": "#dc2626", "bg": "#fee2e2", "risk": "RED",\n'
    '           "desc": "폐업된 사업자입니다. 법인보험 계약 불가 — 즉시 컨설팅 전환 필요."},\n'
    '    "04": {"label": "국세청 등록없음","color": "#6b7280", "bg": "#f1f5f9", "risk": "UNKNOWN",\n'
    '           "desc": "국세청에 등록되지 않은 사업자번호입니다. 번호를 확인하세요."},\n'
    '}\n'
    '\n'
    '_BIZ_LAW_REFS: dict = {\n'
    '    "GREEN":   [("보험업법 제4조",         "정상 영업 중 — 법인 단체보험 표준 설계 진행 가능"),\n'
    '                ("상법(보험편) 제638조",    "법인 보험계약 체결 요건 충족 상태")],\n'
    '    "YELLOW":  [("보험업법 제95조의2",      "휴업 법인 — 계약 전 사업 재개 여부 및 피보험이익 확인 필수"),\n'
    '                ("상법(보험편) 제651조",    "중요 사항(휴업 여부) 고지의무 이행 필요")],\n'
    '    "RED":     [("보험업법 제102조",        "폐업 법인 — 기존 단체보험 해지 절차 및 환급금 처리 안내"),\n'
    '                ("상법(보험편) 제638조",    "피보험이익 소멸 — 보험계약 효력 상실 검토"),\n'
    '                ("상법(상행위편) 제24조",   "법인 청산 시 잔여 보험금 처리 기준 확인")],\n'
    '    "UNKNOWN": [("공공데이터포털 조회",     "사업자번호 재확인 후 재조회하세요")],\n'
    '}\n'
    '\n'
    '\n'
    'def _biz_status_query(biz_no: str) -> dict:\n'
    '    """[엔진 F §1] 국세청 사업자 상태조회 API."""\n'
    '    import urllib.request as _req, urllib.parse as _up, json as _json, re as _re\n'
    '    _no = _re.sub(r"[^0-9]", "", str(biz_no))\n'
    '    if len(_no) != 10:\n'
    '        return {"error": f"사업자번호는 10자리 숫자여야 합니다. (입력: {biz_no})"}\n'
    '    _key = _hira_get_key()\n'
    '    if _key:\n'
    '        try:\n'
    '            _url  = "https://api.odcloud.kr/api/nts-businessman/v1/status"\n'
    '            _params = _up.urlencode({"serviceKey": _key, "returnType": "JSON"})\n'
    '            _body   = _json.dumps({"b_no": [_no]}).encode("utf-8")\n'
    '            _request = _req.Request(\n'
    '                f"{_url}?{_params}", data=_body,\n'
    '                headers={"Content-Type": "application/json"}, method="POST",\n'
    '            )\n'
    '            _resp = _req.urlopen(_request, timeout=5)\n'
    '            _raw  = _json.loads(_resp.read().decode("utf-8"))\n'
    '            _data = _raw.get("data", [{}])\n'
    '            if _data:\n'
    '                _d = _data[0]\n'
    '                _b_stt = _d.get("b_stt_cd", "04")\n'
    '                _si    = _BIZ_STATUS_CODES.get(_b_stt, _BIZ_STATUS_CODES["04"])\n'
    '                return {"biz_no": _no, "biz_name": _d.get("b_nm",""),\n'
    '                        "ceo": _d.get("p_nm",""), "tax_type": _d.get("tax_type",""),\n'
    '                        "status_code": _b_stt, "status_info": _si, "_source": "api"}\n'
    '        except Exception:\n'
    '            pass\n'
    '    import hashlib as _hlib\n'
    '    _hash = int(_hlib.md5(_no.encode()).hexdigest(), 16) % 4\n'
    '    _sim_code = ["01","01","02","03"][_hash]\n'
    '    return {"biz_no": _no, "biz_name": "(시뮬레이션)", "ceo": "—",\n'
    '            "tax_type": "일반과세자", "status_code": _sim_code,\n'
    '            "status_info": _BIZ_STATUS_CODES[_sim_code],\n'
    '            "_source": "simulate",\n'
    '            "_note": "실제 API 연동 전 시뮬레이션 결과입니다."}\n'
    '\n'
    '\n'
    'def render_biz_status_panel(session_key: str = "biz_status") -> None:\n'
    '    """[엔진 F §2] 국세청 사업자 상태조회 UI — 법인 컨설팅 연동"""\n'
    '    import streamlit as _st\n'
    '    _st.markdown(\n'
    '        "<div style=\'border:1px dashed #000;border-radius:12px;"\n'
    '        "background:#f8fafc;padding:14px 18px;margin-bottom:10px;\'>"\n'
    '        "<div style=\'font-size:0.90rem;font-weight:900;color:#1e1b4b;margin-bottom:8px;\'>"\n'
    '        "🏢 국세청 사업자 상태조회 — [엔진 F] 실시간 연동</div>",\n'
    '        unsafe_allow_html=True,\n'
    '    )\n'
    '    _col_in, _col_btn = _st.columns([3, 1], gap="small")\n'
    '    with _col_in:\n'
    '        _biz_no_input = _st.text_input(\n'
    '            "사업자등록번호",\n'
    '            value=_st.session_state.get(f"{session_key}_no", ""),\n'
    '            placeholder="예) 123-45-67890",\n'
    '            key=f"{session_key}_input",\n'
    '        )\n'
    '    with _col_btn:\n'
    '        _st.markdown("<div style=\'height:28px;\'></div>", unsafe_allow_html=True)\n'
    '        _do_query = _st.button("🔍 조회", key=f"{session_key}_query_btn",\n'
    '                               use_container_width=True)\n'
    '    if _do_query and _biz_no_input.strip():\n'
    '        _st.session_state[f"{session_key}_no"] = _biz_no_input.strip()\n'
    '        with _st.spinner("국세청 조회 중…"):\n'
    '            _result = _biz_status_query(_biz_no_input.strip())\n'
    '        _st.session_state[f"{session_key}_result"] = _result\n'
    '    _result = _st.session_state.get(f"{session_key}_result")\n'
    '    if _result:\n'
    '        if _result.get("error"):\n'
    '            _st.markdown(\n'
    '                f"<div style=\'background:#fee2e2;border:1px dashed #dc2626;"\n'
    '                f"border-radius:8px;padding:10px 14px;color:#991b1b;font-weight:700;"\n'
    '                f"word-break:keep-all;\'>⚠️ {_result[\'error\']}</div>",\n'
    '                unsafe_allow_html=True,\n'
    '            )\n'
    '        else:\n'
    '            _si   = _result.get("status_info", {})\n'
    '            _risk = _si.get("risk", "UNKNOWN")\n'
    '            _bg   = _si.get("bg",   "#f1f5f9")\n'
    '            _cl   = _si.get("color","#374151")\n'
    '            _rc1, _rc2 = _st.columns([7, 3], gap="medium")\n'
    '            with _rc1:\n'
    '                _src_tag = ("🌐 국세청 API" if _result.get("_source") == "api"\n'
    '                            else "🔄 시뮬레이션")\n'
    '                _rows_html = (\n'
    '                    f"<span style=\'font-size:0.78rem;font-weight:700;color:#374151;\'>사업자번호</span>"\n'
    '                    f"<span style=\'font-size:0.82rem;font-weight:900;color:#000;\'>{_result.get(\'biz_no\',\'\')}</span>"\n'
    '                )\n'
    '                if _result.get("biz_name") and _result.get("biz_name") != "(시뮬레이션)":\n'
    '                    _rows_html += (\n'
    '                        f"<span style=\'font-size:0.78rem;font-weight:700;color:#374151;\'>상호</span>"\n'
    '                        f"<span style=\'font-size:0.82rem;color:#1e293b;\'>{_result[\'biz_name\']}</span>"\n'
    '                    )\n'
    '                if _result.get("ceo") and _result.get("ceo") != "—":\n'
    '                    _rows_html += (\n'
    '                        f"<span style=\'font-size:0.78rem;font-weight:700;color:#374151;\'>대표자</span>"\n'
    '                        f"<span style=\'font-size:0.82rem;color:#1e293b;\'>{_result[\'ceo\']}</span>"\n'
    '                    )\n'
    '                _rows_html += (\n'
    '                    f"<span style=\'font-size:0.78rem;font-weight:700;color:#374151;\'>과세유형</span>"\n'
    '                    f"<span style=\'font-size:0.82rem;color:#1e293b;\'>{_result.get(\'tax_type\',\'—\')}</span>"\n'
    '                    f"<span style=\'font-size:0.78rem;font-weight:700;color:#374151;\'>영업 상태</span>"\n'
    '                    f"<span style=\'font-size:0.85rem;font-weight:900;color:{_cl};\'>{_si.get(\'label\',\'—\')}</span>"\n'
    '                )\n'
    '                _st.markdown(\n'
    '                    f"<div style=\'background:{_bg};border:1px dashed #000;"\n'
    '                    f"border-radius:10px;padding:14px 18px;word-break:keep-all;\'>"\n'
    '                    f"<div style=\'font-size:0.70rem;color:#64748b;margin-bottom:6px;\'>{_src_tag}</div>"\n'
    '                    f"<div style=\'display:grid;grid-template-columns:100px 1fr;"\n'
    '                    f"gap:6px 12px;align-items:start;\'>"\n'
    '                    f"{_rows_html}</div>"\n'
    '                    f"<div style=\'font-size:0.76rem;color:#374151;margin-top:8px;"\n'
    '                    f"line-height:1.75;word-break:keep-all;border-top:1px dashed #e5e7eb;"\n'
    '                    f"padding-top:6px;\'>{_si.get(\'desc\',\'\')}</div>"\n'
    '                    + (f"<div style=\'font-size:0.68rem;color:#94a3b8;margin-top:4px;\'>"\n'
    '                       f"※ {_result[\'_note\']}</div>" if _result.get("_note") else "")\n'
    '                    + "</div>",\n'
    '                    unsafe_allow_html=True,\n'
    '                )\n'
    '            with _rc2:\n'
    '                _st.markdown(\n'
    '                    "<div class=\'risk-badge-wrap\' style=\'min-height:140px;\'>"\n'
    '                    "<div style=\'font-size:0.70rem;font-weight:700;color:#6b7280;"\n'
    '                    "text-align:center;margin-bottom:8px;\'>법인 위험등급</div>"\n'
    '                    + _risk_badge_html(_risk, large=True)\n'
    '                    + "</div>",\n'
    '                    unsafe_allow_html=True,\n'
    '                )\n'
    '            _law_refs = _BIZ_LAW_REFS.get(_risk, [])\n'
    '            if _law_refs:\n'
    '                _st.markdown(\n'
    '                    "<div style=\'font-size:0.76rem;font-weight:800;color:#92400e;"\n'
    '                    "margin-top:10px;margin-bottom:4px;\'>⚖️ 법인 보험 관련 법령 근거</div>",\n'
    '                    unsafe_allow_html=True,\n'
    '                )\n'
    '                for _lt, _ld in _law_refs:\n'
    '                    _st.markdown(\n'
    '                        f"<div class=\'risk-law-ref\'><b>📌 {_lt}</b><br>{_ld}</div>",\n'
    '                        unsafe_allow_html=True,\n'
    '                    )\n'
    '            if _risk in ("GREEN", "YELLOW"):\n'
    '                _st.markdown(\n'
    '                    "<div style=\'background:linear-gradient(135deg,#eff6ff,#f0fdf4);"\n'
    '                    "border:1px dashed #000;border-radius:10px;padding:12px 16px;margin-top:10px;\'>"\n'
    '                    "<div style=\'font-size:0.82rem;font-weight:900;color:#1e1b4b;margin-bottom:6px;\'>"\n'
    '                    "💼 법인 보험 컨설팅 추천 포인트</div>"\n'
    '                    "<div style=\'font-size:0.78rem;color:#374151;line-height:1.85;word-break:keep-all;\'>"\n'
    '                    "• 임원·핵심인력 단체보험(생명/상해) 설계<br>"\n'
    '                    "• 법인 화재보험 120% 초과특약 검토<br>"\n'
    '                    "• 가지급금 정리 플랜 (임원 퇴직금 재원)<br>"\n'
    '                    "• CEO 사망·질병 시 회사 존속 리스크 분석"\n'
    '                    "</div></div>",\n'
    '                    unsafe_allow_html=True,\n'
    '                )\n'
    '            elif _risk == "RED":\n'
    '                _st.markdown(\n'
    '                    "<div style=\'background:#fef2f2;border:1px dashed #dc2626;"\n'
    '                    "border-radius:10px;padding:12px 16px;margin-top:10px;\'>"\n'
    '                    "<div style=\'font-size:0.82rem;font-weight:900;color:#991b1b;margin-bottom:6px;\'>"\n'
    '                    "🚨 폐업 법인 긴급 조치 사항</div>"\n'
    '                    "<div style=\'font-size:0.78rem;color:#374151;line-height:1.85;word-break:keep-all;\'>"\n'
    '                    "• 기존 단체보험 해지 및 환급금 수령 안내<br>"\n'
    '                    "• 임직원 개인 보험 전환 설계 (개인 실손·종신)<br>"\n'
    '                    "• 법인 해산·청산 시 잔여 보험금 처리 확인<br>"\n'
    '                    "• 대표자 개인 자산 보호 플랜 즉시 수립"\n'
    '                    "</div></div>",\n'
    '                    unsafe_allow_html=True,\n'
    '                )\n'
    '    _st.markdown("</div>", unsafe_allow_html=True)\n'
    '\n'
    '\n'
)

src = src.replace(ENGINE_F_ANCHOR, ENGINE_F_CODE + ENGINE_F_ANCHOR, 1)
print("✓ [엔진 F] 국세청 사업자 상태조회 엔진 삽입")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. GK-RISK 탭 5개 → 6개
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_5TABS = (
    '    _stab1, _stab2, _stab3, _stab4, _stab5 = st.tabs([\n'
    '        "🏥 실손보험 분석", "💀 생명보험 갭", "🏆 최적 상품 추천",\n'
    '        "⚖️ 법령 검색", "🔬 KCD 상세",\n'
    '    ])'
)
assert src.count(OLD_5TABS) == 1, f"5tabs: {src.count(OLD_5TABS)}"

NEW_6TABS = (
    '    _stab1, _stab2, _stab3, _stab4, _stab5, _stab6 = st.tabs([\n'
    '        "🏥 실손보험 분석", "💀 생명보험 갭", "🏆 최적 상품 추천",\n'
    '        "⚖️ 법령 검색", "🔬 KCD 상세", "🏢 사업자 조회",\n'
    '    ])'
)
src = src.replace(OLD_5TABS, NEW_6TABS, 1)
print("✓ 탭 6개로 확장")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. _stab6 블록 추가
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_STAB5_END = (
    "        else:\n"
    "            st.info(\"좌측 'KCD 질병 검색'에서 질병코드를 선택하면 상세 분석이 표시됩니다.\")\n"
    "\n"
    "\n"
    "\n"
    "def _render_gk_job():"
)
assert src.count(OLD_STAB5_END) == 1, f"stab5_end: {src.count(OLD_STAB5_END)}"

NEW_WITH_STAB6 = (
    "        else:\n"
    "            st.info(\"좌측 'KCD 질병 검색'에서 질병코드를 선택하면 상세 분석이 표시됩니다.\")\n"
    "\n"
    "    with _stab6:\n"
    "        render_biz_status_panel(session_key=\"risk_biz\")\n"
    "\n"
    "\n"
    "\n"
    "def _render_gk_job():"
)
src = src.replace(OLD_STAB5_END, NEW_WITH_STAB6, 1)
print("✓ _stab6 (사업자 조회) 블록 추가")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
new_lines = len(src.split('\n'))
print(f"OK total lines: {new_lines} (+{new_lines-original_lines})")
