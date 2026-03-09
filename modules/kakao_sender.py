# ==========================================================================
# modules/kakao_sender.py — 카카오 알림톡 + SMS 폴백 발송 모듈
# ==========================================================================
# [설계 원칙]
#   - 카카오 알림톡(비즈메시지 API) 우선, 실패 시 SMS(솔라API/NHN) 폴백
#   - 환경변수/Secrets에서 키 로드 (하드코딩 금지)
#   - 발송 결과 로그를 session_state에 저장
#   - Streamlit UI 헬퍼 함수 포함 (_render_send_ui)
# ==========================================================================
# [관리자 필수 설정 환경변수]
#   KAKAO_API_KEY      — 카카오 비즈메시지 API 인증키 (또는 st.secrets["KAKAO_API_KEY"])
#   KAKAO_SENDER_KEY   — 발신 채널 키 (플러스친구 채널)
#   KAKAO_TEMPLATE_ID  — 알림톡 템플릿 코드 (사전 등록 필요)
#   SMS_API_KEY        — SMS 발송 API 키 (폴백용, 솔라API 또는 NHN)
#   SMS_API_SECRET     — SMS API Secret
#   SMS_SENDER_NUM     — 발신번호 (사전 등록된 번호)
# ==========================================================================

from __future__ import annotations
import os
import json
import time
import re
from typing import Optional

# ── 환경변수 / Secrets 읽기 헬퍼 ─────────────────────────────────────────
def _get_cfg(key: str, default: str = "") -> str:
    val = default
    try:
        import streamlit as st
        val = st.secrets.get(key, default) or default
    except Exception:
        pass
    if not val or val == default:
        val = os.environ.get(key, default)
    return str(val).strip()


# ── 전화번호 정규화 ─────────────────────────────────────────────────────
def _normalize_phone(phone: str) -> str:
    """010-1234-5678 → 01012345678"""
    return re.sub(r"[^0-9]", "", str(phone or ""))


# ==========================================================================
# [CORE 1] 카카오 알림톡 발송
# ==========================================================================
def send_kakao_alimtalk(
    phone: str,
    message: str,
    template_id: Optional[str] = None,
    *,
    title: str = "골드키 AI 보험 상담 리포트",
) -> dict:
    """
    카카오 비즈메시지 알림톡 발송.
    반환: {"success": bool, "method": "kakao", "msg": str, "code": str}
    """
    api_key     = _get_cfg("KAKAO_API_KEY")
    sender_key  = _get_cfg("KAKAO_SENDER_KEY")
    tmpl_id     = template_id or _get_cfg("KAKAO_TEMPLATE_ID", "goldkey_report_v1")
    phone_norm  = _normalize_phone(phone)

    if not api_key or not sender_key:
        return {
            "success": False, "method": "kakao",
            "msg": "카카오 API 키가 설정되지 않았습니다. 관리자에게 문의하세요.",
            "code": "NO_KEY",
        }
    if not phone_norm or len(phone_norm) < 10:
        return {
            "success": False, "method": "kakao",
            "msg": f"올바르지 않은 전화번호입니다: '{phone}'",
            "code": "BAD_PHONE",
        }

    # 메시지 길이 제한 (알림톡 최대 1000자)
    msg_trimmed = message[:990] + "…" if len(message) > 990 else message

    payload = {
        "senderKey": sender_key,
        "templateCode": tmpl_id,
        "recipientList": [
            {
                "recipientNo": phone_norm,
                "templateParameter": {
                    "title": title,
                    "content": msg_trimmed,
                },
            }
        ],
    }

    try:
        import urllib.request as _req
        import urllib.error  as _err

        data  = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        url   = "https://api-alimtalk.cloud.toast.com/alimtalk/v2.3/appkeys/{}/messages".format(api_key)
        req   = _req.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json;charset=UTF-8")

        with _req.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if body.get("header", {}).get("isSuccessful"):
                return {"success": True, "method": "kakao", "msg": "알림톡 발송 성공", "code": "OK"}
            else:
                return {
                    "success": False, "method": "kakao",
                    "msg": body.get("header", {}).get("resultMessage", "알림톡 발송 실패"),
                    "code": str(body.get("header", {}).get("resultCode", "ERR")),
                }
    except Exception as e:
        return {"success": False, "method": "kakao", "msg": f"알림톡 발송 오류: {e}", "code": "EXCEPTION"}


