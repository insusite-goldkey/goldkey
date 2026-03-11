# -*- coding: utf-8 -*-
"""
[TOTAL STRATEGIC SYSTEM V3] 업그레이드 스크립트
1. 전역 CSS S12 블록 추가 (태블릿 1.2x 폰트, 가로 스크롤 완전 차단, 점선 표준화 확장)
2. [엔진 C] 실손보험 정보 엔진 + 보장 중복/공백 분석 함수 삽입
3. _render_gk_risk() 내부에 실손보험 시너지 UI 탭 추가
4. 전역 CSS에 risk-sector 클래스 + 메가배지 스타일 강화
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
original_len = len(src.split('\n'))
print(f"원본 라인 수: {original_len}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 전역 CSS 끝 "</style>" 앞에 S12 보강 블록 추가
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CSS_ANCHOR = '"thead tr { background: #1565C0 !important; color: #ffffff !important; }"'
assert src.count(CSS_ANCHOR) == 1, f"CSS_ANCHOR count: {src.count(CSS_ANCHOR)}"

CSS_S12 = r'''
            "/* [GP-RESPONSIVE S12-V3] TABLET FONT SCALE 1.2x + RISK SECTOR */"
            "@media screen and (min-width: 768px) and (max-width: 1280px) {"
            "    body, .stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown span {"
            "        font-size: 1.02rem !important;"
            "        line-height: 1.85 !important;"
            "    }"
            "    .stTextInput input, .stSelectbox > div > div {"
            "        font-size: 1.0rem !important;"
            "        min-height: 48px !important;"
            "        padding: 0.65rem 1rem !important;"
            "    }"
            "    .stButton > button {"
            "        font-size: 1.0rem !important;"
            "        min-height: 52px !important;"
            "        padding: 0.65rem 1.4rem !important;"
            "    }"
            "    .risk-badge-wrap { min-height: 200px !important; padding: 24px 20px !important; }"
            "    .risk-mega-badge { font-size: 1.7rem !important; padding: 16px 32px !important; }"
            "}"
            "@media screen and (max-width: 767px) {"
            "    body, .stMarkdown p, .stMarkdown li, .stMarkdown span {"
            "        font-size: 0.95rem !important;"
            "    }"
            "    .risk-badge-wrap { min-height: 80px !important; }"
            "    .risk-mega-badge { font-size: 1.15rem !important; padding: 10px 18px !important; }"
            "}"
            "/* [GP-V3] MEGA BADGE ANIMATION */"
            ".risk-mega-badge-RED {"
            "    background: #dc2626 !important;"
            "    color: #fff !important;"
            "    font-size: 1.35rem !important;"
            "    font-weight: bold !important;"
            "    border-radius: 8px !important;"
            "    padding: 10px 22px !important;"
            "    box-shadow: 0 4px 20px rgba(220,38,38,0.5), 0 0 0 3px #fff, 0 0 0 5px #dc2626 !important;"
            "    display: inline-block !important;"
            "    letter-spacing: 0.03em !important;"
            "    word-break: keep-all !important;"
            "    border: 2px solid #b91c1c !important;"
            "}"
            ".risk-mega-badge-YELLOW {"
            "    background: #f59e0b !important;"
            "    color: #fff !important;"
            "    font-size: 1.35rem !important;"
            "    font-weight: bold !important;"
            "    border-radius: 8px !important;"
            "    padding: 10px 22px !important;"
            "    box-shadow: 0 4px 20px rgba(245,158,11,0.5), 0 0 0 3px #fff, 0 0 0 5px #f59e0b !important;"
            "    display: inline-block !important;"
            "    letter-spacing: 0.03em !important;"
            "    word-break: keep-all !important;"
            "    border: 2px solid #d97706 !important;"
            "}"
            ".risk-mega-badge-GREEN {"
            "    background: #16a34a !important;"
            "    color: #fff !important;"
            "    font-size: 1.35rem !important;"
            "    font-weight: bold !important;"
            "    border-radius: 8px !important;"
            "    padding: 10px 22px !important;"
            "    box-shadow: 0 4px 20px rgba(22,163,74,0.45), 0 0 0 3px #fff, 0 0 0 5px #16a34a !important;"
            "    display: inline-block !important;"
            "    letter-spacing: 0.03em !important;"
            "    word-break: keep-all !important;"
            "    border: 2px solid #15803d !important;"
            "}"
            "/* [GP-V3] SYNERGY PANEL */"
            ".syn-panel {"
            "    border: 1px dashed #000 !important;"
            "    border-radius: 12px !important;"
            "    background: #fff !important;"
            "    padding: 14px 18px !important;"
            "    margin-bottom: 10px !important;"
            "    box-sizing: border-box !important;"
            "    word-break: keep-all !important;"
            "}"
            ".syn-tag {"
            "    display: inline-block;"
            "    padding: 2px 9px;"
            "    border-radius: 8px;"
            "    font-size: 0.68rem;"
            "    font-weight: 800;"
            "    margin-right: 4px;"
            "    margin-bottom: 2px;"
            "}"
            "/* [GP-V3] LOSS INSURANCE PANEL */"
            ".loss-row {"
            "    display: flex;"
            "    align-items: center;"
            "    gap: 8px;"
            "    flex-wrap: wrap;"
            "    padding: 7px 10px;"
            "    border-bottom: 1px dashed #e5e7eb;"
            "    font-size: 0.82rem;"
            "    word-break: keep-all;"
            "}"
            ".loss-ok  { background:#dcfce7; color:#166534; border-radius:6px; padding:2px 8px; font-size:0.70rem; font-weight:800; }"
            ".loss-gap { background:#fee2e2; color:#991b1b; border-radius:6px; padding:2px 8px; font-size:0.70rem; font-weight:800; }"
            ".loss-dup { background:#fef9c3; color:#854d0e; border-radius:6px; padding:2px 8px; font-size:0.70rem; font-weight:800; }"
'''

src = src.replace(
    CSS_ANCHOR,
    CSS_ANCHOR + "\n" + CSS_S12,
    1,
)
print("✓ CSS S12-V3 블록 추가")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. [엔진 C] 실손보험 정보 엔진 삽입 — _RISK_HIGH_KCD_PREFIXES 앞에
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENGINE_C_ANCHOR = "# KCD 고위험 질환 분류 (즉시 RED 배지 대상)"
assert src.count(ENGINE_C_ANCHOR) == 1, f"ENGINE_C_ANCHOR count: {src.count(ENGINE_C_ANCHOR)}"

ENGINE_C = r'''# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [엔진 C] 실손보험 표준 데이터 엔진 (HIRA 인증키 공용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_LOSS_INS_FALLBACK: list = [
    {
        "product_id": "L2024S", "name": "2024년 표준 실손의료보험(4세대)",
        "insurer": "공통 표준", "generation": 4,
        "coverage": [
            {"type": "입원", "limit": 5000, "coinsurance": 20, "deductible": 0, "unit": "만원/회"},
            {"type": "통원(의원)", "limit": 20, "coinsurance": 20, "deductible": 1, "unit": "만원/일"},
            {"type": "통원(병원)", "limit": 30, "coinsurance": 20, "deductible": 2, "unit": "만원/일"},
            {"type": "통원(종합병원)", "limit": 40, "coinsurance": 20, "deductible": 3, "unit": "만원/일"},
            {"type": "처방조제", "limit": 25, "coinsurance": 30, "deductible": 0, "unit": "만원/일"},
        ],
        "exclusions": ["미용·성형", "도수치료(비급여)", "주사치료(비급여)", "체외충격파", "상급병실료(차액)"],
        "notes": "4세대 실손은 비급여 본인부담 30%, 급여 본인부담 20% 적용",
        "law_ref": "보험업법 제95조의2, 금융위원회 고시 실손의료보험 표준약관",
    },
    {
        "product_id": "L2021S", "name": "2021년 표준 실손의료보험(3세대)",
        "insurer": "공통 표준", "generation": 3,
        "coverage": [
            {"type": "입원", "limit": 5000, "coinsurance": 20, "deductible": 0, "unit": "만원/회"},
            {"type": "통원", "limit": 25, "coinsurance": 20, "deductible": 1, "unit": "만원/일"},
            {"type": "처방조제", "limit": 5, "coinsurance": 20, "deductible": 0, "unit": "만원/일"},
        ],
        "exclusions": ["미용·성형", "도수치료 연 350만원 한도 내 초과분", "상급병실료(차액)"],
        "notes": "3세대 실손 — 비급여 특약 분리 운용. 2021.7.1 이후 계약",
        "law_ref": "금융위원회 고시 제2021-18호, 보험업감독규정 별표",
    },
    {
        "product_id": "L2017S", "name": "2017년 표준 실손의료보험(2세대)",
        "insurer": "공통 표준", "generation": 2,
        "coverage": [
            {"type": "입원", "limit": 5000, "coinsurance": 10, "deductible": 0, "unit": "만원/회"},
            {"type": "통원", "limit": 25, "coinsurance": 10, "deductible": 0, "unit": "만원/일"},
        ],
        "exclusions": ["미용·성형", "비급여 주사(일부)", "한방 비급여"],
        "notes": "2세대 실손 — 본인부담 10%, 2009~2017 계약. 중복 가입 시 비례보상",
        "law_ref": "보험업법 제127조의3(중복보험 비례보상)",
    },
    {
        "product_id": "L2009S", "name": "2009년 표준 실손의료보험(1세대·구실손)",
        "insurer": "공통 표준", "generation": 1,
        "coverage": [
            {"type": "입원", "limit": 5000, "coinsurance": 0, "deductible": 0, "unit": "만원/회"},
            {"type": "통원", "limit": 25, "coinsurance": 0, "deductible": 0, "unit": "만원/일"},
        ],
        "exclusions": ["미용·성형"],
        "notes": "1세대 구실손 — 본인부담 0%. 갱신 시 보험료 급등 주의",
        "law_ref": "상법 제638조(보험계약), 보험업법 제102조(보험금 지급)",
    },
]

# KCD → 실손보험 면책·적용 분류
_KCD_LOSS_MAP: dict = {
    "Z41":  {"status": "면책", "reason": "미용·성형 관련 시술"},
    "M47":  {"status": "면책", "reason": "척추병증 — 도수치료 비급여 항목 (4세대 면책)"},
    "M54":  {"status": "조건부", "reason": "요통 — 도수치료 포함 시 세대별 한도 상이"},
    "C":    {"status": "부책", "reason": "악성신생물(암) — 입원/통원 실손 모두 적용"},
    "I6":   {"status": "부책", "reason": "뇌혈관질환 — 입원 실손 적용 (고액 치료비 예상)"},
    "I2":   {"status": "부책", "reason": "허혈심장질환 — 입원 실손 적용"},
    "F0":   {"status": "부책", "reason": "치매 — 요양 입원 실손 적용 (요양병원 제한 조건 확인)"},
    "S":    {"status": "부책", "reason": "손상 — 사고성 실손 전액 적용"},
    "T":    {"status": "부책", "reason": "중독·외상 후속 처치 — 실손 적용"},
    "J45":  {"status": "부책", "reason": "천식 — 입원/통원 실손 적용"},
    "N18":  {"status": "부책", "reason": "만성신장병(투석) — 고액 실손 청구 대상"},
    "E11":  {"status": "조건부", "reason": "2형당뇨 — 합병증 입원 시 실손 적용, 인슐린 주사 비급여 제한"},
    "I10":  {"status": "조건부", "reason": "고혈압 — 합병증 입원 시 실손 적용, 단순 외래 약처방 제한"},
}


def _loss_ins_get_key() -> str:
    """HIRA 인증키 재사용 (금융위 실손 API 동일 키)"""
    return _hira_get_key()


def _loss_ins_search(query: str = "", generation: int = 0) -> list:
    """[엔진 C §1] 실손보험 표준 데이터 조회 — 로컬 폴백 우선 (API 추후 확장)"""
    _results = _LOSS_INS_FALLBACK.copy()
    if generation:
        _results = [r for r in _results if r["generation"] == generation]
    if query.strip():
        _q = query.strip().lower()
        _results = [r for r in _results
                    if _q in r["name"].lower() or _q in r["notes"].lower()
                    or any(_q in e.lower() for e in r["exclusions"])]
    return _results


def _loss_kcd_status(kcd_code: str) -> dict:
    """[엔진 C §2] KCD 코드 → 실손 부책/면책/조건부 상태 반환"""
    if not kcd_code:
        return {}
    for _p in [kcd_code[:4], kcd_code[:3], kcd_code[:2], kcd_code[:1]]:
        if _p in _KCD_LOSS_MAP:
            return _KCD_LOSS_MAP[_p]
    return {"status": "확인필요", "reason": "해당 KCD 코드의 실손 적용 기준을 약관에서 확인하세요."}


def _loss_gap_analysis(client_products: list, kcd_code: str = "") -> dict:
    """[엔진 C §3] 보장 중복/공백 분석
    client_products: [{"name": ..., "generation": ..., "coverage_types": [...]}]
    """
    _gen_counts = {}
    _coverage_all = set()
    for _p in client_products:
        _g = _p.get("generation", 0)
        _gen_counts[_g] = _gen_counts.get(_g, 0) + 1
        for _ct in _p.get("coverage_types", []):
            _coverage_all.add(_ct)

    _gaps = []
    _dups = []
    _ok   = []

    # 세대 중복 체크
    for _g, _cnt in _gen_counts.items():
        if _cnt >= 2:
            _dups.append(f"{_g}세대 실손 {_cnt}건 중복 — 비례보상 적용 (상법 제127조의3)")

    # 기본 커버리지 공백 체크
    _essential = ["입원", "통원"]
    for _e in _essential:
        if _e not in _coverage_all:
            _gaps.append(f"{_e} 실손 미가입 — 보장 공백")

    # KCD 연계 공백
    _kcd_st = _loss_kcd_status(kcd_code)
    if kcd_code and _kcd_st.get("status") == "부책" and not _coverage_all:
        _gaps.append(f"KCD [{kcd_code}] 실손 부책 질환이나 실손 미가입 상태")

    if not _gaps and not _dups:
        _ok.append("현재 보유 실손 구성 정상 — 중복 및 공백 없음")

    return {"gaps": _gaps, "duplicates": _dups, "ok": _ok, "kcd_status": _kcd_st}


def render_loss_insurance_panel(
    session_key: str = "loss_ins",
    kcd_code: str = "",
    client_products: list = None,
) -> None:
    """[엔진 C §4] 실손보험 정보 + 보장 분석 UI 컴포넌트"""
    import streamlit as _st
    if client_products is None:
        client_products = []

    _st.markdown(
        "<div style='border:1px dashed #000;border-radius:12px;"
        "background:#f0f9ff;padding:14px 18px;margin-bottom:10px;'>"
        "<div style='font-size:0.90rem;font-weight:900;color:#0369a1;margin-bottom:8px;'>"
        "🏥 실손보험 분석 센터 — [엔진 C] 표준 데이터 연동</div>",
        unsafe_allow_html=True,
    )

    # KCD 실손 상태 표시
    if kcd_code:
        _kst = _loss_kcd_status(kcd_code)
        _st_color = {"부책": "#16a34a", "면책": "#dc2626", "조건부": "#f59e0b", "확인필요": "#6b7280"}.get(
            _kst.get("status", ""), "#374151"
        )
        _st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;"
            f"padding:8px 12px;background:#fff;border:1px dashed #000;"
            f"border-radius:8px;margin-bottom:8px;'>"
            f"<span style='font-size:0.80rem;font-weight:700;'>🔬 KCD [{kcd_code}] 실손 적용</span>"
            f"<span style='background:{_st_color};color:#fff;border-radius:6px;"
            f"padding:2px 10px;font-size:0.72rem;font-weight:900;'>{_kst.get('status','?')}</span>"
            f"<span style='font-size:0.76rem;color:#374151;flex:1;word-break:keep-all;'>"
            f"{_kst.get('reason','')}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        # 연관 법령
        if _kst.get("status") == "면책":
            _st.markdown(
                "<div class='risk-law-ref'>⚖️ <b>보험업법 제95조의2</b> — 면책 사항은 계약 전 반드시 설명 의무 이행<br>"
                "⚖️ <b>상법(보험편) 제659조</b> — 면책사유 해당 시 보험금 지급 책임 없음</div>",
                unsafe_allow_html=True,
            )
        elif _kst.get("status") == "조건부":
            _st.markdown(
                "<div class='risk-law-ref'>⚖️ <b>상법(보험편) 제651조</b> — 조건부 부책 사항은 고지의무 대상<br>"
                "⚖️ <b>보험업법 제102조</b> — 지급 기준 사전 확인 후 청구 안내 필요</div>",
                unsafe_allow_html=True,
            )

    # 세대별 표준 실손 비교표
    _gen_sel = _st.radio(
        "표준 실손 세대 선택",
        options=["전체", "4세대(2024)", "3세대(2021)", "2세대(2017)", "1세대(구실손)"],
        horizontal=True,
        key=f"{session_key}_gen_sel",
    )
    _gen_map = {"전체": 0, "4세대(2024)": 4, "3세대(2021)": 3, "2세대(2017)": 2, "1세대(구실손)": 1}
    _gen_num = _gen_map.get(_gen_sel, 0)
    _prods   = _loss_ins_search(generation=_gen_num)

    for _p in _prods:
        _gen_color = {"4": "#0369a1", "3": "#7c3aed", "2": "#15803d", "1": "#b45309"}.get(
            str(_p["generation"]), "#374151"
        )
        with _st.expander(
            f"📋 {_p['name']}  ·  {_p['insurer']}",
            expanded=(_gen_num == 4 or _gen_num == 0 and _p["generation"] == 4),
        ):
            _st.markdown(
                f"<div style='font-size:0.72rem;color:{_gen_color};font-weight:800;"
                f"margin-bottom:6px;'>{_p['generation']}세대 실손</div>",
                unsafe_allow_html=True,
            )
            # 커버리지 표
            _hdr = (
                "<div style='display:grid;grid-template-columns:1fr 80px 70px 70px;"
                "gap:4px;padding:6px 10px;background:#1565C0;color:#fff;"
                "border-radius:6px 6px 0 0;font-size:0.72rem;font-weight:800;'>"
                "<span>항목</span><span>한도</span><span>본인부담</span><span>공제</span></div>"
            )
            _rows = ""
            for _cv in _p["coverage"]:
                _rows += (
                    f"<div class='loss-row' style='display:grid;"
                    f"grid-template-columns:1fr 80px 70px 70px;gap:4px;'>"
                    f"<span>{_cv['type']}</span>"
                    f"<span style='font-weight:900;'>{_cv['limit']:,}{_cv['unit']}</span>"
                    f"<span>{_cv['coinsurance']}%</span>"
                    f"<span>{_cv['deductible']}만원</span>"
                    f"</div>"
                )
            _st.markdown(
                f"<div style='border:1px dashed #000;border-radius:8px;overflow:hidden;margin-bottom:6px;'>"
                f"{_hdr}{_rows}</div>",
                unsafe_allow_html=True,
            )
            # 면책 항목
            if _p["exclusions"]:
                _excl_tags = "".join(
                    f"<span class='syn-tag' style='background:#fee2e2;color:#991b1b;'>{e}</span>"
                    for e in _p["exclusions"]
                )
                _st.markdown(
                    f"<div style='margin-top:4px;'>"
                    f"<span style='font-size:0.72rem;font-weight:700;color:#374151;'>면책: </span>"
                    f"{_excl_tags}</div>",
                    unsafe_allow_html=True,
                )
            # 비고 + 법령
            _st.markdown(
                f"<div class='risk-law-ref' style='margin-top:6px;'>"
                f"📝 {_p['notes']}<br>⚖️ {_p['law_ref']}</div>",
                unsafe_allow_html=True,
            )

    # 보장 중복/공백 분석 (client_products 있을 때)
    _st.markdown("---")
    _st.markdown(
        "<div style='font-size:0.82rem;font-weight:800;color:#1e1b4b;margin-bottom:6px;'>"
        "🔍 보장 중복 · 공백 분석</div>",
        unsafe_allow_html=True,
    )

    # 보유 실손 간편 입력
    _held_gen_raw = _st.multiselect(
        "고객 보유 실손 세대 (중복 선택 가능)",
        options=["1세대(구실손)", "2세대(2017)", "3세대(2021)", "4세대(2024)"],
        default=_st.session_state.get(f"{session_key}_held", []),
        key=f"{session_key}_held_sel",
    )
    if _held_gen_raw:
        _st.session_state[f"{session_key}_held"] = _held_gen_raw

    _held_products = [
        {"generation": int(g[0]), "coverage_types": ["입원", "통원"]}
        for g in _held_gen_raw
    ]
    _analysis = _loss_gap_analysis(_held_products, kcd_code=kcd_code)

    if _analysis["duplicates"]:
        for _d in _analysis["duplicates"]:
            _st.markdown(
                f"<div class='loss-row'><span class='loss-dup'>⚠️ 중복</span>"
                f"<span style='font-size:0.80rem;word-break:keep-all;'>{_d}</span></div>",
                unsafe_allow_html=True,
            )
    if _analysis["gaps"]:
        for _g in _analysis["gaps"]:
            _st.markdown(
                f"<div class='loss-row'><span class='loss-gap'>🚨 공백</span>"
                f"<span style='font-size:0.80rem;word-break:keep-all;'>{_g}</span></div>",
                unsafe_allow_html=True,
            )
    if _analysis["ok"]:
        for _o in _analysis["ok"]:
            _st.markdown(
                f"<div class='loss-row'><span class='loss-ok'>✅ 정상</span>"
                f"<span style='font-size:0.80rem;word-break:keep-all;'>{_o}</span></div>",
                unsafe_allow_html=True,
            )

    _st.markdown("</div>", unsafe_allow_html=True)


'''

src = src.replace(ENGINE_C_ANCHOR, ENGINE_C + ENGINE_C_ANCHOR, 1)
print("✓ [엔진 C] 실손보험 정보 엔진 삽입")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. _render_gk_risk() 내부 마지막 법령 검색 뒤에 실손 시너지 UI 탭 추가
#    "KCD 연계 법령 검색" 블록 바로 뒤, 함수 끝 빈 줄 직전
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 현재 함수 끝 — render_law_search 호출 블록 뒤
RISK_BODY_ANCHOR = (
    "    if _active_kcd:\n"
    "        st.markdown(\"---\")\n"
    "        render_law_search(\n"
    "            session_key=\"risk_law\",\n"
    "            kcd_code=_active_kcd,\n"
    "            show_linked=True,\n"
    "        )\n"
)
assert src.count(RISK_BODY_ANCHOR) == 1, f"RISK_BODY_ANCHOR count: {src.count(RISK_BODY_ANCHOR)}"

SYNERGY_BLOCK = r'''    if _active_kcd:
        st.markdown("---")
        render_law_search(
            session_key="risk_law",
            kcd_code=_active_kcd,
            show_linked=True,
        )

    # ── [V3] 3대 데이터 융합 시너지 탭 ─────────────────────────────────────
    st.markdown("<hr style='border:none;border-top:2px dashed #000;margin:24px 0;'>",
                unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:1.0rem;font-weight:900;color:#0369a1;margin-bottom:8px;'>"
        "🔗 3대 데이터 융합 사령부 — 법령 · 질병 · 실손 통합 분석</div>"
        "<div style='font-size:0.76rem;color:#64748b;margin-bottom:10px;word-break:keep-all;'>"
        "KCD 질병코드가 선택되면 실손보험 부책 여부 · 관련 법령 · 위험등급이 한 화면에 연결됩니다.</div>",
        unsafe_allow_html=True,
    )

    _syn_kcd   = (st.session_state.get("risk_kcd_code", "")
                  or st.session_state.get("scan_client_kcd_code", "")
                  or st.session_state.get("sec10_fusion_kcd_code", ""))
    _syn_kcd_nm = (st.session_state.get("risk_kcd", "")
                   or st.session_state.get("scan_client_kcd_name", ""))

    _stab1, _stab2, _stab3 = st.tabs(["🏥 실손보험 분석", "⚖️ 법령 검색", "🔬 KCD 상세"])

    with _stab1:
        render_loss_insurance_panel(
            session_key="risk_loss",
            kcd_code=_syn_kcd,
        )

    with _stab2:
        render_law_search(
            session_key="risk_law2",
            kcd_code=_syn_kcd,
            show_linked=True,
        )
        if _syn_kcd:
            _kst2 = _loss_kcd_status(_syn_kcd)
            if _kst2.get("status") == "면책":
                st.markdown(
                    "<div class='risk-law-ref' style='border:1px dashed #dc2626;background:#fef2f2;'>"
                    "🚨 <b>면책 사유 필수 설명</b> — 보험업법 제95조의2 설명의무 이행 후 계약 체결하십시오.</div>",
                    unsafe_allow_html=True,
                )

    with _stab3:
        if _syn_kcd:
            render_kcd_autocomplete(
                label="KCD 정밀 조회",
                session_key="risk_kcd_detail",
                placeholder="예) 유방암, I21, 뇌경색…",
                autofill_kcd_key="risk_kcd_detail_code",
                show_coverage=True,
            )
            _cov3 = _kcd_get_coverage(_syn_kcd)
            if _cov3:
                _loss3 = _loss_kcd_status(_syn_kcd)
                _s3col = {"부책": "#16a34a", "면책": "#dc2626", "조건부": "#f59e0b"}.get(
                    _loss3.get("status", ""), "#374151"
                )
                st.markdown(
                    f"<div class='syn-panel'>"
                    f"<div style='font-size:0.82rem;font-weight:900;color:#000;margin-bottom:6px;'>"
                    f"🔬 {_syn_kcd_nm or _syn_kcd} 종합 분석</div>"
                    f"<div style='display:flex;gap:8px;flex-wrap:wrap;'>"
                    f"<span class='syn-tag' style='background:{_cov3.get('bg','#f8fafc')};color:{_cov3.get('color','#374151')};'>"
                    f"보장: {_cov3.get('label','—')}</span>"
                    f"<span class='syn-tag' style='background:{_s3col};color:#fff;'>"
                    f"실손: {_loss3.get('status','?')}</span>"
                    f"<span class='syn-tag' style='background:#f1f5f9;color:#1e293b;'>"
                    f"KCD: {_syn_kcd}</span>"
                    f"</div>"
                    f"<div style='font-size:0.74rem;color:#374151;margin-top:6px;line-height:1.75;word-break:keep-all;'>"
                    f"{_loss3.get('reason','')}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("좌측 'KCD 질병 검색'에서 질병코드를 선택하면 상세 분석이 표시됩니다.")

'''

src = src.replace(RISK_BODY_ANCHOR, SYNERGY_BLOCK, 1)
print("✓ 실손+법령+KCD 시너지 탭 삽입")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
lines = src.split('\n')
print(f"OK total lines: {len(lines)} (+{len(lines)-original_len})")
