# ==========================================================
# [response_handler] 전역 AI 출력 프로토콜 — 중앙화 모듈
# 가이딩 프로토콜 전역 출력 표준 (3단계 형식: 정의 → 적용 → 예시)
# ==========================================================
# 사용처:
#   - show_result()        : 메인 AI 분석 결과 렌더링
#   - ins_bot 렌더링       : InsuBot 탭 AI 답변 후처리
#   - home 스캔 피드       : 스캔 결과 요약 출력
# ==========================================================

import re
import streamlit as st

# ── 3단계 출력 구조 태그 ────────────────────────────────────────
STAGE_TAGS = {
    "definition": ("📘 정의", "#0f4c81"),
    "application": ("🔧 적용", "#1565c0"),
    "example": ("💡 예시", "#0369a1"),
}

# ── 안전망 키워드 기본값 ────────────────────────────────────────
_DEFAULT_SAFETY_KW = "확인 불가,알 수 없,정보 없,불확실"

# ── 면책 고지 텍스트 ─────────────────────────────────────────────
DISCLAIMER_TEXT = (
    "\n\n---\n"
    "**[면책 고지]** 본 분석 결과는 AI 보조 도구에 의한 참고용 자료이며, "
    "최종 판단 및 법적 책임은 사용자(상담원)에게 귀속됩니다. "
    "보험금 지급 여부의 최종 결정은 보험사 심사 및 관련 법령에 따르며, "
    "법률·세무·의료 분야의 최종 판단은 반드시 해당 전문가와 확인하십시오.\n\n"
    "**문의:** insusite@gmail.com | 010-3074-2616 goldkey_Ai_masters2026"
)


# ══════════════════════════════════════════════════════════════
# [RH-1] enforce_3stage_format
# 3단계 구조(정의→적용→예시)가 없는 AI 출력에 섹션 헤더를 자동 삽입
# ══════════════════════════════════════════════════════════════
def enforce_3stage_format(text: str) -> str:
    """
    AI 출력 텍스트에 3단계 구조(정의/적용/예시)가 이미 포함되어 있으면 원문 반환.
    없으면 텍스트를 단락 단위로 분할하여 3단계 헤더를 자동 삽입하여 반환.
    """
    if not text or not text.strip():
        return text

    _stage_markers = [
        "정의", "definition", "📘",
        "적용", "application", "🔧",
        "예시", "example", "💡",
    ]
    _text_lower = text.lower()
    _has_stages = sum(1 for m in _stage_markers if m in _text_lower or m in text)

    # 이미 2개 이상 단계 마커가 있으면 원문 유지
    if _has_stages >= 2:
        return text

    # 단락 분할 (빈 줄 기준)
    _paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    if len(_paragraphs) == 0:
        return text
    elif len(_paragraphs) == 1:
        # 단락이 1개면 정의 헤더만 삽입
        return f"### 📘 정의\n{_paragraphs[0]}"
    elif len(_paragraphs) == 2:
        return (
            f"### 📘 정의\n{_paragraphs[0]}\n\n"
            f"### 🔧 적용\n{_paragraphs[1]}"
        )
    else:
        # 3개 이상: 앞 1개 → 정의, 마지막 1개 → 예시, 나머지 → 적용
        _def   = _paragraphs[0]
        _app   = "\n\n".join(_paragraphs[1:-1])
        _ex    = _paragraphs[-1]
        return (
            f"### 📘 정의\n{_def}\n\n"
            f"### 🔧 적용\n{_app}\n\n"
            f"### 💡 예시\n{_ex}"
        )


# ══════════════════════════════════════════════════════════════
# [RH-2] extract_summary_line
# AI 출력 텍스트에서 핵심 결론 한 줄 요약 추출
# ══════════════════════════════════════════════════════════════
def extract_summary_line(text: str, max_len: int = 80) -> str:
    """
    텍스트에서 ★/✅/💡/🔑/핵심/결론/요약 패턴의 첫 줄을 추출.
    없으면 첫 비빈 줄에서 max_len 자 추출.
    """
    if not text:
        return ""

    for _ln in text.splitlines():
        _ln_s = _ln.strip()
        if not _ln_s:
            continue
        if any(tok in _ln_s for tok in ["★", "✅", "💡", "🔑", "핵심", "결론", "요약"]):
            return re.sub(r"\*+", "", _ln_s).strip(" #>-·")

    for _ln in text.splitlines():
        _ln_s = re.sub(r"[#*_>`\-]", "", _ln).strip()
        if len(_ln_s) > 20:
            return _ln_s[:max_len] + ("…" if len(_ln_s) > max_len else "")

    return ""


