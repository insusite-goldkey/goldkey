# modules/smart_scanner.py
# ============================================================
# SmartScanner — 중앙통제형 재사용 스캔 컴포넌트 (DRY 원칙)
#
# 사용법:
#   from modules.smart_scanner import (
#       render_smart_scanner, render_scan_report,   # 의료 스캔
#       render_legal_scanner, render_legal_report,  # 법률 스캔
#       render_ssot_banner,
#   )
#
#   render_smart_scanner(doc_type="의무기록")   # 의료: 어느 섹터에서든 동일 UI
#   render_legal_scanner()                      # 법률: 판결문·소장·행정처분 분석
#   render_legal_report()                       # 법률: A4 리포트 + 답변서 초안 생성
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


# =============================================================
# ██  법률·행정 SmartScanner (LegalTech)  ██
# =============================================================
# 3단계 구조:
#   1단계 — Legal NER   : 사건번호·법원·당사자·청구취지·적용법조 추출
#   2단계 — Legal Trans : 판결문 평어 번역 (법률 용어 → 쉬운 우리말)
#   3단계 — Generative  : 답변서·내용증명 초안 자동 작성
#
# [할루시네이션 방지 6대 절대 수칙 내장]
#   1. 법조문·판례 창작 절대 금지 — regex 검증 후 미확인 시 '원본 기재 없음'
#   2. 손해사정 산출 출처(sourceRule) 의무 명시
#   3. 법적 기한 AI 산출 금지 — 법원 직접 확인 경고 강제
#   4. 초안 템플릿/AI생성 영역 시각 분리 ([AI_TEXT] 태그)
#   5. Confidence Score 0-100 의무 반환 + 색상 분기
#   6. 실제 데이터 오인 방지 — Mock 시연 버너 고정 표시
# =============================================================

import re as _re

# ─────────────────────────────────────────────────────────────
# [수칙 1] 법조문 형식 검증 regex
# ─────────────────────────────────────────────────────────────
_LAW_PATTERN = _re.compile(
    r"(민법|상법|형법|형사소송법|민사소송법|보험업법|약관규제법|소비자기본법"
    r"|특정범죄가중처벌법|금융소비자보호법|변호사법|행정소송법|가이딩 프로토콜)"
    r"\s*제\d+조"
)


def _validate_legal_basis(legal_basis: str) -> tuple[str, str]:
    """법조문 형식 검증. 반환: (검증된_텍스트, 검증_상태)"""
    if not legal_basis or legal_basis.strip() in ("-", ""):
        return "원본 기재 없음", "unverified"
    matches = _LAW_PATTERN.findall(legal_basis)
    if matches:
        return legal_basis, "verified"
    return legal_basis + " ⚠️ (형식 미확인 — 원본 직접 확인 필요)", "unverified"


# ─────────────────────────────────────────────────────────────
# [수칙 5] Confidence Score 색상 분기 헬퍼
# ─────────────────────────────────────────────────────────────
def _confidence_style(score: int) -> dict:
    """90↑초록 / 70~89주황 / 70↓빨강"""
    if score >= 90:
        return {"bg": "#f0fdf4", "border": "#86efac", "text": "#166534", "label": "높음"}
    if score >= 70:
        return {"bg": "#fff7ed", "border": "#fdba74", "text": "#9a3412", "label": "보통"}
    return {"bg": "#fef2f2", "border": "#fca5a5", "text": "#7f1d1d", "label": "낮음 — 원본 확인 필수"}