# ==========================================================================
# [CORE 2] SMS 발송 (폴백 — 솔라API 기반)
# ==========================================================================
def send_sms(
    phone: str,
    message: str,
    *,
    sender: Optional[str] = None,
) -> dict:
    """
    SMS 발송 (카카오 실패 시 폴백).
    반환: {"success": bool, "method": "sms", "msg": str, "code": str}
    """
    api_key    = _get_cfg("SMS_API_KEY")
    api_secret = _get_cfg("SMS_API_SECRET")
    sender_num = sender or _get_cfg("SMS_SENDER_NUM")
    phone_norm = _normalize_phone(phone)

    if not api_key or not api_secret:
        return {
            "success": False, "method": "sms",
            "msg": "SMS API 키가 설정되지 않았습니다. 관리자에게 문의하세요.",
            "code": "NO_KEY",
        }
    if not sender_num:
        return {
            "success": False, "method": "sms",
            "msg": "SMS 발신번호가 설정되지 않았습니다 (SMS_SENDER_NUM).",
            "code": "NO_SENDER",
        }
    if not phone_norm or len(phone_norm) < 10:
        return {
            "success": False, "method": "sms",
            "msg": f"올바르지 않은 전화번호입니다: '{phone}'",
            "code": "BAD_PHONE",
        }

    # SMS 90바이트 / LMS 2000바이트 자동 분기
    msg_type = "SMS" if len(message.encode("euc-kr", errors="ignore")) <= 90 else "LMS"
    msg_trimmed = message[:1900] if msg_type == "LMS" else message[:45]

    payload = {
        "type": msg_type,
        "from": _normalize_phone(sender_num),
        "to": phone_norm,
        "text": msg_trimmed,
    }

    try:
        import urllib.request as _req
        import base64 as _b64
        import hashlib as _hs
        import hmac as _hmac

        # 솔라API v2 HMAC-SHA256 서명
        _ts    = str(int(time.time() * 1000))
        _sign_msg = f"POST\n/messages\n{_ts}\n{api_key}"
        _sig   = _b64.b64encode(
            _hmac.new(api_secret.encode(), _sign_msg.encode(), _hs.sha256).digest()
        ).decode()

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        url  = "https://api.solapi.com/messages/v4/send"
        req  = _req.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json;charset=UTF-8")
        req.add_header("Authorization", f"HMAC-SHA256 apiKey={api_key}, date={_ts}, salt={_ts}, signature={_sig}")

        with _req.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if body.get("groupInfo", {}).get("count", {}).get("success", 0) > 0:
                return {"success": True, "method": "sms", "msg": f"{msg_type} 발송 성공", "code": "OK"}
            else:
                err = body.get("failedMessageList", [{}])
                err_msg = err[0].get("reason", "발송 실패") if err else "발송 실패"
                return {"success": False, "method": "sms", "msg": err_msg, "code": "FAIL"}
    except Exception as e:
        return {"success": False, "method": "sms", "msg": f"SMS 발송 오류: {e}", "code": "EXCEPTION"}


# ==========================================================================
# [GP200조] 플래너 브랜딩 푸터 텍스트 생성
# ==========================================================================
def _build_msg_footer(planner_info: Optional[dict]) -> str:
    """[GP200조] 카카오/SMS 메시지 하단에 삽입할 소속 브랜딩 텍스트."""
    if not planner_info:
        return ""
    _co = (planner_info.get("company") or "").strip()
    _br = (planner_info.get("branch") or "").strip()
    _nm = (planner_info.get("name") or "").strip()
    _ct = (planner_info.get("contact") or "").strip()
    if not (_co or _nm):
        return ""
    _affil = " ".join(filter(None, [_co, _br]))
    _parts = []
    if _affil:
        _parts.append(_affil)
    if _nm:
        _parts.append(f"{_nm} 설계사")
    if _ct:
        _parts.append(_ct)
    return "\n\n[발송: " + " | ".join(_parts) + "]"


# ==========================================================================
# [CORE 3] 통합 발송 (카카오 우선 → SMS 폴백)
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
    보고서 발송 통합 함수.
    - force_sms=False: 카카오 알림톡 시도 → 실패 시 SMS 폴백
    - force_sms=True:  SMS만 발송
    - planner_info: [GP200조] {"company", "branch", "name", "contact"} — 발송 브랜딩 푸터
    반환: {"success": bool, "method": str, "msg": str, "code": str}
    """
    # [GP200조] 메시지에 소속 브랜딩 푸터 자동 삽입
    _footer = _build_msg_footer(planner_info)
    _full_msg = message + _footer if _footer else message

    if not force_sms:
        result = send_kakao_alimtalk(phone, _full_msg, title=title)
        if result["success"]:
            return result
        # 카카오 실패 → SMS 폴백
        sms_result = send_sms(phone, _full_msg)
        if sms_result["success"]:
            sms_result["msg"] = f"카카오 실패({result['code']}) → SMS 폴백 성공"
            return sms_result
        return {
            "success": False,
            "method": "all_failed",
            "msg": f"카카오({result['code']}) + SMS({sms_result['code']}) 모두 실패. API 키 설정을 확인하세요.",
            "code": "ALL_FAILED",
        }
    else:
        return send_sms(phone, _full_msg)


# ==========================================================================
# [UI] Streamlit 발송 UI 헬퍼 — 각 섹터 보고서 하단에 삽입
# ==========================================================================
def render_send_ui(
    report_text: str,
    session_key: str = "_report_send",
    *,
    default_phone: str = "",
    title: str = "골드키 AI 보험 상담 리포트",
    compact: bool = False,
    planner_info: Optional[dict] = None,
) -> None:
    """
    섹터 보고서 하단에 카카오/SMS 발송 UI를 렌더링합니다.

    Args:
        report_text:  발송할 보고서 텍스트 (이미 생성된 결과)
        session_key:  session_state 저장 키 prefix
        default_phone: 기본 수신자 전화번호 (고객 정보에서 자동 주입 가능)
        title:        알림톡 제목 (템플릿 변수)
        compact:      True면 expander 안에 숨김 (기본 False — 직접 표시)
    """
    try:
        import streamlit as st
    except ImportError:
        return

    # ── 이전 발송 결과 표시 ────────────────────────────────────────────
    _prev = st.session_state.get(f"{session_key}_result")
    if _prev:
        if _prev.get("success"):
            st.success(f"✅ 발송 완료 [{_prev.get('method','').upper()}] — {_prev.get('msg','')}")
        else:
            st.error(f"❌ 발송 실패 [{_prev.get('method','').upper()}] — {_prev.get('msg','')}")

    def _inner():
        st.markdown("""