# ══════════════════════════════════════════════════════════════
# [RH-3] check_safety_keywords
# 불확실 키워드 감지 → 오렌지 경고 HTML 반환
# ══════════════════════════════════════════════════════════════
def check_safety_keywords(text: str, kw_str: str = "") -> list:
    """
    텍스트에서 안전망 키워드를 감지하여 히트 목록 반환.
    kw_str이 비어 있으면 세션 상태 또는 기본값 사용.
    """
    if not kw_str:
        kw_str = st.session_state.get("_bucket_safety_kw", _DEFAULT_SAFETY_KW)
    kw_list = [k.strip() for k in kw_str.split(",") if k.strip()]
    return [k for k in kw_list if k in (text or "")]


def render_safety_warning(hits: list) -> None:
    """안전망 키워드 히트 목록을 오렌지 경고 박스로 렌더링."""
    if not hits:
        return
    st.markdown(
        f'<div style="background:#fff3cd;border:2px solid #fb923c;border-radius:10px;'
        f'padding:10px 16px;margin-bottom:8px;">'
        f'<span style="font-size:1.2rem;">⚠️</span>'
        f' <b style="color:#c2410c;">불확실 정보 감지</b>'
        f' — <code>{", ".join(hits)}</code><br>'
        f'<span style="font-size:0.78rem;color:#555;">'
        f'이 답변에는 불확실한 내용이 포함될 수 있습니다. '
        f'반드시 원본 약관 또는 전문가에게 확인하세요.</span></div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# [RH-4] render_ai_summary_badge
# AI 핵심 결론 요약 배지 렌더링
# ══════════════════════════════════════════════════════════════
def render_ai_summary_badge(summary_line: str) -> None:
    """핵심 결론 한 줄 요약을 파스텔 블루 배지로 렌더링."""
    if not summary_line:
        return
    st.markdown(
        f'<div class="gk-ai-summary">'
        f'<span class="gk-summary-label">AI 핵심 결론</span>'
        f'{summary_line}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# [RH-5] render_stage_tabs
# 3단계 구조가 포함된 텍스트를 탭 형식으로 렌더링 (선택적 사용)
# ══════════════════════════════════════════════════════════════
def render_stage_tabs(text: str) -> None:
    """
    3단계 구조 텍스트를 Streamlit 탭으로 분리 렌더링.
    정의/적용/예시 섹션이 있는 경우에만 탭 분리, 없으면 단일 st.markdown 출력.
    """
    _section_pattern = re.compile(
        r"###?\s*(?:📘\s*)?정의\s*\n(.*?)"
        r"(?=###?\s*(?:🔧\s*)?적용|$)",
        re.DOTALL,
    )
    _app_pattern = re.compile(
        r"###?\s*(?:🔧\s*)?적용\s*\n(.*?)"
        r"(?=###?\s*(?:💡\s*)?예시|$)",
        re.DOTALL,
    )
    _ex_pattern = re.compile(
        r"###?\s*(?:💡\s*)?예시\s*\n(.*?)$",
        re.DOTALL,
    )

    _def_match = _section_pattern.search(text)
    _app_match = _app_pattern.search(text)
    _ex_match  = _ex_pattern.search(text)

    if _def_match and (_app_match or _ex_match):
        _tabs = st.tabs(["📘 정의", "🔧 적용", "💡 예시"])
        with _tabs[0]:
            st.markdown(_def_match.group(1).strip() if _def_match else "—")
        with _tabs[1]:
            st.markdown(_app_match.group(1).strip() if _app_match else "—")
        with _tabs[2]:
            st.markdown(_ex_match.group(1).strip() if _ex_match else "—")
    else:
        st.markdown(text)


# ══════════════════════════════════════════════════════════════
# [RH-6] render_standard_output
# 표준화된 AI 출력 렌더링 (show_result의 핵심 로직 래핑)
# 모든 탭에서 일관된 출력 형식을 보장하는 단일 진입점
# ══════════════════════════════════════════════════════════════
def render_standard_output(
    text: str,
    enforce_stages: bool = True,
    show_summary: bool = True,
    show_safety: bool = True,
    use_tabs: bool = False,
) -> None:
    """
    AI 출력 텍스트를 표준 프로토콜에 따라 렌더링.

    Args:
        text          : AI 생성 텍스트
        enforce_stages: True이면 3단계 구조 자동 삽입
        show_summary  : True이면 핵심 결론 배지 표시
        show_safety   : True이면 불확실 키워드 경고 표시
        use_tabs      : True이면 3단계 구조를 탭으로 분리 렌더링
    """
    if not text or not text.strip():
        st.markdown(
            '<div class="gk-ai-output-box" '
            'style="display:flex;align-items:center;justify-content:center;">'
            '<div style="text-align:center;color:#90a4ae;font-size:0.88rem;line-height:2.0;">'
            '🤖 <strong style="color:#1565c0;">AI 분석 결과</strong>가 여기에 표시됩니다.<br>'
            '좌측에서 입력 후 <strong>분석 실행</strong> 버튼을 누르세요.'
            '</div></div>',
            unsafe_allow_html=True,
        )
        return

    # 3단계 형식 강제
    _out_text = enforce_3stage_format(text) if enforce_stages else text

    # 핵심 결론 배지
    if show_summary:
        _summary = extract_summary_line(_out_text)
        render_ai_summary_badge(_summary)

    # 안전망 경고
    if show_safety:
        _hits = check_safety_keywords(_out_text)
        render_safety_warning(_hits)

    # 본문 렌더링
    if use_tabs:
        render_stage_tabs(_out_text)
    else:
        st.markdown(_out_text)


# ══════════════════════════════════════════════════════════════
# [RH-7] format_scan_result_for_feed
# 스캔 결과를 메인 AI 분석 피드 표준 형식으로 변환
# ══════════════════════════════════════════════════════════════
def format_scan_result_for_feed(
    source_tab: str,
    items: list,
    metadata: dict = None,
) -> str:
    """
    스캔 결과 항목 리스트를 메인 AI 분석 피드용 마크다운 문자열로 변환.

    Args:
        source_tab: 스캔 출처 탭 이름 (예: "claim_scanner", "home_scan")
        items     : 항목 딕셔너리 리스트 (name, amount, hospital, date 등)
        metadata  : 추가 메타 정보 딕셔너리 (선택)

    Returns:
        str: 마크다운 형식의 피드 문자열
    """
    metadata = metadata or {}
    _tab_labels = {
        "claim_scanner": "🔬 청구 스캐너",
        "home_scan":     "📂 홈 스캔",
        "ocr":           "🔍 OCR 분석",
        "manual":        "✏️ 수동 입력",
    }
    _label = _tab_labels.get(source_tab, f"📋 {source_tab}")
    _hospital = metadata.get("hospital", "")
    _date     = metadata.get("date", "")

    _meta_row = ""
    if _hospital or _date:
        _meta_row = f"\n의료기관: {_hospital}  |  진료일: {_date}\n"

    _items_md = "\n".join(
        f"- **{it.get('name', '-')}**: {it.get('amount', 0):,}원"
        + (f"  [{it.get('hospital', '')}  {it.get('date', '')}]"
           if it.get("hospital") or it.get("date") else "")
        + ("  *(OCR 미인식 — 직접 입력 필요)*" if it.get("_ocr_broken") else "")
        for it in items
    )

    return (
        f"### 📘 정의\n"
        f"{_label} 스캔 결과 — {len(items)}건 항목 추출\n"
        f"{_meta_row}\n"
        f"### 🔧 적용\n"
        f"[항목 내역]\n{_items_md}\n\n"
        f"### 💡 예시\n"
        f"→ 항목을 확인하고 청구 계산을 진행하세요."
    )


# ══════════════════════════════════════════════════════════════
# [RH-8] apply_3stage_to_session
# 세션 상태의 AI 결과에 3단계 형식 적용 (인플레이스 업데이트)
# ══════════════════════════════════════════════════════════════
def apply_3stage_to_session(result_key: str) -> bool:
    """
    세션 상태의 result_key 값에 3단계 형식을 적용하고 업데이트.
    변경이 발생한 경우 True 반환, 변경 없으면 False 반환.
    """
    _text = st.session_state.get(result_key, "")
    if not _text:
        return False
    _formatted = enforce_3stage_format(_text)
    if _formatted != _text:
        st.session_state[result_key] = _formatted
        return True
    return False
