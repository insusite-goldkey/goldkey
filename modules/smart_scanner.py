# modules/smart_scanner.py
# ============================================================
# SmartScanner — 중앙통제형 재사용 스캔 컴포넌트 (DRY 원칙)
#
# 사용법:
#   from modules.smart_scanner import render_smart_scanner, render_scan_report
#
#   render_smart_scanner(doc_type="의무기록")   # 어느 섹터에서든 동일 UI
#   render_scan_report()                        # 분석 결과 리포트 + 출력 버튼
# ============================================================

import time
import json
import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────────────────────
# KCD 코드 → 질환 정보 매핑 테이블
# ─────────────────────────────────────────────────────────────
KCD_MAP: dict = {
    # 심장
    "I20.9": {"disease": "협심증 (Angina Pectoris)",        "sector": "heart",      "payout": 20_000_000, "label": "심장질환"},
    "I21.9": {"disease": "급성 심근경색 (AMI)",              "sector": "heart",      "payout": 30_000_000, "label": "심장질환"},
    "I50.9": {"disease": "심부전",                           "sector": "heart",      "payout": 15_000_000, "label": "심장질환"},
    # 뇌
    "I63.9": {"disease": "뇌경색 (Cerebral Infarction)",     "sector": "brain",      "payout": 30_000_000, "label": "뇌질환"},
    "I61.9": {"disease": "뇌출혈 (ICH)",                     "sector": "brain",      "payout": 30_000_000, "label": "뇌질환"},
    "G45.9": {"disease": "일과성 뇌허혈 (TIA)",              "sector": "brain",      "payout": 10_000_000, "label": "뇌질환"},
    # 암
    "C34.1": {"disease": "폐암 (Lung Cancer)",               "sector": "cancer",     "payout": 50_000_000, "label": "암질환"},
    "C18.9": {"disease": "대장암 (Colon Cancer)",            "sector": "cancer",     "payout": 50_000_000, "label": "암질환"},
    "C50.9": {"disease": "유방암 (Breast Cancer)",           "sector": "cancer",     "payout": 50_000_000, "label": "암질환"},
    # 장해·상해
    "S72.0": {"disease": "대퇴골 경부 골절",                 "sector": "disability", "payout": 10_000_000, "label": "골절·장해"},
    "M51.1": {"disease": "추간판 탈출증 (디스크)",           "sector": "disability", "payout":  8_000_000, "label": "척추질환"},
    "S06.3": {"disease": "외상성 뇌손상 (TBI)",              "sector": "disability", "payout": 20_000_000, "label": "뇌손상"},
}

# KCD 코드 → 섹터 라우팅 맵
KCD_SECTOR_ROUTE: dict = {
    "heart":      "heart",
    "brain":      "brain",
    "cancer":     "cancer",
    "disability": "disability",
    "injury":     "injury",
}

# ─────────────────────────────────────────────────────────────
# Mock NER 엔진 — 실제 Gemini Vision 연동 전 시뮬레이션
# ─────────────────────────────────────────────────────────────
_MOCK_NER_RESULTS: list[dict] = [
    {
        "kcd_code":    "I20.9",
        "disease":     "협심증 (Angina Pectoris)",
        "surgery":     "관상동맥 스텐트 삽입술 (PCI)",
        "doctor_note": "관상동맥 협착 70% 확인. 우측 관상동맥(RCA)에 약물 용출 스텐트(DES) 삽입. "
                       "시술 후 TIMI flow grade 3 회복. 현재 심박출률(EF) 55%로 정상 범위. "
                       "항혈소판제(아스피린·클로피도그렐) 병용 투여 중.",
        "sector":      "heart",
        "payout":      20_000_000,
    },
    {
        "kcd_code":    "I63.9",
        "disease":     "뇌경색 (Cerebral Infarction)",
        "surgery":     "혈전 용해술 (tPA 정맥 투여)",
        "doctor_note": "좌측 중대뇌동맥(MCA) 영역 급성 뇌경색. "
                       "발병 4시간 내 내원하여 tPA 투여. MRI DWI에서 제한성 확산 소견. "
                       "좌측 상하지 경미한 편마비 잔존.",
        "sector":      "brain",
        "payout":      30_000_000,
    },
    {
        "kcd_code":    "S72.0",
        "disease":     "대퇴골 경부 골절",
        "surgery":     "인공 고관절 전치환술 (THA)",
        "doctor_note": "낙상으로 인한 우측 대퇴골 경부 골절. Garden stage III. "
                       "수술적 치료로 비골두 보존 어려워 인공 고관절 전치환술 시행. "
                       "보행 보조기 사용 재활 중.",
        "sector":      "disability",
        "payout":      10_000_000,
    },
]