# ─────────────────────────────────────────────────────────────
# Mock Legal NER 결과 — 실제 Gemini Vision 연동 전 시뮬레이션
# ─────────────────────────────────────────────────────────────
_MOCK_LEGAL_NER: list[dict] = [
    {
        "doc_type":      "구상금 청구 소장",
        "case_number":   "2026가소98765",
        "court":         "서울중앙지방법원",
        "plaintiff":     "A 화재해상보험(주)",
        "defendant":     "김고객 (본인)",
        "claim_amount":  5_000_000,
        "claim_summary": "원고는 2024년 9월 3일 발생한 교통사고로 인하여 피해자에게 보험금 5,000,000원을 지급하였는바, 피고의 과실에 의한 구상금 청구의 소를 제기함.",
        "legal_basis":   "상법 제682조 (대위권), 민법 제750조 (불법행위)",
        "deadline_days": None,
        "easy_summary":  "상대방(A보험사)이 과거 교통사고와 관련해 고객님께 500만 원을 물어내라는 소송을 걸었습니다. 기한은 사건별로 상이하므로 반드시 대법원 나의사건검색 및 법원 송달 서류를 직접 확인하십시오.",
        "verdict":       None,
        "confidence":    78,
        "source_rule":   "스캔본 소장 본문 (1페이지 청구취지) 기준 추출",
        "sector":        "t1",   # 보험금 청구 상담
    },
    {
        "doc_type":      "보험금 지급 거절 통보서 (행정처분)",
        "case_number":   "금감원-2026-민원-00123",
        "court":         "금융감독원 분쟁조정위원회",
        "plaintiff":     "B 생명보험(주)",
        "defendant":     "이고객 (청구인)",
        "claim_amount":  20_000_000,
        "claim_summary": "피보험자의 진단서상 KCD I21.9(급성심근경색)에 대해 '계약 전 알릴 의무 위반(고지의무 위반)'을 이유로 보험금 지급을 거절함.",
        "legal_basis":   "보험업법 제651조 (고지의무), 약관규제법 제5조 (불명확 약관 고객 유리 해석)",
        "deadline_days": None,
        "easy_summary":  "B보험사가 '가입할 때 병력을 숨겼다'는 이유로 심근경색 보험금 2,000만 원 지급을 거절했습니다. 하지만 약관 문구가 불명확하면 고객에게 유리하게 해석해야 합니다. 분쟁조정 신청 기한은 사건별로 상이하므로 반드시 금감원 공식 안내를 직접 확인하십시오.",
        "verdict":       None,
        "confidence":    82,
        "source_rule":   "스캔본 보험금 지급 거절 통보서 + KCD I21.9 진단서 대조 기준 추출",
        "sector":        "t1",
    },
    {
        "doc_type":      "손해배상 청구 판결문",
        "case_number":   "2025나11234",
        "court":         "서울고등법원 제3민사부",
        "plaintiff":     "박원고",
        "defendant":     "C 손해보험(주)",
        "claim_amount":  15_000_000,
        "claim_summary": "원고의 청구를 인용하여 피고는 원고에게 15,000,000원 및 이에 대한 소장 송달일 다음날부터 다 갚는 날까지 연 12%의 비율에 의한 금원을 지급하라.",
        "legal_basis":   "상법 제658조 (보험금 지연지급), 소비자기본법 제19조",
        "deadline_days": None,
        "easy_summary":  "고객님(원고)이 승소하셨습니다! C보험사가 보험금 1,500만 원과 연 12% 이자를 지급해야 합니다. 강제집행 신청 기한은 사건별로 상이하므로 반드시 대법원 나의사건검색 및 법원 판결문 원본을 직접 확인하십시오.",
        "verdict":       "원고 승소",
        "confidence":    91,
        "source_rule":   "스캔본 판결문 주문(主文) 및 이유 섹션 직접 추출",
        "sector":        "t1",
    },
]

# ─────────────────────────────────────────────────────────────
# 답변서 초안 템플릿 생성기
# ─────────────────────────────────────────────────────────────
def _generate_answer_draft(data: dict) -> str:
    """법원 제출용 표준 답변서 초안 텍스트 생성.
    [수칙 4] 고정 템플릿(TEMPLATE)과 AI생성(AI_TEXT) 영역을 태그로 명확히 분리.
    """
    today = __import__("datetime").date.today().strftime("%Y. %m. %d.")
    return f"""[TEMPLATE_START]
답  변  서

사 건: {data.get('case_number', '')}  {data.get('doc_type', '')}
원 고: {data.get('plaintiff', '')}
피 고: {data.get('defendant', '')}

위 사건에 관하여 피고는 다음과 같이 답변합니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[청구 취지에 대한 답변]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 원고의 청구를 기각한다.
2. 소송비용은 원고가 부담한다.
라는 판결을 구합니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[청구 원인에 대한 답변]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 원고 주장의 요지
[TEMPLATE_END]
[AI_TEXT]
원고는 "{data.get('claim_summary', '')}"라고 주장하나, 이는 사실과 다르며
아래와 같이 반박합니다.
[/AI_TEXT]
[TEMPLATE_START]
2. 피고의 반박 사유
[TEMPLATE_END]
[AI_TEXT]
· 피고는 해당 사고 당시 법령을 준수하였으며 원고 주장과 같은 귀책사유가 없습니다.
· 적용 법조 ({data.get('legal_basis', '')}) 검토 결과,
  피고에게 배상 책임을 귀속시킬 인과관계가 성립하지 않습니다.
· 원고가 제출한 증거자료의 신빙성에 대하여 다툽니다.
[/AI_TEXT]
[TEMPLATE_START]
3. 결론
원고의 청구는 이유 없으므로 기각되어야 합니다.

{today}
위 피고  {data.get('defendant', '')}  (인)

[제출처] {data.get('court', '')}  귀중

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[주의] 법적 제출 기한은 반드시 법원 송달 서류를 직접 확인하십시오.
       AI는 소송 기한을 보장하지 않습니다 (오판 시 무변론 패소 위험).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
본 초안은 AI가 생성한 참고용 문서입니다.
실제 제출 전 반드시 변호사·손해사정인의 검토를 받으시기 바랍니다.
[TEMPLATE_END]"""