<div style="background:linear-gradient(135deg,#fff7e6,#fef3c7);
  border-radius:10px;padding:12px 16px;margin-bottom:10px;
  border-left:4px solid #f59e0b;">
  <div style="font-size:0.95rem;font-weight:900;color:#92400e;">
    📲 카카오 알림톡 / 문자 발송
  </div>
  <div style="font-size:0.75rem;color:#78350f;margin-top:3px;">
    분석 리포트를 고객에게 즉시 전송합니다 — 카카오 알림톡 우선, 실패 시 SMS 자동 전환
  </div>
</div>""", unsafe_allow_html=True)

        _ph_key = f"{session_key}_phone"
        _phone = st.text_input(
            "📱 수신자 전화번호",
            value=st.session_state.get(_ph_key, default_phone),
            key=_ph_key,
            placeholder="010-1234-5678",
            help="하이픈(-) 포함 또는 미포함 모두 가능",
        )

        _c1, _c2, _c3 = st.columns(3)
        with _c1:
            _btn_kakao = st.button(
                "📲 카카오 알림톡 발송",
                key=f"{session_key}_kakao",
                use_container_width=True,
                type="primary",
            )
        with _c2:
            _btn_sms = st.button(
                "💬 SMS 문자 발송",
                key=f"{session_key}_sms",
                use_container_width=True,
            )
        with _c3:
            _btn_clear = st.button(
                "🗑️ 결과 초기화",
                key=f"{session_key}_clear",
                use_container_width=True,
            )

        if _btn_kakao:
            if not _phone.strip():
                st.warning("전화번호를 입력하세요.")
            elif not report_text or not report_text.strip():
                st.warning("발송할 보고서가 없습니다. 먼저 AI 분석을 실행하세요.")
            else:
                with st.spinner("📲 카카오 알림톡 발송 중..."):
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
                with st.spinner("💬 SMS 문자 발송 중..."):
                    res = send_report(_phone, report_text, title=title,
                                      force_sms=True, planner_info=planner_info)
                st.session_state[f"{session_key}_result"] = res
                st.rerun()

        if _btn_clear:
            st.session_state.pop(f"{session_key}_result", None)
            st.rerun()

        # ── 발송 내용 미리보기 ─────────────────────────────────────────
        if report_text:
            with st.expander("📄 발송 내용 미리보기 (클릭하여 확인)", expanded=False):
                st.text(report_text[:1500] + ("..." if len(report_text) > 1500 else ""))
        else:
            st.caption("⚠️ AI 분석 결과가 없습니다. 위에서 분석을 먼저 실행해 주세요.")

    if compact:
        import streamlit as st
        with st.expander("📲 카카오/SMS 발송", expanded=False):
            _inner()
    else:
        _inner()


# ==========================================================================
# [UTIL] 발송 설정 상태 확인 (관리자 탭용)
# ==========================================================================
def check_sender_config() -> dict:
    """발송 관련 환경변수 설정 현황 반환 (관리자 진단용)"""
    return {
        "KAKAO_API_KEY":     "✅ 설정됨" if _get_cfg("KAKAO_API_KEY")     else "❌ 미설정",
        "KAKAO_SENDER_KEY":  "✅ 설정됨" if _get_cfg("KAKAO_SENDER_KEY")  else "❌ 미설정",
        "KAKAO_TEMPLATE_ID": _get_cfg("KAKAO_TEMPLATE_ID") or "⚠️ 기본값(goldkey_report_v1) 사용",
        "SMS_API_KEY":       "✅ 설정됨" if _get_cfg("SMS_API_KEY")       else "❌ 미설정",
        "SMS_API_SECRET":    "✅ 설정됨" if _get_cfg("SMS_API_SECRET")    else "❌ 미설정",
        "SMS_SENDER_NUM":    _get_cfg("SMS_SENDER_NUM") or "❌ 미설정",
    }