def _run_mock_ner(files: list, doc_type: str) -> dict:
    """
    Mock NER 분석 — 업로드된 파일 수·문서 유형에 따라
    KCD 추출 결과 반환 (실제 Gemini Vision 연동 시 교체).
    """
    import random
    if doc_type in ("의무기록", "의무기록·진단서", "🏥 의무기록·진단서"):
        result = random.choice(_MOCK_NER_RESULTS)
    else:
        result = _MOCK_NER_RESULTS[0]

    return {
        "kcd_code":    result["kcd_code"],
        "disease":     result["disease"],
        "surgery":     result["surgery"],
        "doctor_note": result["doctor_note"],
        "sector":      result["sector"],
        "payout":      result["payout"],
        "file_count":  len(files) if files else 0,
        "doc_type":    doc_type,
    }


# ─────────────────────────────────────────────────────────────
# PRINT CSS — @media print A4 출력 (components.html 주입)
# ─────────────────────────────────────────────────────────────
_PRINT_CSS = """
<style>
@media print {
  /* 사이드바·헤더·푸터·네비·버튼 전부 숨김 */
  [data-testid="stSidebar"],
  [data-testid="stHeader"],
  [data-testid="stToolbar"],
  [data-testid="stDecoration"],
  footer,
  .stButton,
  .stRadio,
  .stSelectbox,
  .stFileUploader,
  .stAlert,
  .stTabs,
  #gk-print-hide { display: none !important; }

  /* 리포트 본문만 A4로 */
  #gk-print-report {
    width: 210mm !important;
    margin: 0 auto !important;
    padding: 18mm !important;
    background: #fff !important;
    color: #000 !important;
    font-size: 11pt !important;
    line-height: 1.6 !important;
  }

  .gk-report-card {
    page-break-inside: avoid;
    border: 1px solid #ccc !important;
    box-shadow: none !important;
  }

  .gk-payout-box {
    border: 2px solid #000 !important;
    background: #fff !important;
    color: #000 !important;
  }
}
</style>
"""