def _generate_complaint_draft(data: dict) -> str:
    """내용증명 초안 텍스트 생성.
    [수칙 4] 고정 템플릿(TEMPLATE)과 AI생성(AI_TEXT) 영역을 태그로 명확히 분리.
    """
    today = __import__("datetime").date.today().strftime("%Y. %m. %d.")
    return f"""[TEMPLATE_START]
내  용  증  명

수 신: {data.get('plaintiff', '')} 귀중
발 신: {data.get('defendant', '')}
제 목: {data.get('doc_type', '')} 관련 이의 및 보험금 지급 촉구

귀사의 무궁한 발전을 기원합니다.

본인({data.get('defendant', '')})은 귀사가 {data.get('case_number', '')}와 관련하여
청구금액 {data.get('claim_amount', 0):,}원의 지급 거절(또는 청구)에 대해
다음과 같이 공식적으로 이의를 제기합니다.
[TEMPLATE_END]
[AI_TEXT]
1. 이의 사유
· 귀사의 처분/청구는 {data.get('legal_basis', '')}에 근거하고 있으나,
  해당 조항의 적용 요건이 충족되지 않았습니다.
· 본인은 계약 체결 시 성실히 고지의무를 이행하였으며,
  관련 증빙자료를 보유하고 있습니다.
[/AI_TEXT]
[TEMPLATE_START]
2. 요구 사항
본 내용증명 수령 후 14일 이내에 서면으로 답변해 주시기 바랍니다.
정당한 사유 없이 답변이 없을 경우 금융감독원 분쟁조정 신청 및
민사소송을 제기할 예정임을 알립니다.

{today}
발신인  {data.get('defendant', '')}  (인)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[주의] 내용증명 발송 후 기한 계산은 반드시 우체국 접수증 기준으로 확인하십시오.
       AI는 법적 효력을 갖는 날짜를 보장하지 않습니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
본 초안은 AI가 생성한 참고용 문서입니다.
실제 발송 전 반드시 전문가의 검토를 받으시기 바랍니다.
[TEMPLATE_END]"""


def _strip_draft_tags(text: str) -> str:
    """[TEMPLATE_START], [TEMPLATE_END], [AI_TEXT], [/AI_TEXT] 태그를 제거하여 plain text 반환."""
    for tag in ("[TEMPLATE_START]", "[TEMPLATE_END]", "[AI_TEXT]", "[/AI_TEXT]"):
        text = text.replace(tag, "")
    return text.strip()


