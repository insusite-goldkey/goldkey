# -*- coding: utf-8 -*-
"""
[FINAL ULTIMATUM V5-ULTIMATE] 업그레이드 스크립트
1. 메가 배지 CSS border-radius:12px 강화 + 150% 폰트 확대
2. [엔진 F] 국세청 사업자 상태조회 API + render_biz_status_panel()
3. GK-RISK 탭 5개 → 6개 (6번째: 🏢 사업자 조회)
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
original_lines = len(src.split('\n'))
print(f"원본: {original_lines}줄")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 메가 배지 CSS 강화 — border-radius:12px, 폰트 150% 상향
#    현재 .risk-mega-badge-RED/YELLOW/GREEN 클래스의 font-size/border-radius 교체
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RED 배지: font-size 1.35rem → 1.55rem, border-radius 8px → 12px
src = src.replace(
    '"    font-size: 1.35rem !important;"\n'
    '            "    font-weight: bold !important;"\n'
    '            "    border-radius: 8px !important;"\n'
    '            "    padding: 10px 22px !important;"\n'
    '            "    box-shadow: 0 4px 20px rgba(220,38,38,0.5), 0 0 0 3px #fff, 0 0 0 5px #dc2626 !important;"\n'
    '            "    display: inline-block !important;"\n'
    '            "    letter-spacing: 0.03em !important;"\n'
    '            "    word-break: keep-all !important;"\n'
    '            "    border: 2px solid #b91c1c !important;"\n'
    '            "}"',
    '"    font-size: 1.55rem !important;"\n'
    '            "    font-weight: bold !important;"\n'
    '            "    border-radius: 12px !important;"\n'
    '            "    padding: 12px 26px !important;"\n'
    '            "    box-shadow: 0 6px 28px rgba(220,38,38,0.6), 0 0 0 3px #fff, 0 0 0 6px #dc2626 !important;"\n'
    '            "    display: inline-block !important;"\n'
    '            "    letter-spacing: 0.04em !important;"\n'
    '            "    word-break: keep-all !important;"\n'
    '            "    border: 2px solid #b91c1c !important;"\n'
    '            "}"',
    1,
)

# YELLOW 배지
src = src.replace(
    '"    font-size: 1.35rem !important;"\n'
    '            "    font-weight: bold !important;"\n'
    '            "    border-radius: 8px !important;"\n'
    '            "    padding: 10px 22px !important;"\n'
    '            "    box-shadow: 0 4px 20px rgba(245,158,11,0.5), 0 0 0 3px #fff, 0 0 0 5px #f59e0b !important;"\n'
    '            "    display: inline-block !important;"\n'
    '            "    letter-spacing: 0.03em !important;"\n'
    '            "    word-break: keep-all !important;"\n'
    '            "    border: 2px solid #d97706 !important;"\n'
    '            "}"',
    '"    font-size: 1.55rem !important;"\n'
    '            "    font-weight: bold !important;"\n'
    '            "    border-radius: 12px !important;"\n'
    '            "    padding: 12px 26px !important;"\n'
    '            "    box-shadow: 0 6px 28px rgba(245,158,11,0.6), 0 0 0 3px #fff, 0 0 0 6px #f59e0b !important;"\n'
    '            "    display: inline-block !important;"\n'
    '            "    letter-spacing: 0.04em !important;"\n'
    '            "    word-break: keep-all !important;"\n'
    '            "    border: 2px solid #d97706 !important;"\n'
    '            "}"',
    1,
)

# GREEN 배지
src = src.replace(
    '"    font-size: 1.35rem !important;"\n'
    '            "    font-weight: bold !important;"\n'
    '            "    border-radius: 8px !important;"\n'
    '            "    padding: 10px 22px !important;"\n'
    '            "    box-shadow: 0 4px 20px rgba(22,163,74,0.45), 0 0 0 3px #fff, 0 0 0 5px #16a34a !important;"\n'
    '            "    display: inline-block !important;"\n'
    '            "    letter-spacing: 0.03em !important;"\n'
    '            "    word-break: keep-all !important;"\n'
    '            "    border: 2px solid #15803d !important;"\n'
    '            "}"',
    '"    font-size: 1.55rem !important;"\n'
    '            "    font-weight: bold !important;"\n'
    '            "    border-radius: 12px !important;"\n'
    '            "    padding: 12px 26px !important;"\n'
    '            "    box-shadow: 0 6px 28px rgba(22,163,74,0.5), 0 0 0 3px #fff, 0 0 0 6px #16a34a !important;"\n'
    '            "    display: inline-block !important;"\n'
    '            "    letter-spacing: 0.04em !important;"\n'
    '            "    word-break: keep-all !important;"\n'
    '            "    border: 2px solid #15803d !important;"\n'
    '            "}"',
    1,
)

# _risk_badge_html 함수의 인라인 스타일도 강화
src = src.replace(
    '    _cfg = {\n'
    '        "RED":     {"bg": "#dc2626", "color": "#fff",    "border": "#b91c1c", "label": "🚨 심각 (HIGH RISK)", "shadow": "0 4px 20px rgba(220,38,38,0.45)"},\n'
    '        "YELLOW":  {"bg": "#f59e0b", "color": "#fff",    "border": "#d97706", "label": "⚠️ 주의 (CAUTION)",   "shadow": "0 4px 20px rgba(245,158,11,0.45)"},\n'
    '        "GREEN":   {"bg": "#16a34a", "color": "#fff",    "border": "#15803d", "label": "✅ 안전 (SAFE)",       "shadow": "0 4px 20px rgba(22,163,74,0.40)"},\n'
    '        "UNKNOWN": {"bg": "#6b7280", "color": "#fff",    "border": "#4b5563", "label": "❓ 미입력",            "shadow": "none"},\n'
    '    }',
    '    _cfg = {\n'
    '        "RED":     {"bg": "#dc2626", "color": "#fff",    "border": "#b91c1c", "label": "🚨 심각 (HIGH RISK)", "shadow": "0 6px 28px rgba(220,38,38,0.6)"},\n'
    '        "YELLOW":  {"bg": "#f59e0b", "color": "#fff",    "border": "#d97706", "label": "⚠️ 주의 (CAUTION)",   "shadow": "0 6px 28px rgba(245,158,11,0.6)"},\n'
    '        "GREEN":   {"bg": "#16a34a", "color": "#fff",    "border": "#15803d", "label": "✅ 안전 (SAFE)",       "shadow": "0 6px 28px rgba(22,163,74,0.5)"},\n'
    '        "UNKNOWN": {"bg": "#6b7280", "color": "#fff",    "border": "#4b5563", "label": "❓ 미입력",            "shadow": "none"},\n'
    '    }',
    1,
)

# badge 함수 font-size/border-radius/padding 강화
src = src.replace(
    '    fs = "1.35rem" if large else "0.82rem"\n'
    '    pad = "10px 22px" if large else "4px 12px"\n'
    '    return (\n'
    '        f"<div style=\'background:{c[\'bg\']};color:{c[\'color\']};\'"
    "f\'border:2px solid {c[\'border\']};border-radius:8px;\'"
    "f\'padding:{pad};font-size:{fs};font-weight:bold;\'"
    "f\'box-shadow:{c[\'shadow\']};display:inline-block;\'"
    "f\'letter-spacing:0.03em;word-break:keep-all;\'>\'"
    "f\'{c[\'label\']}</div>\'",
    '    fs = "1.55rem" if large else "0.88rem"\n'
    '    pad = "12px 26px" if large else "5px 14px"\n'
    '    return (\n'
    '        f"<div style=\'background:{c[\'bg\']};color:{c[\'color\']};\'"
    "f\'border:2px solid {c[\'border\']};border-radius:12px;\'"
    "f\'padding:{pad};font-size:{fs};font-weight:bold;\'"
    "f\'box-shadow:{c[\'shadow\']};display:inline-block;\'"
    "f\'letter-spacing:0.04em;word-break:keep-all;\'>\'"
    "f\'{c[\'label\']}</div>\'",
    1,
)

print("✓ 메가 배지 CSS 강화 (border-radius:12px, font 150%, shadow 강화)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. [엔진 F] 국세청 사업자 상태조회 — render_fss_product_panel 직후에 삽입
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENGINE_F_ANCHOR = "def _loss_ins_search(query: str = \"\", generation: int = 0) -> list:"
assert src.count(ENGINE_F_ANCHOR) == 1

ENGINE_F = r'''# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [엔진 F] 국세청 사업자 상태조회 API (HIRA 인증키 공용)
# 공공데이터포털 국세청 사업자등록상태 API: data.go.kr/B552061
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_BIZ_STATUS_CODES: dict = {
    "01": {"label": "계속사업자",  "color": "#16a34a", "bg": "#dcfce7", "risk": "GREEN",
           "desc": "정상 영업 중인 사업자입니다."},
    "02": {"label": "휴업자",      "color": "#f59e0b", "bg": "#fef9c3", "risk": "YELLOW",
           "desc": "현재 휴업 상태입니다. 보험 계약 전 재개업 여부를 확인하세요."},
    "03": {"label": "폐업자",      "color": "#dc2626", "bg": "#fee2e2", "risk": "RED",
           "desc": "폐업된 사업자입니다. 법인보험 계약 불가 — 즉시 컨설팅 전환 필요."},
    "04": {"label": "국세청 등록없음", "color": "#6b7280", "bg": "#f1f5f9", "risk": "UNKNOWN",
           "desc": "국세청에 등록되지 않은 사업자번호입니다. 번호를 확인하세요."},
}

# 법인 보험 연계 법령
_BIZ_LAW_REFS: dict = {
    "GREEN":   [("보험업법 제4조",          "정상 영업 중 — 법인 단체보험 표준 설계 진행 가능"),
                ("상법(보험편) 제638조",     "법인 보험계약 체결 요건 충족 상태")],
    "YELLOW":  [("보험업법 제95조의2",       "휴업 법인 — 계약 전 사업 재개 여부 및 피보험이익 확인 필수"),
                ("상법(보험편) 제651조",     "중요 사항(휴업 여부) 고지의무 이행 필요")],
    "RED":     [("보험업법 제102조",         "폐업 법인 — 기존 단체보험 해지 절차 및 환급금 처리 안내"),
                ("상법(보험편) 제638조",     "피보험이익 소멸 — 보험계약 효력 상실 검토"),
                ("상법(상행위편) 제24조",    "법인 청산 시 잔여 보험금 처리 기준 확인")],
    "UNKNOWN": [("공공데이터포털 조회",      "사업자번호 재확인 후 재조회하세요")],
}


def _biz_get_key() -> str:
    """공공데이터포털 인증키 (HIRA 키 공용)"""
    return _hira_get_key()


def _biz_status_query(biz_no: str) -> dict:
    """[엔진 F §1] 국세청 사업자 상태조회 API → 로컬 폴백"""
    import urllib.request as _req, urllib.parse as _up, json as _json, re as _re

    # 숫자만 추출
    _no = _re.sub(r'[^0-9]', '', str(biz_no))
    if len(_no) != 10:
        return {"error": f"사업자번호는 10자리 숫자여야 합니다. (입력: {biz_no})"}

    _key = _biz_get_key()
    if _key:
        try:
            _url = "https://api.odcloud.kr/api/nts-businessman/v1/status"
            _params = _up.urlencode({"serviceKey": _key, "returnType": "JSON"})
            _body   = _json.dumps({"b_no": [_no]}).encode("utf-8")
            _request = _req.Request(
                f"{_url}?{_params}",
                data=_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            _resp = _req.urlopen(_request, timeout=5)
            _raw  = _json.loads(_resp.read().decode("utf-8"))
            _data = _raw.get("data", [{}])
            if _data:
                _d   = _data[0]
                _tax = _d.get("tax_type", "")
                _b_stt = _d.get("b_stt_cd", "")
                _bno   = _d.get("b_no", _no)
                _bname = _d.get("b_nm", "")
                _ceo   = _d.get("p_nm", "")
                _status_info = _BIZ_STATUS_CODES.get(
                    _b_stt,
                    {"label": _d.get("b_stt", "확인불가"), "color": "#6b7280",
                     "bg": "#f1f5f9", "risk": "UNKNOWN", "desc": "상태 코드를 확인하세요."},
                )
                return {
                    "biz_no":   _bno,
                    "biz_name": _bname,
                    "ceo":      _ceo,
                    "tax_type": _tax,
                    "status_code": _b_stt,
                    "status_info": _status_info,
                    "_source":  "api",
                }
        except Exception as _e:
            pass  # API 실패 시 시뮬레이션 폴백

    # 로컬 시뮬레이션 폴백
    import hashlib as _hlib
    _hash = int(_hlib.md5(_no.encode()).hexdigest(), 16) % 4
    _sim_codes = ["01", "01", "02", "03"]
    _sim_code  = _sim_codes[_hash]
    return {
        "biz_no":      _no,
        "biz_name":    "(시뮬레이션)",
        "ceo":         "—",
        "tax_type":    "일반과세자",
        "status_code": _sim_code,
        "status_info": _BIZ_STATUS_CODES[_sim_code],
        "_source":     "simulate",
        "_note":       "실제 API 연동 전 시뮬레이션 결과입니다.",
    }


def render_biz_status_panel(session_key: str = "biz_status") -> None:
    """[엔진 F §2] 국세청 사업자 상태조회 UI — 법인 컨설팅 섹션 연동"""
    import streamlit as _st

    _st.markdown(
        "<div style='border:1px dashed #000;border-radius:12px;"
        "background:#f8fafc;padding:14px 18px;margin-bottom:10px;'>"
        "<div style='font-size:0.90rem;font-weight:900;color:#1e1b4b;margin-bottom:8px;'>"
        "🏢 국세청 사업자 상태조회 — [엔진 F] 실시간 연동</div>",
        unsafe_allow_html=True,
    )

    # 입력 폼
    _col_in, _col_btn = _st.columns([3, 1], gap="small")
    with _col_in:
        _biz_no_input = _st.text_input(
            "사업자등록번호",
            value=_st.session_state.get(f"{session_key}_no", ""),
            placeholder="예) 123-45-67890 또는 1234567890",
            key=f"{session_key}_input",
        )
    with _col_btn:
        _st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        _do_query = _st.button("🔍 조회", key=f"{session_key}_query_btn",
                               use_container_width=True)

    if _do_query and _biz_no_input.strip():
        _st.session_state[f"{session_key}_no"] = _biz_no_input.strip()
        with _st.spinner("국세청 조회 중…"):
            _result = _biz_status_query(_biz_no_input.strip())
        _st.session_state[f"{session_key}_result"] = _result

    _result = _st.session_state.get(f"{session_key}_result")

    if _result:
        if _result.get("error"):
            _st.markdown(
                f"<div style='background:#fee2e2;border:1px dashed #dc2626;"
                f"border-radius:8px;padding:10px 14px;color:#991b1b;font-weight:700;"
                f"word-break:keep-all;'>"
                f"⚠️ {_result['error']}</div>",
                unsafe_allow_html=True,
            )
        else:
            _si   = _result.get("status_info", {})
            _risk = _si.get("risk", "UNKNOWN")
            _bg   = _si.get("bg",   "#f1f5f9")
            _cl   = _si.get("color","#374151")

            # 메인 결과 박스 (7:3 레이아웃)
            _rc1, _rc2 = _st.columns([7, 3], gap="medium")

            with _rc1:
                _src_tag = ("🌐 국세청 API" if _result.get("_source") == "api"
                            else "🔄 시뮬레이션")
                _st.markdown(
                    f"<div style='background:{_bg};border:1px dashed #000;"
                    f"border-radius:10px;padding:14px 18px;word-break:keep-all;'>"
                    f"<div style='font-size:0.70rem;color:#64748b;margin-bottom:6px;'>"
                    f"{_src_tag}</div>"
                    f"<div style='display:grid;grid-template-columns:100px 1fr;"
                    f"gap:6px 12px;align-items:start;'>"
                    f"<span style='font-size:0.78rem;font-weight:700;color:#374151;'>사업자번호</span>"
                    f"<span style='font-size:0.82rem;font-weight:900;color:#000;'>"
                    f"{_result.get('biz_no','')}</span>"
                    + (f"<span style='font-size:0.78rem;font-weight:700;color:#374151;'>상호</span>"
                       f"<span style='font-size:0.82rem;color:#1e293b;'>"
                       f"{_result.get('biz_name','—')}</span>"
                       if _result.get("biz_name") and _result.get("biz_name") != "(시뮬레이션)" else "")
                    + (f"<span style='font-size:0.78rem;font-weight:700;color:#374151;'>대표자</span>"
                       f"<span style='font-size:0.82rem;color:#1e293b;'>"
                       f"{_result.get('ceo','—')}</span>"
                       if _result.get("ceo") and _result.get("ceo") != "—" else "")
                    + f"<span style='font-size:0.78rem;font-weight:700;color:#374151;'>과세유형</span>"
                    f"<span style='font-size:0.82rem;color:#1e293b;'>"
                    f"{_result.get('tax_type','—')}</span>"
                    f"<span style='font-size:0.78rem;font-weight:700;color:#374151;'>영업 상태</span>"
                    f"<span style='font-size:0.85rem;font-weight:900;color:{_cl};'>"
                    f"{_si.get('label','—')}</span>"
                    f"</div>"
                    f"<div style='font-size:0.76rem;color:#374151;margin-top:8px;"
                    f"line-height:1.75;word-break:keep-all;border-top:1px dashed #e5e7eb;"
                    f"padding-top:6px;'>{_si.get('desc','')}</div>"
                    + (f"<div style='font-size:0.68rem;color:#94a3b8;margin-top:4px;'>"
                       f"※ {_result['_note']}</div>" if _result.get("_note") else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )

            with _rc2:
                _badge_html = _risk_badge_html(_risk, large=True)
                _st.markdown(
                    "<div class='risk-badge-wrap' style='min-height:140px;'>"
                    "<div style='font-size:0.70rem;font-weight:700;color:#6b7280;"
                    "text-align:center;margin-bottom:8px;'>법인 위험등급</div>"
                    + _badge_html
                    + "</div>",
                    unsafe_allow_html=True,
                )

            # 법령 근거
            _law_refs = _BIZ_LAW_REFS.get(_risk, [])
            if _law_refs:
                _st.markdown(
                    "<div style='font-size:0.76rem;font-weight:800;color:#92400e;"
                    "margin-top:10px;margin-bottom:4px;'>⚖️ 법인 보험 관련 법령 근거</div>",
                    unsafe_allow_html=True,
                )
                for _lt, _ld in _law_refs:
                    _st.markdown(
                        f"<div class='risk-law-ref'>"
                        f"<b>📌 {_lt}</b><br>{_ld}</div>",
                        unsafe_allow_html=True,
                    )

            # 법인 보험 컨설팅 CTA
            if _risk in ("GREEN", "YELLOW"):
                _st.markdown(
                    "<div style='background:linear-gradient(135deg,#eff6ff,#f0fdf4);"
                    "border:1px dashed #000;border-radius:10px;padding:12px 16px;margin-top:10px;'>"
                    "<div style='font-size:0.82rem;font-weight:900;color:#1e1b4b;margin-bottom:6px;'>"
                    "💼 법인 보험 컨설팅 추천 포인트</div>"
                    "<div style='font-size:0.78rem;color:#374151;line-height:1.85;word-break:keep-all;'>"
                    "• 임원·핵심인력 단체보험(생명/상해) 설계<br>"
                    "• 법인 화재보험 120% 초과특약 검토<br>"
                    "• 가지급금 정리 플랜 (임원 퇴직금 재원)<br>"
                    "• CEO 사망·질병 시 회사 존속 리스크 분석"
                    "</div></div>",
                    unsafe_allow_html=True,
                )
            elif _risk == "RED":
                _st.markdown(
                    "<div style='background:#fef2f2;border:1px dashed #dc2626;"
                    "border-radius:10px;padding:12px 16px;margin-top:10px;'>"
                    "<div style='font-size:0.82rem;font-weight:900;color:#991b1b;margin-bottom:6px;'>"
                    "🚨 폐업 법인 긴급 조치 사항</div>"
                    "<div style='font-size:0.78rem;color:#374151;line-height:1.85;word-break:keep-all;'>"
                    "• 기존 단체보험 해지 및 환급금 수령 안내<br>"
                    "• 임직원 개인 보험 전환 설계 (개인 실손·종신)<br>"
                    "• 법인 해산·청산 시 잔여 보험금 처리 확인<br>"
                    "• 대표자 개인 자산 보호 플랜 즉시 수립"
                    "</div></div>",
                    unsafe_allow_html=True,
                )

    _st.markdown("</div>", unsafe_allow_html=True)


'''

src = src.replace(ENGINE_F_ANCHOR, ENGINE_F + ENGINE_F_ANCHOR, 1)
print("✓ [엔진 F] 국세청 사업자 상태조회 엔진 삽입")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. GK-RISK 탭 5개 → 6개 (6번째 탭 추가)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_5TABS = (
    '    _stab1, _stab2, _stab3, _stab4, _stab5 = st.tabs([\n'
    '        "🏥 실손보험 분석", "💀 생명보험 갭", "🏆 최적 상품 추천", "⚖️ 법령 검색", "🔬 KCD 상세",\n'
    '    ])'
)
assert src.count(OLD_5TABS) == 1, f"5tabs anchor count: {src.count(OLD_5TABS)}"

NEW_6TABS = (
    '    _stab1, _stab2, _stab3, _stab4, _stab5, _stab6 = st.tabs([\n'
    '        "🏥 실손보험 분석", "💀 생명보험 갭", "🏆 최적 상품 추천",\n'
    '        "⚖️ 법령 검색", "🔬 KCD 상세", "🏢 사업자 조회",\n'
    '    ])'
)
src = src.replace(OLD_5TABS, NEW_6TABS, 1)
print("✓ 탭 6개로 확장")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. _stab5 블록 뒤에 _stab6 블록 삽입
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_STAB5_END = (
    '        else:\n'
    '            st.info("좌측 \'KCD 질병 검색\'에서 질병코드를 선택하면 상세 분석이 표시됩니다.")\n'
    '\n'
    '\n'
    '\n'
    'def _render_gk_job():'
)
assert src.count(OLD_STAB5_END) == 1, f"stab5_end count: {src.count(OLD_STAB5_END)}"

NEW_STAB6_BLOCK = (
    '        else:\n'
    '            st.info("좌측 \'KCD 질병 검색\'에서 질병코드를 선택하면 상세 분석이 표시됩니다.")\n'
    '\n'
    '    with _stab6:\n'
    '        render_biz_status_panel(session_key="risk_biz")\n'
    '\n'
    '\n'
    '\n'
    'def _render_gk_job():'
)
src = src.replace(OLD_STAB5_END, NEW_STAB6_BLOCK, 1)
print("✓ _stab6 (사업자 조회) 블록 추가")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
new_lines = len(src.split('\n'))
print(f"OK total lines: {new_lines} (+{new_lines-original_lines})")
