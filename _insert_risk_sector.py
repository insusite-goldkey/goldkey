# -*- coding: utf-8 -*-
"""
[STRATEGIC RISK CENTER] 독립 섹터 신설 스크립트
1. SECTOR_CODES에 gk_risk 섹터 등록 (코드 2700)
2. _render_gk_risk() 렌더러 삽입 (_render_gk_job 앞)
3. 라우터 추가 (GK-JOB 라우터 앞)
4. 위험등급 배지 CSS — 폰트 150%, 고채도, border-radius:8px
5. KCD 고위험 질환 → RED 배지 자동 변환 + 법령 근거 노출
6. 태블릿 7:3 레이아웃
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. SECTOR_CODES에 gk_risk 등록
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SC_ANCHOR = '    "9900": {"name": "VVIP CEO 통합 경영 전략 센터"'
assert src.count(SC_ANCHOR) == 1, f"SC_ANCHOR count: {src.count(SC_ANCHOR)}"

SECTOR_RISK = '''    # ── 2700: 전략적 위험 분석 사령부 (STRATEGIC RISK CENTER) ──────────────────
    "2700": {"name": "전략적 위험 분석 사령부", "tab_key": "gk_risk", "keywords": [
        "위험분석", "위험등급", "리스크센터", "gk-risk", "전략위험",
        "고위험질환", "kcd위험", "위험사령부", "리스크배지", "위험배지",
        "고위험", "위험도", "위험도분석", "전략리스크",
    ]},
    '''

src = src.replace(SC_ANCHOR, SECTOR_RISK + SC_ANCHOR, 1)
print("✓ SECTOR_CODES 등록")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. _render_gk_risk() 렌더러 삽입 — _render_gk_job() def 앞에
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RENDERER_ANCHOR = "def _render_gk_job():"
assert src.count(RENDERER_ANCHOR) == 1

RENDERER = r'''# ══════════════════════════════════════════════════════════════
# [GK-RISK] 전략적 위험 분석 사령부 렌더러
# KCD 고위험 질환 자동 RED 배지 + 법령 근거 연동
# ══════════════════════════════════════════════════════════════

# KCD 고위험 질환 분류 (즉시 RED 배지 대상)
_RISK_HIGH_KCD_PREFIXES: tuple = (
    "C",    # 악성신생물 (암 전체)
    "I6",   # 뇌혈관질환 (뇌졸중·뇌경색·뇌출혈)
    "I21",  # 급성심근경색
    "I22",  # 재발성 급성심근경색
    "F00",  # 알츠하이머치매
    "F01",  # 혈관치매
    "F02",  # 기타 치매
    "F03",  # 상세불명 치매
    "G20",  # 파킨슨병
    "K74",  # 간경변증
    "N18",  # 만성신장병 4~5기
    "J96",  # 호흡부전
)

_RISK_MED_KCD_PREFIXES: tuple = (
    "I20",  # 협심증
    "I25",  # 만성허혈심장질환
    "I50",  # 심부전
    "E10",  # 1형당뇨
    "E11",  # 2형당뇨
    "I10",  # 고혈압
    "M05",  # 류마티스관절염
    "J45",  # 천식
    "S06",  # 두개내손상
    "S72",  # 대퇴골골절
)

# 위험등급 → 법령 근거 매핑
_RISK_LAW_REFS: dict = {
    "RED": [
        ("상법(보험편) 제651조", "고지의무 위반 시 보험사 해지권 행사 가능 — 고위험 질환 고지 필수"),
        ("보험업법 제95조의2", "설계사 설명의무 — 고위험 질환자 보장 제한 사항 반드시 설명"),
        ("금융소비자보호법 제19조", "적합성 원칙 — 고위험 고객의 상품 적합성 사전 확인 의무"),
    ],
    "YELLOW": [
        ("상법(보험편) 제651조", "유병자 고지의무 — 2년 이내 병력 고지 대상 여부 확인"),
        ("보험업법 제102조", "보험금 지급 — 7일 이내 결정 원칙, 분쟁 예방을 위한 서류 완비"),
    ],
    "GREEN": [
        ("상법(보험편) 제638조", "보험계약 성립 요건 — 정상 인수 가능 상태"),
        ("보험업법 제4조", "보험업 허가 요건 — 표준 상품 설계 진행 가능"),
    ],
}


def _risk_assess_kcd(kcd_code: str) -> str:
    """KCD 코드로 위험등급 반환: RED / YELLOW / GREEN / UNKNOWN"""
    if not kcd_code:
        return "UNKNOWN"
    for p in _RISK_HIGH_KCD_PREFIXES:
        if kcd_code.upper().startswith(p):
            return "RED"
    for p in _RISK_MED_KCD_PREFIXES:
        if kcd_code.upper().startswith(p):
            return "YELLOW"
    return "GREEN"


def _risk_badge_html(grade: str, large: bool = True) -> str:
    """위험등급 배지 HTML — large=True 시 150% 크기"""
    _cfg = {
        "RED":     {"bg": "#dc2626", "color": "#fff",    "border": "#b91c1c", "label": "🚨 심각 (HIGH RISK)", "shadow": "0 4px 20px rgba(220,38,38,0.45)"},
        "YELLOW":  {"bg": "#f59e0b", "color": "#fff",    "border": "#d97706", "label": "⚠️ 주의 (CAUTION)",   "shadow": "0 4px 20px rgba(245,158,11,0.45)"},
        "GREEN":   {"bg": "#16a34a", "color": "#fff",    "border": "#15803d", "label": "✅ 안전 (SAFE)",       "shadow": "0 4px 20px rgba(22,163,74,0.40)"},
        "UNKNOWN": {"bg": "#6b7280", "color": "#fff",    "border": "#4b5563", "label": "❓ 미입력",            "shadow": "none"},
    }
    c = _cfg.get(grade, _cfg["UNKNOWN"])
    fs = "1.35rem" if large else "0.82rem"
    pad = "10px 22px" if large else "4px 12px"
    return (
        f"<div style='background:{c['bg']};color:{c['color']};"
        f"border:2px solid {c['border']};border-radius:8px;"
        f"padding:{pad};font-size:{fs};font-weight:bold;"
        f"box-shadow:{c['shadow']};display:inline-block;"
        f"letter-spacing:0.03em;word-break:keep-all;'>"
        f"{c['label']}</div>"
    )


def _render_gk_risk():
    """[GK-RISK] 전략적 위험 분석 사령부 — KCD·건강보험료·직업 통합 위험등급"""
    import streamlit as st

    st.markdown("""<style>