def _render_draft_with_highlights(text: str) -> None:
    """
    [수칙 4] 초안 텍스트를 파싱하여 템플릿(검정)과 AI생성(인디고 박스)을 시각적으로 분리 렌더링.
    - [TEMPLATE_START]...[TEMPLATE_END] : 검정 고정 서식
    - [AI_TEXT]...[/AI_TEXT]           : 인디고 하이라이트 박스 (AI 작성 표시)
    """
    import html as _html

    # 토큰 분리
    _TK_TS  = "[TEMPLATE_START]"
    _TK_TE  = "[TEMPLATE_END]"
    _TK_AS  = "[AI_TEXT]"
    _TK_AE  = "[/AI_TEXT]"

    parts = _re.split(
        r"(\[TEMPLATE_START\]|\[TEMPLATE_END\]|\[AI_TEXT\]|\[/AI_TEXT\])",
        text,
    )

    html_blocks = []
    mode = "template"  # 초기 상태
    for part in parts:
        if part == _TK_TS:
            mode = "template"
        elif part == _TK_TE:
            pass
        elif part == _TK_AS:
            mode = "ai"
        elif part == _TK_AE:
            mode = "template"
        else:
            content = part.strip("\n")
            if not content:
                continue
            safe = _html.escape(content).replace("\n", "<br>")
            if mode == "ai":
                html_blocks.append(
                    f"""<div style="position:relative;margin:6px 0;padding:12px 16px 12px 14px;
background:#eef2ff;border-left:4px solid #6366f1;border-radius:0 8px 8px 0;">
  <span style="position:absolute;top:-10px;left:8px;background:#c7d2fe;color:#4338ca;
    font-size:0.62rem;font-weight:900;padding:2px 8px;border-radius:4px;">
    AI가 스캔본을 바탕으로 작성한 내용 (검토 필수)
  </span>
  <span style="font-size:0.82rem;color:#312e81;line-height:1.8;font-family:monospace;">{safe}</span>
</div>"""
                )
            else:
                html_blocks.append(
                    f"""<div style="padding:2px 0;font-size:0.82rem;color:#1e293b;
line-height:1.8;font-family:monospace;white-space:pre-wrap;">{safe}</div>"""
                )

    if html_blocks:
        st.markdown(
            f"""<div style="background:#f8fafc;border:1.5px solid #cbd5e1;border-radius:10px;
padding:16px 18px;margin:8px 0;">{''.join(html_blocks)}</div>""",
            unsafe_allow_html=True,
        )


def _run_mock_legal_ner(files: list, doc_subtype: str) -> dict:
    """Mock Legal NER — 문서 유형에 따라 결과 반환."""
    import random
    _map = {
        "소장·답변서":       _MOCK_LEGAL_NER[0],
        "행정처분·거절통보": _MOCK_LEGAL_NER[1],
        "판결문":            _MOCK_LEGAL_NER[2],
        "내용증명":          _MOCK_LEGAL_NER[0],
        "준비서면":          _MOCK_LEGAL_NER[2],
        "조정조서":          _MOCK_LEGAL_NER[1],
    }
    result = _map.get(doc_subtype, random.choice(_MOCK_LEGAL_NER))
    return {**result, "file_count": len(files) if files else 0, "doc_subtype": doc_subtype}


# ─────────────────────────────────────────────────────────────
# [수칙 6] Mock 시연 배너 HTML
# ─────────────────────────────────────────────────────────────
_MOCK_DEMO_BANNER = """
<div style="background:#fefce8;border:2px solid #fde047;border-radius:10px;
  padding:10px 16px;margin-bottom:10px;display:flex;align-items:flex-start;gap:10px;">
  <span style="font-size:1.1rem;flex-shrink:0;">🧪</span>
  <div>
    <div style="font-size:0.8rem;font-weight:900;color:#713f12;">
      [시연(Demo) 데이터] — 이 분석 결과는 실제 문서가 아닙니다
    </div>
    <div style="font-size:0.72rem;color:#92400e;margin-top:2px;line-height:1.6;">
      현재 화면은 AI 시뮬레이션 샘플입니다. 실제 문서를 업로드하면 해당 내용으로 교체됩니다.
      사건번호·당사자명·금액 등은 모두 가상의 예시이며 법적 효력이 없습니다.
    </div>
  </div>
</div>"""

# ─────────────────────────────────────────────────────────────
# [메인] 법률 SmartScanner UI
# ─────────────────────────────────────────────────────────────
_LEGAL_DISCLAIMER = """⚖️ 법적 고지 (필독): 본 AI 분석 리포트 및 답변서·내용증명 초안은 \
참고용 보조 자료이며, 변호사법 제109조에 의거하여 유상 법률 대리 및 법률 감정을 \
수행하지 않습니다. 실제 문서 제출로 인한 모든 법적 책임은 사용자에게 있으며, \
제출 전 반드시 변호사·손해사정인(독립사정인 포함)의 검토를 받으시기 바랍니다."""

_LEGAL_DOC_TYPES = [
    "소장·답변서",
    "판결문",
    "행정처분·거절통보",
    "내용증명",
    "준비서면",
    "조정조서",
]


