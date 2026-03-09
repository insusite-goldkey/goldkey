# ==========================================================================
# modules/kakao_stub.py — 카카오 알림톡 가상(Stub) 발송 모듈
# ==========================================================================
# [설계 원칙 — 가이딩 프로토콜 제240조]
#   - 실제 API 미연결 상태에서 전체 UI/UX 흐름을 완전하게 테스트 가능하도록 한다.
#   - 호출 시 발송 로그를 session_state에 기록하고 미리보기를 화면에 노출한다.
#   - API 키(밸브)만 꽂으면 즉시 실제 발송으로 전환되는 구조를 유지한다.
#   - kakao_sender.py 와 동일한 함수 시그니처를 사용하여 drop-in 교체 가능.
# ==========================================================================

from __future__ import annotations
import time
from datetime import datetime
from typing import Optional


# ==========================================================================
# [STUB CORE] 가상 발송 함수
# ==========================================================================

def send_report(
    phone: str,
    message: str,
    *,
    title: str = "골드키 AI 보험 상담 리포트",
    force_sms: bool = False,
    planner_info: Optional[dict] = None,
) -> dict:
    """
    [STUB] 카카오/SMS 가상 발송 — 실제 API 호출 없이 시뮬레이션만 수행.
    kakao_sender.send_report 와 동일한 시그니처 → API 키 등록 시 즉시 교체 가능.
    반환: {"success": True, "method": "stub", "msg": str, "preview": str}
    """
    _method = "SMS(stub)" if force_sms else "카카오(stub)"
    _ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # [GP200조] 브랜딩 푸터 미리보기 생성
    _footer = _build_stub_footer(planner_info)
    _full_msg = message + _footer if _footer else message

    # 발송 시뮬레이션 로그 저장
    _log_entry = {
        "ts": _ts,
        "method": _method,
        "phone": _mask_phone(phone),
        "title": title,
        "preview": _full_msg[:500],
    }
    _append_stub_log(_log_entry)

    return {
        "success": True,
        "method": "stub",
        "msg": f"[시뮬레이션] {_method} 전송 완료 → {_mask_phone(phone)} ({_ts})",
        "preview": _full_msg,
        "log": _log_entry,
    }


def send_kakao_alimtalk(
    phone: str,
    message: str,
    template_id: Optional[str] = None,
    *,
    title: str = "골드키 AI 보험 상담 리포트",
) -> dict:
    """[STUB] 카카오 알림톡 가상 발송."""
    return send_report(phone, message, title=title)


def send_sms(
    phone: str,
    message: str,
    *,
    sender: Optional[str] = None,
) -> dict:
    """[STUB] SMS 가상 발송."""
    return send_report(phone, message, force_sms=True)


# ==========================================================================
# [STUB UTIL]
# ==========================================================================

def _mask_phone(phone: str) -> str:
    """전화번호 가운데 4자리 마스킹: 010-1234-5678 → 010-****-5678"""
    import re
    digits = re.sub(r"[^0-9]", "", str(phone or ""))
    if len(digits) == 11:
        return f"{digits[:3]}-****-{digits[7:]}"
    return phone[:3] + "****" + phone[-2:] if len(phone) >= 5 else "***"


def _build_stub_footer(planner_info: Optional[dict]) -> str:
    """[GP200조] 브랜딩 푸터 텍스트 생성 (stub용)."""
    if not planner_info:
        return ""
    _co = (planner_info.get("company") or "").strip()
    _br = (planner_info.get("branch")  or "").strip()
    _nm = (planner_info.get("name")    or "").strip()
    _ct = (planner_info.get("contact") or "").strip()
    if not (_co or _nm):
        return ""
    _affil = " ".join(filter(None, [_co, _br]))
    _parts = [p for p in [_affil, f"{_nm} 설계사" if _nm else "", _ct] if p]
    return "\n\n[발송: " + " | ".join(_parts) + "] [STUB 시뮬레이션]"


def _append_stub_log(entry: dict) -> None:
    """session_state에 stub 발송 이력 저장 (최근 50건 유지)."""
    try:
        import streamlit as st
        _log = st.session_state.get("_kakao_stub_log", [])
        _log.append(entry)
        st.session_state["_kakao_stub_log"] = _log[-50:]
    except Exception:
        pass


# ==========================================================================
# [UI] Streamlit Stub 발송 UI 헬퍼
# ==========================================================================

