"""
compliance.py — Goldkey AI Masters 2026
Google Play Store / AI 가이드라인 컴플라이언스 방어 모듈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1] render_ai_disclaimer()          — 금융 AI 면책 고지 (고정 노출)
[2] render_feedback_button(key)     — AI 결과 오류 신고 모달 (AIGC 정책)
[3] render_permission_disclosure()  — 권한 요청 전 In-app Disclosure 모달
[4] check_permission_granted(ptype) — 권한 승인 세션 상태 조회
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
from __future__ import annotations
import datetime
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# 상수
# ══════════════════════════════════════════════════════════════════════════════

_DISCLAIMER_TEXT = (
    "※ 본 AI 분석 리포트 및 맞춤보장 브리핑은 2026년 기준 요율(7.19%)을 바탕으로 산출된 "
    "참고용 추정치입니다. 실제 보험 계약, 세무 판단 및 최종 재무 설계의 책임은 "
    "전적으로 담당 설계사에게 있습니다."
)

_PERMISSION_META: dict[str, dict] = {
    "microphone": {
        "icon": "🎤",
        "label": "마이크 접근 권한",
        "reason": (
            "음성 인식(STT) 기능을 사용하면 고객 상담 내용을 빠르게 기록하고 "
            "AI 분석에 활용할 수 있습니다. 마이크 권한은 음성 입력 버튼을 눌렀을 때만 "
            "활성화되며, 녹음 내용은 외부 서버로 전송되지 않습니다."
        ),
        "deny_msg": "마이크 권한을 허용하지 않으면 음성 입력 기능을 사용할 수 없습니다.",
    },
    "notification": {
        "icon": "🔔",
        "label": "알림 권한",
        "reason": (
            "보험 만기 알림, 상담 일정 리마인더, NBA 영업 제안 알림을 받으려면 "
            "알림 권한이 필요합니다. 앱이 백그라운드에 있을 때도 중요한 영업 기회를 "
            "놓치지 않도록 도와줍니다."
        ),
        "deny_msg": "알림 권한을 허용하지 않으면 만기·일정 푸시 알림을 받을 수 없습니다.",
    },
    "camera": {
        "icon": "📷",
        "label": "카메라 접근 권한",
        "reason": (
            "증권 사진 촬영 및 OCR 분석 기능을 사용하면 고객의 보험 증권을 "
            "즉시 스캔하여 보장 공백을 자동으로 분석할 수 있습니다. "
            "카메라는 스캔 버튼 실행 시에만 사용됩니다."
        ),
        "deny_msg": "카메라 권한을 허용하지 않으면 증권 스캔 OCR 기능을 사용할 수 없습니다.",
    },
    "calendar": {
        "icon": "📅",
        "label": "캘린더 접근 권한",
        "reason": (
            "기기 캘린더와 앱 일정을 동기화하면 고객 상담 일정이 자동으로 추가되고 "
            "리마인더가 설정됩니다. 캘린더 데이터는 로컬에서만 처리됩니다."
        ),
        "deny_msg": "캘린더 권한을 허용하지 않으면 일정 자동 동기화를 사용할 수 없습니다.",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# [1] 금융 AI 면책 고지 (Disclaimer)
# ══════════════════════════════════════════════════════════════════════════════

def render_ai_disclaimer(margin_top: int = 6) -> None:
    """
    Google Play Store 금융 AI 규제 — 필수 면책 고지 고정 노출.
    트리니티 결과 화면 하단 및 AI 브리핑 플레이어 하단에 사용.
    """
    st.markdown(
        f"<div style='margin-top:{margin_top}px;padding:6px 10px;"
        "background:#f8f9fa;border-left:3px solid #d1d5db;"
        "border-radius:0 4px 4px 0;'>"
        f"<span style='font-size:0.70rem;color:#6b7280;line-height:1.5;'>"
        f"{_DISCLAIMER_TEXT}</span></div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# [2] AI 결과 피드백 / 오류 신고 (Feedback Mechanism)
# ══════════════════════════════════════════════════════════════════════════════

def render_feedback_button(
    key: str = "fb_default",
    context: str = "",
    compact: bool = True,
) -> None:
    """
    Google AIGC 정책 필수 — AI 결과 오류 신고 버튼 + 인라인 모달.
    피드백은 session_state 로그 + Supabase (가능시) 저장.

    Args:
        key     : 위젯 중복 방지용 고유 키
        context : 신고 대상 AI 컨텐츠 식별자 (예: "morning_briefing", "nba_card")
        compact : True → 작은 링크형 버튼, False → 일반 버튼
    """
    fb_open_key  = f"_fb_open_{key}"
    fb_done_key  = f"_fb_done_{key}"

    # 신고 완료 후 확인 메시지
    if st.session_state.get(fb_done_key):
        st.caption("✅ 피드백이 접수되었습니다. 검토 후 개선에 반영하겠습니다.")
        return

    # 버튼 스타일
    if compact:
        st.markdown(
            f"<div style='text-align:right;margin-top:4px;'>"
            f"<span style='font-size:0.68rem;color:#94a3b8;cursor:pointer;'>"
            f"⚠️ AI 결과 피드백 / 오류 신고</span></div>",
            unsafe_allow_html=True,
        )
        _btn_label = "⚠️ AI 결과 피드백 / 오류 신고"
        _btn_clicked = st.button(
            _btn_label,
            key=f"_fb_btn_{key}",
            help="AI가 부정확하거나 부적절한 결과를 제공했을 때 신고하세요.",
            type="secondary",
        )
    else:
        _btn_clicked = st.button(
            "⚠️ AI 결과 피드백 / 오류 신고",
            key=f"_fb_btn_{key}",
            help="AI가 부정확하거나 부적절한 결과를 제공했을 때 신고하세요.",
            use_container_width=True,
        )

    if _btn_clicked:
        st.session_state[fb_open_key] = True

    # 인라인 신고 폼
    if st.session_state.get(fb_open_key):
        with st.container():
            st.markdown(
                "<div style='background:#fff7ed;border:1.5px solid #fed7aa;"
                "border-radius:10px;padding:14px 16px;margin-top:6px;'>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "**AI가 부정확하거나 부적절한 결과를 제공했습니까?**",
            )
            _fb_category = st.selectbox(
                "문제 유형",
                [
                    "수치/계산 오류",
                    "부적절한 언어 또는 표현",
                    "고객 정보 오인식",
                    "맥락에 맞지 않는 제안",
                    "기타",
                ],
                key=f"_fb_cat_{key}",
            )
            _fb_detail = st.text_area(
                "상세 내용 (선택)",
                placeholder="어떤 부분이 잘못되었는지 간략히 설명해 주세요.",
                height=80,
                key=f"_fb_detail_{key}",
            )
            _col1, _col2 = st.columns(2)
            with _col1:
                if st.button("📨 신고 제출", key=f"_fb_submit_{key}",
                             use_container_width=True, type="primary"):
                    _save_feedback(key, context, _fb_category, _fb_detail)
                    del st.session_state[fb_open_key]
                    st.session_state[fb_done_key] = True
                    st.rerun()
            with _col2:
                if st.button("취소", key=f"_fb_cancel_{key}",
                             use_container_width=True):
                    del st.session_state[fb_open_key]
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def _save_feedback(
    key: str,
    context: str,
    category: str,
    detail: str,
) -> None:
    """피드백을 session_state 로그에 추가하고 Supabase에 best-effort 저장."""
    record = {
        "ts":       datetime.datetime.utcnow().isoformat(),
        "agent_id": st.session_state.get("agent_id", ""),
        "context":  context or key,
        "category": category,
        "detail":   detail[:500] if detail else "",
    }
    # session_state 로컬 로그 (항상 저장)
    _log: list = st.session_state.setdefault("_ai_feedback_log", [])
    _log.append(record)

    # Supabase best-effort 저장
    try:
        from shared_components import get_env_secret
        from supabase import create_client
        _url = get_env_secret("SUPABASE_URL", "")
        _key = get_env_secret("SUPABASE_SERVICE_ROLE_KEY",
                              get_env_secret("SUPABASE_KEY", ""))
        if _url and _key:
            _sb = create_client(_url, _key)
            _sb.table("ai_feedback_log").insert(record).execute()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# [3] 권한 요청 In-app Disclosure 모달
# ══════════════════════════════════════════════════════════════════════════════

def check_permission_granted(permission_type: str) -> bool:
    """세션 기준 권한 승인 여부 반환."""
    return bool(st.session_state.get(f"_perm_granted_{permission_type}"))


def render_permission_disclosure(
    permission_type: str,
    on_grant_key: str = "",
) -> None:
    """
    시스템 권한 요청 전 In-app Disclosure 모달.
    Google Play 정책: 권한이 왜 필요한지 먼저 앱 내 UI로 설명한 뒤 요청.

    Args:
        permission_type : "microphone" | "notification" | "camera" | "calendar"
        on_grant_key    : 승인 시 session_state[on_grant_key] = True 설정할 키
    """
    meta = _PERMISSION_META.get(permission_type)
    if not meta:
        return

    granted_key = f"_perm_granted_{permission_type}"
    denied_key  = f"_perm_denied_{permission_type}"
    open_key    = f"_perm_open_{permission_type}"

    # 이미 결정된 경우 생략
    if st.session_state.get(granted_key) or st.session_state.get(denied_key):
        return

    st.session_state.setdefault(open_key, True)

    if not st.session_state.get(open_key):
        return

    st.markdown(
        "<div style='background:#eff6ff;border:2px solid #3b82f6;"
        "border-radius:12px;padding:18px 20px;margin:10px 0;'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"### {meta['icon']} {meta['label']} 안내",
    )
    st.info(meta["reason"])
    st.caption(meta["deny_msg"])

    _ga, _de = st.columns(2)
    with _ga:
        if st.button(
            f"✅ {meta['label']} 허용",
            key=f"_perm_allow_{permission_type}",
            use_container_width=True,
            type="primary",
        ):
            st.session_state[granted_key] = True
            st.session_state[open_key]    = False
            if on_grant_key:
                st.session_state[on_grant_key] = True
            st.rerun()
    with _de:
        if st.button(
            "거부",
            key=f"_perm_deny_{permission_type}",
            use_container_width=True,
        ):
            st.session_state[denied_key] = True
            st.session_state[open_key]   = False
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def request_permission_if_needed(
    permission_type: str,
    on_grant_key: str = "",
) -> bool:
    """
    권한이 필요한 액션 실행 직전 호출.
    - 이미 허용: True 반환 (즉시 실행 가능)
    - 미결정: In-app Disclosure 렌더링 후 False 반환 (다음 rerun에서 재시도)
    - 거부됨: st.warning + False 반환
    """
    granted_key = f"_perm_granted_{permission_type}"
    denied_key  = f"_perm_denied_{permission_type}"
    meta        = _PERMISSION_META.get(permission_type, {})

    if st.session_state.get(granted_key):
        return True
    if st.session_state.get(denied_key):
        st.warning(
            f"{meta.get('icon','⚠️')} {meta.get('deny_msg','권한이 거부되었습니다.')}"
        )
        return False
    render_permission_disclosure(permission_type, on_grant_key)
    return False


# ══════════════════════════════════════════════════════════════════════════════
# [4] 앱 기동 시 권한 상태 초기화 (app.py 최상단에서 1회 호출)
# ══════════════════════════════════════════════════════════════════════════════

def init_permission_state() -> None:
    """
    앱 기동 시 1회 — 권한 관련 session_state 기본값 초기화.
    각 권한은 세션 단위로 유지 (재기동 시 재요청).
    """
    for _ptype in _PERMISSION_META:
        st.session_state.setdefault(f"_perm_granted_{_ptype}", False)
        st.session_state.setdefault(f"_perm_denied_{_ptype}", False)
        st.session_state.setdefault(f"_perm_open_{_ptype}", False)
    st.session_state.setdefault("_ai_feedback_log", [])