def render_legal_scanner(
    session_key: str = "legal_scanner_result",
    uploader_key: str = "legal_scanner_files",
    show_result_inline: bool = True,
):
    """
    법률·행정 SmartScanner 컴포넌트 (Navy 테마).

    Parameters
    ----------
    session_key       : 결과를 저장할 session_state 키
    uploader_key      : file_uploader 위젯 키
    show_result_inline: True면 스캔 완료 후 같은 화면에 리포트 표시
    """
    # ── Print CSS 주입 (의료 스캐너와 공유) ───────────────────
    components.html(_PRINT_CSS, height=0)

    # ── 법적 면책 조항 (최상단 고정) ──────────────────────────
    st.markdown(f"""
<div style="background:#fef2f2;border:1.5px solid #fca5a5;border-radius:10px;
  padding:10px 16px;margin-bottom:12px;display:flex;align-items:flex-start;gap:10px;">
  <span style="font-size:1.1rem;flex-shrink:0;">⚠️</span>
  <span style="font-size:0.76rem;color:#7f1d1d;line-height:1.7;font-weight:600;">
    {_LEGAL_DISCLAIMER}
  </span>
</div>""", unsafe_allow_html=True)

    # ── 헤더 (Navy 테마) ───────────────────────────────────────
    st.markdown("""
<div style="background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);
  border-radius:12px;padding:12px 18px 10px;margin-bottom:12px;">
  <div style="color:#fff;font-size:1rem;font-weight:900;letter-spacing:0.04em;">
    ⚖️ LegalScanner — AI 법률·행정 문서 분석
  </div>
  <div style="color:#bfdbfe;font-size:0.74rem;margin-top:3px;">
    판결문·소장·행정처분서를 업로드하면 사건번호 자동 추출 → 평어 번역 → 답변서 초안 생성
  </div>
</div>""", unsafe_allow_html=True)

    # ── 문서 유형 선택 ─────────────────────────────────────────
    _dtype = st.radio(
        "법률 문서 유형",
        _LEGAL_DOC_TYPES,
        horizontal=True,
        key=f"{uploader_key}_ltype",
    )

    # ── 파일 업로더 ────────────────────────────────────────────
    _files = st.file_uploader(
        "📎 파일 첨부 (PDF / JPG / PNG — 복수 업로드 가능)",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=uploader_key,
    )

    # ── 스캔 실행 버튼 ─────────────────────────────────────────
    _btn_col, _info_col = st.columns([2, 1])
    with _btn_col:
        _do_scan = st.button(
            "⚖️ AI 법률 문서 분석 시작",
            key=f"{uploader_key}_run",
            use_container_width=True,
            type="primary",
            disabled=not _files,
        )
    with _info_col:
        st.caption("📌 PDF·스캔 이미지 모두 지원\nGemini Vision 연동 예정")

    # ── 스캔 실행 로직 ─────────────────────────────────────────
    if _do_scan and _files:
        with st.spinner("⚖️ 법률 문서를 판독 중입니다... (Legal NER 분석)"):
            time.sleep(2)
            _result = _run_mock_legal_ner(_files, _dtype)

        st.session_state[session_key] = _result
        st.session_state["legal_scan_ready"] = True
        st.success(
            f"✅ 판독 완료 — **{_result['doc_type']}** "
            f"(사건번호: `{_result['case_number']}`)"
        )
        st.rerun()

    # ── 인라인 리포트 출력 ─────────────────────────────────────
    if show_result_inline and st.session_state.get("legal_scan_ready"):
        _result = st.session_state.get(session_key)
        if _result:
            render_legal_report(_result)