# ─────────────────────────────────────────────────────────────
# [메인] SmartScanner UI — 어느 섹터에서든 호출 가능
# ─────────────────────────────────────────────────────────────
def render_smart_scanner(
    doc_type: str = "의무기록",
    session_key: str = "smart_scanner_result",
    uploader_key: str = "smart_scanner_files",
    show_result_inline: bool = True,
):
    """
    중앙통제형 SmartScanner 컴포넌트.

    Parameters
    ----------
    doc_type          : 기본 문서 유형 (라디오 버튼 기본값)
    session_key       : 결과를 저장할 session_state 키
    uploader_key      : file_uploader 위젯 키 (섹터별 고유값 권장)
    show_result_inline: True면 스캔 완료 후 같은 화면에 리포트 표시
    """

    # ── Print CSS 주입 (1회) ──────────────────────────────────
    components.html(_PRINT_CSS, height=0)

    # ── 그룹 박스 헤더 ─────────────────────────────────────────
    st.markdown("""
<div id="gk-print-hide" style="background:linear-gradient(135deg,#0d3b2e 0%,#1a6b4a 100%);
  border-radius:12px;padding:12px 18px 10px 18px;margin-bottom:10px;">
  <div style="color:#fff;font-size:1rem;font-weight:900;letter-spacing:0.04em;">
    🔬 SmartScanner — AI 의무기록 판독
  </div>
  <div style="color:#a8e6cf;font-size:0.74rem;margin-top:3px;">
    진단서·의무기록을 업로드하면 KCD 코드 자동 추출 → 예상 보장금액 산출 → 해당 섹터 자동 이동
  </div>
</div>""", unsafe_allow_html=True)

    # ── SSOT 캐시 알림 ─────────────────────────────────────────
    _ssot = st.session_state.get("ssot_scan_data", [])
    if _ssot:
        st.info(f"💾 통합 스캔 허브에 저장된 문서 **{len(_ssot)}건** 이 있습니다. "
                "아래에서 새 파일을 업로드하거나, 기존 스캔 결과를 재분석할 수 있습니다.",
                icon="📂")

    # ── 문서 유형 선택 ─────────────────────────────────────────
    _dtype = st.radio(
        "문서 유형",
        ["의무기록", "진단서", "보험증권", "청구서류"],
        horizontal=True,
        key=f"{uploader_key}_dtype",
        index=["의무기록", "진단서", "보험증권", "청구서류"].index(
            doc_type if doc_type in ["의무기록", "진단서", "보험증권", "청구서류"] else "의무기록"
        ),
    )

    # ── 파일 업로더 ────────────────────────────────────────────
    _files = st.file_uploader(
        "📎 파일 첨부 (PDF / JPG / PNG — 복수 업로드 가능)",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=uploader_key,
    )

    # ── 스캔 실행 버튼 ─────────────────────────────────────────
    _btn_col, _route_col = st.columns([2, 1])
    with _btn_col:
        _do_scan = st.button(
            "🔬 AI 의무기록 판독 시작",
            key=f"{uploader_key}_run",
            use_container_width=True,
            type="primary",
            disabled=not _files,
        )
    with _route_col:
        _auto_route = st.toggle(
            "분석 후 자동 이동",
            value=True,
            key=f"{uploader_key}_autoroute",
        )

    # ── 스캔 실행 로직 ─────────────────────────────────────────
    if _do_scan and _files:
        with st.spinner("🔬 의무기록을 판독 중입니다... (AI NER 분석)"):
            time.sleep(2)   # Mock: 실제 Gemini Vision 연동 시 대체
            _result = _run_mock_ner(_files, _dtype)

        # SSOT 세션에 저장
        st.session_state[session_key] = _result
        st.session_state["smart_scan_ready"] = True
        st.session_state["smart_scan_sector"] = _result["sector"]

        st.success(
            f"✅ 판독 완료 — **{_result['disease']}** (KCD: `{_result['kcd_code']}`)"
        )
        st.rerun()

    # ── 인라인 리포트 출력 ─────────────────────────────────────
    if show_result_inline and st.session_state.get("smart_scan_ready"):
        _result = st.session_state.get(session_key)
        if _result:
            render_scan_report(_result, auto_route=_auto_route)