.risk-wrap {
    background: linear-gradient(135deg, #fff7f7 0%, #fffbeb 50%, #f0fdf4 100%);
    border: 2px dashed #000;
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 18px;
    box-sizing: border-box;
    word-break: keep-all;
}
.risk-panel {
    background: rgba(255,255,255,0.92);
    border: 1px dashed #000;
    border-radius: 12px;
    padding: 18px 22px;
    box-sizing: border-box;
    word-break: keep-all;
}
.risk-badge-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 160px;
    background: rgba(255,255,255,0.85);
    border: 2px dashed #000;
    border-radius: 14px;
    padding: 20px 16px;
    box-sizing: border-box;
    word-break: keep-all;
}
.risk-law-ref {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.74rem;
    color: #78350f;
    line-height: 1.75;
    margin-top: 6px;
    word-break: keep-all;
}
@media (max-width: 900px) {
    .risk-wrap { padding: 14px 12px; }
    .risk-panel { padding: 12px 14px; }
    .risk-badge-wrap { min-height: 100px; padding: 12px 10px; }
}
</style>""", unsafe_allow_html=True)

    tab_home_btn("gk_risk")

    st.markdown(
        "<div style='background:linear-gradient(135deg,#7f1d1d 0%,#991b1b 60%,#dc2626 100%);"
        "border-radius:14px;padding:20px 28px;margin-bottom:10px;border:1px solid #ef4444;'>"
        "<div style='font-size:1.35rem;font-weight:900;color:#fef2f2;letter-spacing:0.04em;'>"
        "🚨 전략적 위험 분석 사령부 — STRATEGIC RISK CENTER</div>"
        "<div style='font-size:0.85rem;color:#fca5a5;margin-top:6px;line-height:1.6;'>"
        "KCD 질병코드 · 직업 위험등급 · 건강보험료 역산 통합 위험도 산출 &nbsp;·&nbsp; "
        "<span style='background:#fef2f2;color:#7f1d1d;border-radius:6px;"
        "padding:1px 8px;font-weight:800;font-size:0.78rem;'>⚡ 사령관 최우선 확인</span>"
        "</div>"
        "</div>", unsafe_allow_html=True
    )

    # ── 입력 소스 수집 ────────────────────────────────────────────────────────
    _kcd_code  = st.session_state.get("scan_client_kcd_code", "") or st.session_state.get("sec10_fusion_kcd_code", "")
    _kcd_name  = st.session_state.get("scan_client_kcd_name", "")
    _job_grade = st.session_state.get("gs_job_grade", 0)
    _nhis_prem = st.session_state.get("gs_nhis_premium", 0)
    _si_sick   = st.session_state.get("home_si_sick", "해당 없음")

    # ── 위험등급 계산 ─────────────────────────────────────────────────────────
    _kcd_grade  = _risk_assess_kcd(_kcd_code)
    _job_risk   = "RED" if _job_grade >= 4 else ("YELLOW" if _job_grade >= 2 else "GREEN")
    _sick_risk  = "RED" if _si_sick and _si_sick not in ("해당 없음", "없음", "") else "GREEN"

    _grade_rank = {"RED": 3, "YELLOW": 2, "GREEN": 1, "UNKNOWN": 0}
    _overall = max([_kcd_grade, _job_risk, _sick_risk], key=lambda g: _grade_rank.get(g, 0))

    st.markdown("<div class='risk-wrap'>", unsafe_allow_html=True)

    # ── 7:3 레이아웃 (좌: 분석 패널, 우: 대형 배지) ──────────────────────────
    _lc, _rc = st.columns([7, 3], gap="medium")

    with _lc:
        st.markdown("<div class='risk-panel'>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:1.0rem;font-weight:900;color:#1e1b4b;margin-bottom:12px;'>"
            "📋 위험 인자 분석 현황</div>",
            unsafe_allow_html=True,
        )

        # KCD 인자
        _kcd_badge_sm = _risk_badge_html(_kcd_grade, large=False)
        _kcd_disp = f"[{_kcd_code}] {_kcd_name}" if _kcd_code else "—"
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;"
            f"padding:8px 0;border-bottom:1px dashed #e5e7eb;'>"
            f"<span style='font-size:0.82rem;font-weight:700;color:#374151;min-width:90px;'>"
            f"🔬 KCD 질병</span>"
            f"<span style='font-size:0.82rem;color:#1e293b;'>{_kcd_disp}</span>"
            f"<span style='margin-left:auto;'>{_kcd_badge_sm}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # 직업 위험등급 인자
        _job_badge_sm = _risk_badge_html(_job_risk, large=False)
        _job_disp = f"상해급수 {_job_grade}급" if _job_grade else "—"
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;"
            f"padding:8px 0;border-bottom:1px dashed #e5e7eb;'>"
            f"<span style='font-size:0.82rem;font-weight:700;color:#374151;min-width:90px;'>"
            f"💼 직업 위험</span>"
            f"<span style='font-size:0.82rem;color:#1e293b;'>{_job_disp}</span>"
            f"<span style='margin-left:auto;'>{_job_badge_sm}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # 유병자 여부 인자
        _sick_badge_sm = _risk_badge_html(_sick_risk, large=False)
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;"
            f"padding:8px 0;border-bottom:1px dashed #e5e7eb;'>"
            f"<span style='font-size:0.82rem;font-weight:700;color:#374151;min-width:90px;'>"
            f"🏥 유병 여부</span>"
            f"<span style='font-size:0.82rem;color:#1e293b;'>{_si_sick or '—'}</span>"
            f"<span style='margin-left:auto;'>{_sick_badge_sm}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # 건강보험료 역산 참고
        if _nhis_prem:
            import math as _math
            _est_income = round(_nhis_prem / 0.0709 / 10000) * 10000
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;"
                f"padding:8px 0;'>"
                f"<span style='font-size:0.82rem;font-weight:700;color:#374151;min-width:90px;'>"
                f"💰 건보료 역산</span>"
                f"<span style='font-size:0.82rem;color:#1e293b;'>"
                f"월 {_nhis_prem:,}원 → 추정월소득 약 {_est_income:,}원</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # ── 법령 근거 ────────────────────────────────────────────────────────
        _law_refs = _RISK_LAW_REFS.get(_overall, [])
        if _law_refs:
            st.markdown(
                "<div style='font-size:0.76rem;font-weight:800;color:#92400e;"
                "margin-top:10px;margin-bottom:4px;'>⚖️ 위험등급 산출 법령 근거</div>",
                unsafe_allow_html=True,
            )
            for _law_title, _law_desc in _law_refs:
                st.markdown(
                    f"<div class='risk-law-ref'>"
                    f"<b>📌 {_law_title}</b><br>{_law_desc}</div>",
                    unsafe_allow_html=True,
                )

    with _rc:
        st.markdown("<div class='risk-badge-wrap'>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:0.72rem;font-weight:700;color:#6b7280;"
            "margin-bottom:10px;text-align:center;'>종합 위험등급</div>",
            unsafe_allow_html=True,
        )
        st.markdown(_risk_badge_html(_overall, large=True), unsafe_allow_html=True)
        _overall_kor = {"RED": "고위험 — 인수 조건 정밀 검토 필요",
                        "YELLOW": "주의 — 유병자 보험 검토 권장",
                        "GREEN": "표준 인수 가능",
                        "UNKNOWN": "정보 입력 후 산출"}.get(_overall, "")
        st.markdown(
            f"<div style='font-size:0.72rem;color:#374151;margin-top:10px;"
            f"text-align:center;line-height:1.6;word-break:keep-all;'>{_overall_kor}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── 직접 입력 섹션 (KCD 미입력 시) ──────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.9rem;font-weight:800;color:#1e1b4b;margin-bottom:8px;'>"
        "🔧 위험 인자 직접 입력 (GK-SEC-01 미입력 시 보완)</div>",
        unsafe_allow_html=True,
    )
    _ri_c1, _ri_c2 = st.columns(2)
    with _ri_c1:
        _ri_kcd = render_kcd_autocomplete(
            label="KCD 질병 검색",
            session_key="risk_kcd",
            placeholder="예) 유방암, I21, 뇌경색…",
            autofill_kcd_key="risk_kcd_code",
            show_coverage=True,
        )
    with _ri_c2:
        _ri_grade = st.selectbox(
            "직업 상해급수",
            options=[0, 1, 2, 3, 4, 5, 6],
            index=_job_grade if _job_grade <= 6 else 0,
            format_func=lambda x: f"{x}급" if x > 0 else "미입력",
            key="risk_job_grade_sel",
        )
        if _ri_grade:
            st.session_state["gs_job_grade"] = _ri_grade

    # ── KCD 연계 법령 검색 ────────────────────────────────────────────────────
    _active_kcd = (st.session_state.get("risk_kcd_code", "")
                   or st.session_state.get("scan_client_kcd_code", ""))
    if _active_kcd:
        st.markdown("---")
        render_law_search(
            session_key="risk_law",
            kcd_code=_active_kcd,
            show_linked=True,
        )


'''

src = src.replace(RENDERER_ANCHOR, RENDERER + RENDERER_ANCHOR, 1)
print("✓ _render_gk_risk() 렌더러 삽입")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 라우터 추가 — GK-JOB 라우터 앞에
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROUTER_ANCHOR = "    # ══════════════════════════════════════════════════════════════════════\n    # [GK-JOB] 계층형 직업 진단 엔진 라우터"
assert src.count(ROUTER_ANCHOR) == 1, f"ROUTER_ANCHOR count: {src.count(ROUTER_ANCHOR)}"

ROUTER_RISK = """    # ══════════════════════════════════════════════════════════════════════
    # [GK-RISK] 전략적 위험 분석 사령부 라우터
    # ══════════════════════════════════════════════════════════════════════
    if cur == "gk_risk":
        _render_gk_risk()
        st.stop()

    """

src = src.replace(ROUTER_ANCHOR, ROUTER_RISK + ROUTER_ANCHOR, 1)
print("✓ 라우터 추가")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
lines = src.split('\n')
print(f"OK total lines: {len(lines)}")