def render_send_ui(
    report_text: str,
    session_key: str = "_stub_send",
    *,
    default_phone: str = "",
    title: str = "골드키 AI 보험 상담 리포트",
    compact: bool = False,
    planner_info: Optional[dict] = None,
) -> None:
    """
    [STUB] 카카오 알림톡 가상 발송 UI.
    kakao_sender.render_send_ui 와 동일한 시그니처 → API 키 등록 시 즉시 교체 가능.
    """
    try:
        import streamlit as st
    except ImportError:
        return

    # 이전 발송 결과 표시
    _prev = st.session_state.get(f"{session_key}_result")
    if _prev:
        st.success(
            f"✅ {_prev.get('msg', '')}",
            icon="📲",
        )

    def _inner():
        # ── 안내 배너 ────────────────────────────────────────────────
        st.markdown("""
<div style="background:linear-gradient(135deg,#FFF9E6,#FFF3CD);
  border-radius:10px;padding:12px 16px;margin-bottom:10px;
  border-left:4px solid #FFC107;">
  <div style="font-size:0.93rem;font-weight:900;color:#7B5E00;">
    📲 카카오 알림톡 / 문자 발송 <span style="font-size:0.72rem;
    background:#FFC107;color:#1a1a1a;border-radius:4px;
    padding:1px 6px;margin-left:6px;font-weight:700;">STUB 시뮬레이션</span>
  </div>
  <div style="font-size:0.74rem;color:#92650A;margin-top:3px;">
    API 키 미설정 상태 — 실제 발송 없이 전송 흐름을 미리 체험할 수 있습니다.
    키 등록 후 즉시 실발송으로 전환됩니다.
  </div>
</div>""", unsafe_allow_html=True)

        # ── 수신자 전화번호 ───────────────────────────────────────────
        _ph_key = f"{session_key}_phone"
        _phone = st.text_input(
            "📱 수신자 전화번호",
            value=st.session_state.get(_ph_key, default_phone),
            key=_ph_key,
            placeholder="010-1234-5678",
            help="STUB 모드: 실제 문자가 발송되지 않습니다.",
        )

        # ── 메시지 미리보기 ────────────────────────────────────────────
        _footer = _build_stub_footer(planner_info)
        _preview_text = (report_text or "") + (_footer if _footer else "")
        with st.expander("📄 전송될 메시지 미리보기", expanded=True):
            st.markdown(f"""
<div style="background:#FEE500;border-radius:12px;padding:14px 16px;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;
  font-size:0.82rem;line-height:1.75;color:#3C1E1E;
  white-space:pre-wrap;max-width:380px;
  box-shadow:0 2px 8px rgba(0,0,0,0.12);">
  <div style="font-size:0.9rem;font-weight:900;margin-bottom:6px;
    border-bottom:1px solid rgba(0,0,0,0.1);padding-bottom:6px;">
    💬 카카오톡 알림톡 미리보기
  </div>
  <div style="font-size:0.8rem;font-weight:700;color:#92400e;
    margin-bottom:6px;">{title}</div>
  {(_preview_text[:600] + ('…' if len(_preview_text) > 600 else '')).replace(chr(10), '<br>')}
</div>""", unsafe_allow_html=True)

        # ── 버튼 행 ──────────────────────────────────────────────────
        _c1, _c2, _c3 = st.columns(3)
        with _c1:
            _btn_kakao = st.button(
                "📲 카카오 전송(예약)",
                key=f"{session_key}_kakao",
                use_container_width=True,
                type="primary",
            )
        with _c2:
            _btn_sms = st.button(
                "💬 SMS 전송(예약)",
                key=f"{session_key}_sms",
                use_container_width=True,
            )
        with _c3:
            _btn_clear = st.button(
                "🗑️ 초기화",
                key=f"{session_key}_clear",
                use_container_width=True,
            )

        # ── 버튼 이벤트 처리 ─────────────────────────────────────────
        if _btn_kakao:
            if not _phone.strip():
                st.warning("전화번호를 입력하세요.")
            elif not report_text or not report_text.strip():
                st.warning("발송할 보고서가 없습니다. 먼저 AI 분석을 실행하세요.")
            else:
                with st.spinner("📲 카카오 알림톡 전송 시뮬레이션 중..."):
                    time.sleep(0.6)  # 실제 발송 느낌을 위한 딜레이
                    res = send_report(_phone, report_text, title=title,
                                      planner_info=planner_info)
                st.session_state[f"{session_key}_result"] = res
                st.rerun()

        if _btn_sms:
            if not _phone.strip():
                st.warning("전화번호를 입력하세요.")
            elif not report_text or not report_text.strip():
                st.warning("발송할 보고서가 없습니다. 먼저 AI 분석을 실행하세요.")
            else:
                with st.spinner("💬 SMS 전송 시뮬레이션 중..."):
                    time.sleep(0.4)
                    res = send_report(_phone, report_text, title=title,
                                      force_sms=True, planner_info=planner_info)
                st.session_state[f"{session_key}_result"] = res
                st.rerun()

        if _btn_clear:
            st.session_state.pop(f"{session_key}_result", None)
            st.rerun()

        # ── stub 로그 확인 ────────────────────────────────────────────
        _stub_logs = st.session_state.get("_kakao_stub_log", [])
        if _stub_logs:
            with st.expander(f"🗒️ 시뮬레이션 발송 이력 ({len(_stub_logs)}건)", expanded=False):
                for _entry in reversed(_stub_logs[-10:]):
                    st.markdown(
                        f"<div style='font-size:0.75rem;padding:4px 8px;"
                        f"background:#f8fafc;border-radius:6px;margin-bottom:3px;"
                        f"border-left:3px solid #FFC107;'>"
                        f"<b>{_entry.get('ts','')}</b> | {_entry.get('method','')} "
                        f"→ <code>{_entry.get('phone','')}</code> | "
                        f"{_entry.get('title','')}</div>",
                        unsafe_allow_html=True,
                    )

    if compact:
        import streamlit as st
        with st.expander("📲 카카오/SMS 전송(예약)", expanded=False):
            _inner()
    else:
        _inner()


# ==========================================================================
# [UTIL] Stub 모드 여부 확인
# ==========================================================================

def is_stub_mode() -> bool:
    """현재 Stub 모드 여부 반환 (API 키 미설정 시 True)."""
    import os
    try:
        import streamlit as st
        _kakao_key = st.secrets.get("KAKAO_API_KEY", "") or ""
    except Exception:
        _kakao_key = ""
    if not _kakao_key:
        _kakao_key = os.environ.get("KAKAO_API_KEY", "")
    return not bool(_kakao_key.strip())