# ─────────────────────────────────────────────────────────────
# [서브] 분석 결과 리포트 렌더러
# ─────────────────────────────────────────────────────────────
def render_scan_report(result: dict, auto_route: bool = False):
    """
    분석 결과를 A4 리포트 형식으로 렌더링.
    우측 상단 [출력하기] 버튼 포함 (@media print 적용).
    """
    if not result:
        return

    kcd   = result.get("kcd_code", "-")
    dis   = result.get("disease",  "-")
    surg  = result.get("surgery",  "-")
    note  = result.get("doctor_note", "-")
    pay   = result.get("payout", 0)
    sec   = result.get("sector", "home")
    fcnt  = result.get("file_count", 0)

    # ── 출력 버튼 (우측 상단) ──────────────────────────────────
    _hdr_l, _hdr_r = st.columns([4, 1])
    with _hdr_l:
        st.markdown("""
<div style="font-size:1rem;font-weight:900;color:#1a3a5c;
  border-left:4px solid #2e6da4;padding-left:10px;margin:8px 0;">
  📄 AI 보장 분석 리포트
</div>""", unsafe_allow_html=True)
    with _hdr_r:
        components.html("""
<button onclick="window.print()"
  style="width:100%;padding:8px 12px;background:#2e6da4;color:#fff;
  border:none;border-radius:8px;font-weight:900;font-size:0.82rem;
  cursor:pointer;white-space:nowrap;">
  🖨️ 출력하기
</button>""", height=44)

    # ── 리포트 카드 본체 ───────────────────────────────────────
    st.markdown(f"""
<div id="gk-print-report">
<div class="gk-report-card" style="background:#fff;border:1.5px solid #e2e8f0;
  border-radius:14px;padding:20px 24px;margin-bottom:12px;
  box-shadow:0 2px 12px rgba(0,0,0,0.07);">

  <div style="display:flex;align-items:center;justify-content:space-between;
    border-bottom:2px solid #f1f5f9;padding-bottom:12px;margin-bottom:16px;">
    <div>
      <div style="font-size:0.72rem;font-weight:700;color:#94a3b8;
        letter-spacing:0.08em;">질병분류코드 (KCD)</div>
      <div style="font-size:1.8rem;font-weight:900;color:#2563eb;
        letter-spacing:0.04em;">{kcd}</div>
    </div>
    <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;
      padding:6px 14px;font-size:0.78rem;font-weight:900;color:#166534;">
      📂 {fcnt}개 파일 분석 완료
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">
    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;">
      <div style="font-size:0.70rem;font-weight:700;color:#94a3b8;margin-bottom:4px;">진단명</div>
      <div style="font-size:0.88rem;font-weight:900;color:#1e293b;">{dis}</div>
    </div>
    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;">
      <div style="font-size:0.70rem;font-weight:700;color:#94a3b8;margin-bottom:4px;">수술·시술</div>
      <div style="font-size:0.88rem;font-weight:900;color:#1e293b;">{surg}</div>
    </div>
  </div>

  <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
    padding:12px 16px;margin-bottom:14px;">
    <div style="font-size:0.70rem;font-weight:700;color:#3b82f6;margin-bottom:6px;">
      🩺 AI 의사 소견 번역
    </div>
    <div style="font-size:0.82rem;color:#1e3a5f;line-height:1.75;font-weight:500;">
      {note}
    </div>
  </div>

  <div class="gk-payout-box" style="background:#1e293b;color:#fff;border-radius:12px;
    padding:16px 20px;display:flex;align-items:center;justify-content:space-between;">
    <div style="font-size:0.9rem;font-weight:900;">
      💰 예상 지급 보험금 총액
    </div>
    <div style="font-size:1.5rem;font-weight:900;color:#4ade80;">
      {pay:,}원
    </div>
  </div>

  <div style="margin-top:10px;font-size:0.68rem;color:#94a3b8;text-align:right;">
    * 본 리포트는 참고용 보조 지표이며 법적 효력이 없습니다.
  </div>
</div>
</div>
""", unsafe_allow_html=True)

    # ── 섹터 라우팅 버튼 ───────────────────────────────────────
    _sector_label = {
        "heart":      "❤️ 심장질환 상담",
        "brain":      "🧠 뇌질환 상담",
        "cancer":     "🎗️ 암질환 상담",
        "disability": "🩺 장해산출",
        "injury":     "🚑 상해통합관리",
    }
    _label = _sector_label.get(sec, f"📋 {sec} 섹터")

    st.markdown("---")
    _r1, _r2 = st.columns([1, 1])
    with _r1:
        if st.button(
            f"➡️ {_label} 으로 이동",
            key="smart_scan_route_btn",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["current_tab"] = sec
            st.session_state["smart_scan_ready"] = False
            st.rerun()
    with _r2:
        if st.button("🔄 새 문서 재스캔", key="smart_scan_reset_btn", use_container_width=True):
            st.session_state["smart_scan_ready"] = False
            st.session_state.pop("smart_scanner_result", None)
            st.rerun()


# ─────────────────────────────────────────────────────────────
# [유틸] 다른 섹터에서 SSOT 스캔 결과 확인 위젯
# ─────────────────────────────────────────────────────────────
def render_ssot_banner(sector: str = ""):
    """
    scan_hub SSOT 결과가 있을 때 상단 배너로 알림.
    disability / heart / brain / cancer 섹터에서 호출.
    """
    _result = st.session_state.get("smart_scanner_result")
    if not _result:
        return

    _kcd = _result.get("kcd_code", "")
    _dis = _result.get("disease", "")
    _sec = _result.get("sector", "")

    if sector and _sec != sector:
        return  # 다른 섹터 결과는 표시 안 함

    st.markdown(f"""
<div style="background:#f0fdf4;border:1.5px solid #86efac;border-radius:10px;
  padding:10px 16px;margin-bottom:10px;">
  <span style="font-size:0.78rem;font-weight:900;color:#166534;">
    🔬 SmartScanner 판독 결과 자동 주입
  </span><br>
  <span style="font-size:0.82rem;color:#1e3a5f;">
    <b>KCD:</b> {_kcd} &nbsp;|&nbsp; <b>진단명:</b> {_dis}
  </span>
</div>""", unsafe_allow_html=True)