# ─────────────────────────────────────────────────────────────
# [서브] 법률 분석 리포트 렌더러 (Navy 테마)
# ─────────────────────────────────────────────────────────────
def render_legal_report(result: dict):
    """
    법률 분석 결과를 A4 리포트 형식으로 렌더링.
    - 1단계: Legal NER 추출 정보 표시
    - 2단계: 평어 번역 (easy_summary)
    - 3단계: 답변서 / 내용증명 초안 생성 버튼
    """
    if not result:
        return

    doc_type    = result.get("doc_type",      "-")
    case_num    = result.get("case_number",   "-")
    court       = result.get("court",         "-")
    plaintiff   = result.get("plaintiff",     "-")
    defendant   = result.get("defendant",     "-")
    amount      = result.get("claim_amount",  0)
    summary     = result.get("claim_summary", "-")
    easy        = result.get("easy_summary",  "-")
    legal_basis_raw = result.get("legal_basis", "-")
    verdict     = result.get("verdict",       None)
    fcnt        = result.get("file_count",    0)
    confidence  = result.get("confidence",    72)
    source_rule = result.get("source_rule",   "원본 기재 없음")
    is_mock     = result.get("file_count", 0) == 0 or True  # Mock 결과 항상 True

    # [수칙 1] 법조문 형식 검증
    legal_basis, _law_status = _validate_legal_basis(legal_basis_raw)
    _law_border  = "#7dd3fc" if _law_status == "verified" else "#fca5a5"
    _law_color   = "#0369a1" if _law_status == "verified" else "#9a3412"
    _law_badge   = "✅ 형식 검증됨" if _law_status == "verified" else "⚠️ 형식 미검증 — 원본 확인 필요"

    # [수칙 5] Confidence Score 스타일
    _cs = _confidence_style(confidence)
    _conf_low_html = (
        '<div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:8px;'
        'padding:8px 14px;margin-bottom:10px;font-size:0.78rem;font-weight:700;color:#7f1d1d;">'
        "⚠️ 신뢰도가 낮아 분석 결과의 오류 가능성이 높습니다. 원본 문서를 반드시 직접 확인하십시오.</div>"
        if confidence < 70 else ""
    )

    # ── 출력 버튼 (우측 상단) ──────────────────────────────────
    _hdr_l, _hdr_r = st.columns([4, 1])
    with _hdr_l:
        st.markdown("""
<div style="font-size:1rem;font-weight:900;color:#1e3a5f;
  border-left:4px solid #2563eb;padding-left:10px;margin:8px 0;">
  ⚖️ AI 법률 문서 분석 리포트
</div>""", unsafe_allow_html=True)
    with _hdr_r:
        components.html("""
<button onclick="window.print()"
  style="width:100%;padding:8px 12px;background:#1e3a5f;color:#fff;
  border:none;border-radius:8px;font-weight:900;font-size:0.82rem;
  cursor:pointer;white-space:nowrap;">
  🖨️ 출력
</button>""", height=44)

    # [수칙 6] Mock 시연 배너
    if is_mock:
        st.markdown(_MOCK_DEMO_BANNER, unsafe_allow_html=True)

    # ── 리포트 본체 ────────────────────────────────────────────
    # 판결 결과 뱃지 색상
    _verdict_color = "#166534" if verdict and "승소" in verdict else "#7f1d1d" if verdict else "#1e3a5f"
    _verdict_bg    = "#f0fdf4" if verdict and "승소" in verdict else "#fef2f2" if verdict else "#eff6ff"

    # [수칙 5] Confidence Score 블록
    st.markdown(f"""
<div style="background:{_cs['bg']};border:2px solid {_cs['border']};border-radius:12px;
  padding:12px 18px;margin-bottom:12px;display:flex;align-items:center;
  justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-size:1.2rem;">🛡️</span>
    <div>
      <div style="font-size:0.75rem;font-weight:700;color:{_cs['text']};">AI 판독 신뢰도</div>
      <div style="font-size:0.70rem;color:{_cs['text']};margin-top:1px;">산출 근거: {source_rule}</div>
    </div>
  </div>
  <div style="font-size:2rem;font-weight:900;color:{_cs['text']};">{confidence}%</div>
</div>
{_conf_low_html}
""", unsafe_allow_html=True)

    st.markdown(f"""
<div id="gk-print-report">
<div class="gk-report-card" style="background:#fff;border:1.5px solid #e2e8f0;
  border-radius:14px;padding:20px 24px;margin-bottom:12px;
  box-shadow:0 2px 12px rgba(0,0,0,0.07);">

  <!-- 헤더: 문서종류 + 파일수 -->
  <div style="display:flex;align-items:center;justify-content:space-between;
    border-bottom:2px solid #e2e8f0;padding-bottom:12px;margin-bottom:16px;">
    <div>
      <div style="font-size:0.70rem;font-weight:700;color:#94a3b8;letter-spacing:0.08em;">문서 종류</div>
      <div style="font-size:1.3rem;font-weight:900;color:#1e3a5f;">{doc_type}</div>
    </div>
    <div style="background:{_verdict_bg};border:1px solid #c7d2fe;border-radius:8px;
      padding:6px 14px;font-size:0.78rem;font-weight:900;color:{_verdict_color};">
      {"⚖️ " + verdict if verdict else f"📂 {fcnt}개 파일 분석 완료"}
    </div>
  </div>

  <!-- 2열: 사건번호 + 청구금액 -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">
    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;">
      <div style="font-size:0.70rem;font-weight:700;color:#94a3b8;margin-bottom:4px;">사건번호 · 법원</div>
      <div style="font-size:0.88rem;font-weight:900;color:#1e293b;">{case_num}</div>
      <div style="font-size:0.76rem;color:#64748b;margin-top:2px;">{court}</div>
    </div>
    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;">
      <div style="font-size:0.70rem;font-weight:700;color:#94a3b8;margin-bottom:4px;">청구 금액 (AI 추정치)</div>
      <div style="font-size:1.3rem;font-weight:900;color:#1e3a5f;">{amount:,}원</div>
      <div style="font-size:0.68rem;color:#64748b;margin-top:2px;">* 실제 지급액과 다를 수 있습니다</div>
    </div>
  </div>

  <!-- 2열: 원고 / 피고 -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px;">
    <div style="border:1px solid #fecaca;background:#fff5f5;border-radius:10px;padding:10px 14px;">
      <div style="font-size:0.70rem;font-weight:700;color:#94a3b8;margin-bottom:4px;">원고 (청구인)</div>
      <div style="font-size:0.85rem;font-weight:900;color:#7f1d1d;">{plaintiff}</div>
    </div>
    <div style="border:1px solid #bfdbfe;background:#eff6ff;border-radius:10px;padding:10px 14px;">
      <div style="font-size:0.70rem;font-weight:700;color:#94a3b8;margin-bottom:4px;">피고 (응소인)</div>
      <div style="font-size:0.85rem;font-weight:900;color:#1e3a5f;">{defendant}</div>
    </div>
  </div>

  <!-- 청구 원인 요약 -->
  <div style="background:#f8faff;border:1px solid #c7d2fe;border-radius:10px;
    padding:12px 16px;margin-bottom:12px;">
    <div style="font-size:0.70rem;font-weight:700;color:#4f46e5;margin-bottom:6px;">
      📋 청구 원인 요약 (원문)
    </div>
    <div style="font-size:0.82rem;color:#1e293b;line-height:1.75;font-weight:500;">{summary}</div>
  </div>

  <!-- [수칙 1] 적용 법조 + 형식 검증 결과 -->
  <div style="background:#f0f9ff;border:1px solid {_law_border};border-radius:10px;
    padding:10px 16px;margin-bottom:12px;">
    <div style="font-size:0.70rem;font-weight:700;color:{_law_color};margin-bottom:4px;">
      📜 적용 법조 {_law_badge}
    </div>
    <div style="font-size:0.82rem;color:#0c4a6e;font-weight:700;">{legal_basis}</div>
  </div>

  <!-- 평어 번역 (핵심) -->
  <div style="background:#eef2ff;border:2px solid #6366f1;border-radius:12px;
    padding:14px 18px;margin-bottom:10px;">
    <div style="font-size:0.76rem;font-weight:900;color:#4338ca;margin-bottom:8px;">
      💡 AI 핵심 요약 — 쉬운 우리말 번역
    </div>
    <div style="font-size:0.9rem;color:#1e293b;line-height:1.8;font-weight:600;">
      {easy}
    </div>
  </div>

  <!-- [수칙 3] 법적 기한 강제 경고 -->
  <div style="background:#fff7ed;border:1.5px solid #fdba74;border-radius:10px;
    padding:12px 16px;margin-bottom:12px;display:flex;align-items:flex-start;gap:10px;">
    <span style="font-size:1.1rem;flex-shrink:0;">⏰</span>
    <div style="font-size:0.76rem;color:#9a3412;line-height:1.75;font-weight:600;">
      <b>[치명적 기한 경고]</b> AI는 소송 답변서 제출 기한·강제집행 신청 기한 등
      법적 효력을 갖는 날짜를 보장하지 않습니다. 오판 시 <b>무변론 패소·권리 소멸</b>의
      위험이 있습니다. 반드시 <b>대법원 나의사건검색(ecfs.scourt.go.kr)</b> 및
      송달받은 법원 서류를 직접 확인하십시오.
    </div>
  </div>

  <div style="margin-top:8px;font-size:0.67rem;color:#94a3b8;text-align:right;">
    * 본 리포트는 AI 추정치이며 법적 효력이 없습니다. 반드시 전문가 검토 후 활용하세요.
  </div>
</div>
</div>
""", unsafe_allow_html=True)

    # ── 3단계: 초안 생성 버튼 ──────────────────────────────────
    st.markdown("---")
    _d1, _d2, _d3 = st.columns([1, 1, 1])

    with _d1:
        if st.button(
            "📝 법원 제출용 답변서 초안 생성",
            key="legal_draft_answer_btn",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["legal_show_answer"] = not st.session_state.get("legal_show_answer", False)
            st.session_state["legal_show_complaint"] = False

    with _d2:
        if st.button(
            "📮 내용증명 초안 생성",
            key="legal_draft_complaint_btn",
            use_container_width=True,
        ):
            st.session_state["legal_show_complaint"] = not st.session_state.get("legal_show_complaint", False)
            st.session_state["legal_show_answer"] = False

    with _d3:
        if st.button("🔄 새 문서 재스캔", key="legal_scan_reset_btn", use_container_width=True):
            st.session_state["legal_scan_ready"] = False
            st.session_state.pop("legal_scanner_result", None)
            st.session_state["legal_show_answer"]    = False
            st.session_state["legal_show_complaint"] = False
            st.rerun()

    # ── [수칙 4] 답변서 초안 — 템플릿/AI생성 시각 분리 ─────────
    if st.session_state.get("legal_show_answer"):
        _draft_raw = _generate_answer_draft(result)
        st.markdown("""
<div style="background:#1e3a5f;border-radius:10px;padding:8px 16px;margin:10px 0 4px;">
  <span style="color:#bfdbfe;font-size:0.85rem;font-weight:900;">
    📝 [초안] 답변서 — 법원 제출용 표준 양식
  </span>
</div>""", unsafe_allow_html=True)

        # 템플릿/AI생성 영역 시각 분리 렌더링
        _render_draft_with_highlights(_draft_raw)

        # 편집용 텍스트 영역 (태그 제거된 plain text)
        _plain = _strip_draft_tags(_draft_raw)
        _edited = st.text_area(
            "✏️ 아래에서 수정 후 복사하세요 (태그 자동 제거됨)",
            value=_plain,
            height=380,
            key="legal_answer_textarea",
        )
        _safe_copy = _plain.replace('`', '\\`').replace('${', '\\${').replace('\\', '\\\\')
        components.html(f"""
<button onclick="navigator.clipboard.writeText(`{_safe_copy}`)
  .then(()=>this.innerText='✅ 복사 완료!').catch(()=>this.innerText='❌ 복사 실패')"
  style="width:100%;padding:10px;background:#1e3a5f;color:#fff;border:none;
  border-radius:8px;font-weight:900;font-size:0.88rem;cursor:pointer;margin-top:4px;">
  📋 클립보드에 복사하기
</button>""", height=46)
        st.warning("⚠️ 파란 박스(AI 작성) 부분은 실제 사실관계로 반드시 교체하세요. 제출 전 변호사·손해사정인 검토 필수.")

    # ── [수칙 4] 내용증명 초안 — 템플릿/AI생성 시각 분리 ────────
    if st.session_state.get("legal_show_complaint"):
        _comp_raw = _generate_complaint_draft(result)
        st.markdown("""
<div style="background:#1e3a5f;border-radius:10px;padding:8px 16px;margin:10px 0 4px;">
  <span style="color:#bfdbfe;font-size:0.85rem;font-weight:900;">
    📮 [초안] 내용증명 — 보험사 발송용
  </span>
</div>""", unsafe_allow_html=True)

        _render_draft_with_highlights(_comp_raw)

        _plain_comp = _strip_draft_tags(_comp_raw)
        _edited_comp = st.text_area(
            "✏️ 아래에서 수정 후 복사하세요 (태그 자동 제거됨)",
            value=_plain_comp,
            height=340,
            key="legal_complaint_textarea",
        )
        _safe_copy_comp = _plain_comp.replace('`', '\\`').replace('${', '\\${').replace('\\', '\\\\')
        components.html(f"""
<button onclick="navigator.clipboard.writeText(`{_safe_copy_comp}`)
  .then(()=>this.innerText='✅ 복사 완료!').catch(()=>this.innerText='❌ 복사 실패')"
  style="width:100%;padding:10px;background:#1e3a5f;color:#fff;border:none;
  border-radius:8px;font-weight:900;font-size:0.88rem;cursor:pointer;margin-top:4px;">
  📋 클립보드에 복사하기
</button>""", height=46)
        st.warning("⚠️ 파란 박스(AI 작성) 부분은 실제 사실관계로 반드시 교체하세요. 발송 전 전문가 검토 필수.")
