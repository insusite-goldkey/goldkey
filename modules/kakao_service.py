# ==========================================================================
# modules/kakao_service.py — 가이딩 프로토콜 제240조: 카카오톡 비즈니스 메시지
# ==========================================================================
# [제240조 구현 사양]
#   §1  메시지 유형: 분석 리포트 / 마스터의 약속 / 간편 알림
#   §2  GP200 브랜딩: 마스터 소속/성함/연락처 자동 하단 포함
#   §3  Kakao REST API 템플릿 기반 발송 (알림톡) + 나에게 보내기 폴백
#   §4  전역 발송 버튼 UI: #FEE500 배경, 검정 글자
#   §5  1인칭 화법 자동 구성
#   §6  보안: 핵심 요약만 전송 (PII 마스킹), 단기 링크 옵션
#
# [관리자 필수 설정 — st.secrets 또는 환경변수]
#   KAKAO_REST_API_KEY   — 카카오 개발자센터 REST API 키 (앱 키)
#   KAKAO_REDIRECT_URI   — 카카오 OAuth 리다이렉트 URI
#   KAKAO_CHANNEL_ID     — 카카오톡 채널 ID (_Oxxxx 형식, 알림톡용)
#   KAKAO_TEMPLATE_ID    — 알림톡 템플릿 코드 (사전 카카오 심사 필요)
#   GP200_MASTER_NAME    — 마스터 성함 (예: 이세윤)
#   GP200_MASTER_ORG     — 마스터 소속 (예: 골드키지사)
#   GP200_MASTER_PHONE   — 마스터 연락처 (예: 010-3074-2616)
#   GP200_MASTER_LICENSE — 설계사 자격번호 (옵션)
# ==========================================================================

from __future__ import annotations
import os
import json
import re
import hashlib
import time
from typing import Optional
from datetime import datetime


# ==========================================================================
# [CONFIG] 환경변수/Secrets 헬퍼
# ==========================================================================
def _cfg(key: str, default: str = "") -> str:
    """st.secrets → 환경변수 순으로 설정값 로드"""
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return str(val).strip()
    except Exception:
        pass
    return os.environ.get(key, default).strip()


def get_gp200_profile() -> dict:
    """
    GP200 마스터 프로필 로드.
    우선순위: session_state(art43 입력) > st.secrets/env
    """
    try:
        import streamlit as st
        _ss_name  = st.session_state.get("art43_planner_name", "").strip()
        _ss_tel   = st.session_state.get("art43_tel", "").strip()
        # gp200 설정 탭에서 저장된 값 우선
        _cfg_name = st.session_state.get("gp200_master_name", "").strip()
        _cfg_org  = st.session_state.get("gp200_master_org", "").strip()
        _cfg_tel  = st.session_state.get("gp200_master_phone", "").strip()
        _user     = st.session_state.get("user_name", "").strip()
    except Exception:
        _ss_name = _ss_tel = _cfg_name = _cfg_org = _cfg_tel = _user = ""

    name  = _cfg_name or _ss_name  or _cfg("GP200_MASTER_NAME")  or _user or "마스터"
    org   = _cfg_org  or _cfg("GP200_MASTER_ORG")  or "골드키지사"
    phone = _cfg_tel  or _ss_tel   or _cfg("GP200_MASTER_PHONE") or ""
    lic   = _cfg("GP200_MASTER_LICENSE")

    return {"name": name, "org": org, "phone": phone, "license": lic}


def _normalize_phone(phone: str) -> str:
    return re.sub(r"[^0-9]", "", str(phone or ""))


def _mask_pii(text: str) -> str:
    """주민번호·계좌번호·전화번호 마스킹 (발송 전 보안 처리)"""
    # 주민번호: 000000-0000000
    text = re.sub(r"\d{6}-\d{7}", "######-#######", text)
    # 전화번호 (수신자 제외)
    text = re.sub(r"0\d{1,2}-\d{3,4}-\d{4}", "010-****-****", text)
    # 계좌번호 11~14자리
    text = re.sub(r"\b\d{11,14}\b", "[계좌번호마스킹]", text)
    return text


# ==========================================================================
# [MSG TYPES] 1인칭 화법 메시지 빌더
# ==========================================================================
MSG_TYPE_REPORT   = "report"    # 분석 리포트
MSG_TYPE_PROMISE  = "promise"   # 마스터의 약속
MSG_TYPE_NOTICE   = "notice"    # 간편 알림


def build_message(
    msg_type: str,
    content: str,
    *,
    client_name: str = "고객",
    title: str = "",
    include_footer: bool = True,
    max_chars: int = 900,
) -> str:
    """
    GP240조 §3·§5: 1인칭 화법 + GP200 브랜딩 메시지 자동 구성.
    반환: 완성된 발송 문자열
    """
    profile = get_gp200_profile()
    master  = profile["name"]
    org     = profile["org"]
    phone   = profile["phone"]

    if msg_type == MSG_TYPE_REPORT:
        header = (
            f"[{org}] {master} 설계사입니다.\n"
            f"{client_name}님을 위해 정밀 분석한 'AI 인생 방어 리포트'가 도착했습니다.\n\n"
        )
    elif msg_type == MSG_TYPE_PROMISE:
        header = (
            f"[{org}] {master} 설계사입니다.\n"
            f"{client_name}님, 오늘 상담에서 제가 드린 약속을 정리해 보내드립니다.\n\n"
        )
    else:  # notice
        header = (
            f"[{org}] {master} 설계사입니다.\n"
            f"{client_name}님께 안내 말씀드립니다.\n\n"
        )

    if title:
        header += f"■ {title}\n\n"

    # 본문 길이 조정 (PII 마스킹 후)
    body = _mask_pii(content)
    available = max_chars - len(header) - 60  # 푸터 공간 확보
    if len(body) > available:
        body = body[:available] + "…"

    footer = ""
    if include_footer:
        footer_parts = [f"\n\n─────────────────\n담당: {master} ({org})"]
        if phone:
            footer_parts.append(f"연락처: {phone}")
        if profile.get("license"):
            footer_parts.append(f"자격번호: {profile['license']}")
        footer = "\n".join(footer_parts)

    return header + body + footer


# ==========================================================================
# [CORE A] 카카오톡 나에게 보내기 (OAuth 토큰 기반 — 개발/테스트용)
# ==========================================================================
def _get_kakao_token() -> Optional[str]:
    """session_state에 저장된 카카오 액세스 토큰 반환"""
    try:
        import streamlit as st
        return st.session_state.get("_kakao_access_token")
    except Exception:
        return None


def send_kakao_memo(message: str) -> dict:
    """
    나에게 보내기 API (OAuth 토큰 필요, 테스트/개발 환경용).
    실제 고객 발송은 send_kakao_alimtalk() 사용.
    """
    token = _get_kakao_token()
    if not token:
        return {"success": False, "method": "memo", "msg": "카카오 액세스 토큰 없음", "code": "NO_TOKEN"}

    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": message[:2000],
            "link": {"web_url": "https://goldkey-ai-817097913199.asia-northeast3.run.app"},
        }, ensure_ascii=False)
    }
    try:
        import urllib.request as _req
        import urllib.parse  as _up
        data = _up.urlencode(payload).encode("utf-8")
        req  = _req.Request(
            "https://kapi.kakao.com/v2/api/talk/memo/default/send",
            data=data, method="POST",
        )
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with _req.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if body.get("result_code") == 0:
                return {"success": True, "method": "memo", "msg": "나에게 보내기 성공", "code": "OK"}
            return {"success": False, "method": "memo", "msg": str(body), "code": "API_ERR"}
    except Exception as e:
        return {"success": False, "method": "memo", "msg": str(e), "code": "EXCEPTION"}


# ==========================================================================
# [CORE B] 카카오 알림톡 발송 (비즈니스 API — 실제 고객 발송)
# ==========================================================================
def send_kakao_alimtalk(
    phone: str,
    message: str,
    *,
    template_id: Optional[str] = None,
    button_label: str = "리포트 확인",
    button_url: str = "https://goldkey-ai-817097913199.asia-northeast3.run.app",
) -> dict:
    """
    카카오 알림톡 발송 (NHN Cloud / 카카오 비즈메시지 API).
    KAKAO_REST_API_KEY, KAKAO_CHANNEL_ID, KAKAO_TEMPLATE_ID 필요.
    """
    api_key    = _cfg("KAKAO_REST_API_KEY")
    channel_id = _cfg("KAKAO_CHANNEL_ID")
    tmpl       = template_id or _cfg("KAKAO_TEMPLATE_ID", "goldkey_report_v1")
    phone_norm = _normalize_phone(phone)

    if not api_key or not channel_id:
        return {"success": False, "method": "alimtalk",
                "msg": "KAKAO_REST_API_KEY 또는 KAKAO_CHANNEL_ID 미설정. 관리자 안내 참조.",
                "code": "NO_KEY"}
    if not phone_norm or len(phone_norm) < 10:
        return {"success": False, "method": "alimtalk",
                "msg": f"전화번호 형식 오류: '{phone}'", "code": "BAD_PHONE"}

    payload = {
        "senderKey":   channel_id,
        "templateCode": tmpl,
        "recipientList": [{
            "recipientNo": phone_norm,
            "templateParameter": {
                "content": message[:990],
                "button_label": button_label,
                "button_url":   button_url,
            },
        }],
    }
    try:
        import urllib.request as _req
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        url  = f"https://api-alimtalk.cloud.toast.com/alimtalk/v2.3/appkeys/{api_key}/messages"
        req  = _req.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json;charset=UTF-8")
        with _req.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            if body.get("header", {}).get("isSuccessful"):
                return {"success": True, "method": "alimtalk", "msg": "알림톡 발송 성공", "code": "OK"}
            err = body.get("header", {}).get("resultMessage", "발송 실패")
            return {"success": False, "method": "alimtalk", "msg": err, "code": "API_ERR"}
    except Exception as e:
        return {"success": False, "method": "alimtalk", "msg": str(e), "code": "EXCEPTION"}


# ==========================================================================
# [CORE C] SMS 폴백 (솔라API v4)
# ==========================================================================
def send_sms(phone: str, message: str) -> dict:
    """SMS 발송 폴백 — 알림톡 실패 시 자동 전환"""
    api_key    = _cfg("SMS_API_KEY")
    api_secret = _cfg("SMS_API_SECRET")
    sender_num = _cfg("SMS_SENDER_NUM")
    phone_norm = _normalize_phone(phone)

    if not api_key or not api_secret:
        return {"success": False, "method": "sms", "msg": "SMS_API_KEY/SECRET 미설정", "code": "NO_KEY"}
    if not sender_num:
        return {"success": False, "method": "sms", "msg": "SMS_SENDER_NUM 미설정", "code": "NO_SENDER"}
    if not phone_norm or len(phone_norm) < 10:
        return {"success": False, "method": "sms", "msg": f"전화번호 오류: '{phone}'", "code": "BAD_PHONE"}

    enc_bytes = message.encode("euc-kr", errors="ignore")
    msg_type  = "SMS" if len(enc_bytes) <= 90 else "LMS"
    text      = message[:1900] if msg_type == "LMS" else message[:45]

    try:
        import urllib.request as _req
        import base64, hmac, hashlib as _hs
        ts   = str(int(time.time() * 1000))
        salt = ts
        sign_str = f"POST\n/messages\n{ts}\n{api_key}\n{salt}"
        sig  = base64.b64encode(
            hmac.new(api_secret.encode(), sign_str.encode(), _hs.sha256).digest()
        ).decode()

        payload = {"type": msg_type, "from": _normalize_phone(sender_num),
                   "to": phone_norm, "text": text}
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req  = _req.Request("https://api.solapi.com/messages/v4/send", data=data, method="POST")
        req.add_header("Content-Type", "application/json;charset=UTF-8")
        req.add_header("Authorization",
                       f"HMAC-SHA256 apiKey={api_key}, date={ts}, salt={salt}, signature={sig}")
        with _req.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            ok   = body.get("groupInfo", {}).get("count", {}).get("success", 0)
            if ok > 0:
                return {"success": True, "method": "sms", "msg": f"{msg_type} 발송 성공", "code": "OK"}
            fail = body.get("failedMessageList", [{}])
            return {"success": False, "method": "sms",
                    "msg": fail[0].get("reason", "발송 실패") if fail else "발송 실패",
                    "code": "FAIL"}
    except Exception as e:
        return {"success": False, "method": "sms", "msg": str(e), "code": "EXCEPTION"}


# ==========================================================================
# [CORE D] 통합 발송 (알림톡 → SMS 자동 폴백)
# ==========================================================================
def send_report(
    phone: str,
    message: str,
    *,
    msg_type: str = MSG_TYPE_REPORT,
    client_name: str = "고객",
    title: str = "",
    force_sms: bool = False,
) -> dict:
    """
    GP240조 통합 발송 함수.
    1) 메시지 자동 구성 (1인칭 화법 + GP200 푸터)
    2) 알림톡 시도 → 실패 시 SMS 폴백
    """
    full_msg = build_message(
        msg_type, message,
        client_name=client_name,
        title=title,
    )

    if not force_sms:
        r = send_kakao_alimtalk(phone, full_msg)
        if r["success"]:
            return r
        # 알림톡 키 없으면 SMS 직접 시도
        r2 = send_sms(phone, full_msg)
        if r2["success"]:
            r2["msg"] = f"알림톡({r['code']}) → SMS 폴백 성공"
        else:
            r2["msg"] = f"알림톡({r['code']}) + SMS({r2['code']}) 모두 실패 — API 키 설정 확인"
            r2["code"] = "ALL_FAILED"
        return r2
    return send_sms(phone, full_msg)


# ==========================================================================
# [UI] GP240조 전역 발송 버튼 — 카카오 상징색 #FEE500
# ==========================================================================
def render_kakao_btn(
    report_text: str,
    session_key: str,
    *,
    client_name: str = "고객",
    msg_type: str = MSG_TYPE_REPORT,
    title: str = "",
    default_phone: str = "",
    compact: bool = True,
) -> None:
    """
    GP240조 §4: 분석 결과창 하단 카카오 발송 액션 버튼.
    compact=True  → expander 안에 숨겨진 형태 (탭 오염 최소화)
    compact=False → 전체 UI 노출
    """
    try:
        import streamlit as st
    except ImportError:
        return

    # ── 이전 발송 결과 토스트 표시 ─────────────────────────────────────
    _prev = st.session_state.get(f"{session_key}_kakao_result")
    if _prev:
        if _prev.get("success"):
            st.success(
                f"✅ [{_prev.get('method','').upper()}] 발송 완료 — {_prev.get('msg','')}",
                icon="📲",
            )
        else:
            st.error(
                f"❌ [{_prev.get('method','').upper()}] 발송 실패 — {_prev.get('msg','')}",
                icon="⚠️",
            )

    def _inner():
        # ── 카카오 상징색 헤더 ──────────────────────────────────────
        st.markdown("""
<div style="background:#FEE500;border-radius:10px;padding:10px 16px;
  margin-bottom:10px;display:flex;align-items:center;gap:10px;">
  <span style="font-size:1.4rem;">💬</span>
  <div>
    <div style="font-size:0.95rem;font-weight:900;color:#3C1E1E;">
      카카오톡으로 분석 결과 전송
    </div>
    <div style="font-size:0.72rem;color:#5c3d00;margin-top:2px;">
      알림톡 우선 발송 · 실패 시 SMS 자동 전환 · GP200 브랜딩 자동 포함
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        # ── GP200 프로필 미리보기 ───────────────────────────────────
        _p = get_gp200_profile()
        st.caption(
            f"📌 발신자: {_p['name']} ({_p['org']})"
            + (f" · {_p['phone']}" if _p.get("phone") else "")
        )

        # ── 수신자 입력 ─────────────────────────────────────────────
        _ph_key  = f"{session_key}_recv_phone"
        _recv_ph = st.text_input(
            "📱 수신자 전화번호",
            value=st.session_state.get(_ph_key, default_phone),
            key=_ph_key,
            placeholder="010-1234-5678",
            help="고객 연락처 (하이픈 포함/미포함 모두 가능)",
        )

        # ── 메시지 유형 선택 ────────────────────────────────────────
        _type_map = {
            "📊 분석 리포트": MSG_TYPE_REPORT,
            "🤝 마스터의 약속": MSG_TYPE_PROMISE,
            "📢 간편 알림": MSG_TYPE_NOTICE,
        }
        _type_label = st.radio(
            "메시지 유형",
            list(_type_map.keys()),
            horizontal=True,
            key=f"{session_key}_msg_type",
            label_visibility="collapsed",
        )
        _sel_type = _type_map[_type_label]

        # ── 발송 버튼 (카카오 골드 스타일) ─────────────────────────
        _c1, _c2, _c3 = st.columns([3, 2, 1])
        with _c1:
            _btn_send = st.button(
                "💬 카카오톡으로 전송",
                key=f"{session_key}_send_btn",
                use_container_width=True,
                type="primary",
                help="알림톡 → SMS 자동 폴백",
            )
        with _c2:
            _btn_sms = st.button(
                "📩 SMS만 발송",
                key=f"{session_key}_sms_btn",
                use_container_width=True,
            )
        with _c3:
            _btn_clr = st.button(
                "🗑️",
                key=f"{session_key}_clr_btn",
                use_container_width=True,
                help="결과 초기화",
            )

        if _btn_send:
            if not _recv_ph.strip():
                st.warning("수신자 전화번호를 입력하세요.")
            elif not report_text or not str(report_text).strip():
                st.warning("발송할 분석 결과가 없습니다. 먼저 AI 분석을 실행하세요.")
            else:
                with st.spinner("📲 카카오 알림톡 발송 중..."):
                    _res = send_report(
                        _recv_ph, str(report_text),
                        msg_type=_sel_type,
                        client_name=client_name,
                        title=title,
                    )
                st.session_state[f"{session_key}_kakao_result"] = _res
                st.rerun()

        if _btn_sms:
            if not _recv_ph.strip():
                st.warning("수신자 전화번호를 입력하세요.")
            elif not report_text or not str(report_text).strip():
                st.warning("발송할 분석 결과가 없습니다. 먼저 AI 분석을 실행하세요.")
            else:
                with st.spinner("📩 SMS 발송 중..."):
                    _res = send_report(
                        _recv_ph, str(report_text),
                        msg_type=_sel_type,
                        client_name=client_name,
                        title=title,
                        force_sms=True,
                    )
                st.session_state[f"{session_key}_kakao_result"] = _res
                st.rerun()

        if _btn_clr:
            st.session_state.pop(f"{session_key}_kakao_result", None)
            st.rerun()

        # ── 발송 내용 미리보기 ──────────────────────────────────────
        if report_text and str(report_text).strip():
            with st.expander("📄 전송 내용 미리보기", expanded=False):
                _preview = build_message(
                    _sel_type, str(report_text),
                    client_name=client_name, title=title,
                )
                st.text(_preview[:1200] + ("…" if len(_preview) > 1200 else ""))
        else:
            st.caption("⚠️ AI 분석 실행 후 발송 가능합니다.")

    if compact:
        with st.expander("💬 카카오톡으로 분석 결과 전송", expanded=False):
            _inner()
    else:
        _inner()


# ==========================================================================
# [UI] 고객 관리 탭용 — 인라인 발송 버튼 (연락처 옆 배치)
# ==========================================================================
def render_customer_kakao_btn(
    customer_name: str,
    customer_phone: str,
    session_key: str,
    *,
    btn_label: str = "💬 카카오톡 상담 요청",
    notice_text: str = "",
) -> None:
    """
    고객 관리 탭에서 각 고객 행 옆에 배치하는 인라인 카카오 버튼.
    """
    try:
        import streamlit as st
    except ImportError:
        return

    _prev = st.session_state.get(f"{session_key}_kakao_result")
    if _prev:
        _icon = "✅" if _prev.get("success") else "❌"
        st.caption(f"{_icon} {_prev.get('msg', '')[:40]}")

    if st.button(
        btn_label,
        key=f"{session_key}_kakao_inline",
        use_container_width=True,
        help=f"{customer_name}님께 카카오톡 발송",
    ):
        if not customer_phone:
            st.warning(f"{customer_name}님 전화번호가 없습니다.")
            return
        _msg = notice_text or f"안녕하세요, {customer_name}님! 상담 일정을 확인해 주세요."
        with st.spinner("발송 중..."):
            _res = send_report(
                customer_phone, _msg,
                msg_type=MSG_TYPE_NOTICE,
                client_name=customer_name,
                title="상담 요청",
            )
        st.session_state[f"{session_key}_kakao_result"] = _res
        st.rerun()


# ==========================================================================
# [ADMIN] 발송 설정 상태 점검 (관리자 탭 진단용)
# ==========================================================================
def check_config() -> dict:
    """API 키 설정 현황 반환"""
    p = get_gp200_profile()
    return {
        "KAKAO_REST_API_KEY":  "✅ 설정됨" if _cfg("KAKAO_REST_API_KEY")  else "❌ 미설정",
        "KAKAO_CHANNEL_ID":    "✅ 설정됨" if _cfg("KAKAO_CHANNEL_ID")    else "❌ 미설정",
        "KAKAO_TEMPLATE_ID":   _cfg("KAKAO_TEMPLATE_ID") or "⚠️ 기본값(goldkey_report_v1) 사용",
        "SMS_API_KEY":         "✅ 설정됨" if _cfg("SMS_API_KEY")          else "❌ 미설정",
        "SMS_SENDER_NUM":      _cfg("SMS_SENDER_NUM")  or "❌ 미설정",
        "GP200_MASTER_NAME":   p["name"]  or "❌ 미설정",
        "GP200_MASTER_ORG":    p["org"]   or "❌ 미설정",
        "GP200_MASTER_PHONE":  p["phone"] or "⚠️ 미설정 (메시지 하단에 연락처 누락됨)",
    }


def render_config_panel() -> None:
    """관리자 탭: GP240조 설정 패널"""
    try:
        import streamlit as st
    except ImportError:
        return

    st.markdown("""
<div style="background:linear-gradient(135deg,#FEE500,#FFD000);
  border-radius:10px;padding:12px 16px;margin-bottom:12px;">
  <span style="font-size:1rem;font-weight:900;color:#3C1E1E;">
    💬 GP240조 카카오 발송 설정 (관리자)
  </span>
</div>""", unsafe_allow_html=True)

    cfg = check_config()
    for k, v in cfg.items():
        _icon = "✅" if "설정됨" in str(v) else ("⚠️" if "기본값" in str(v) or "미설정됨" in str(v) else "❌")
        st.markdown(f"- **{k}**: {v}")

    st.divider()
    st.markdown("**🖊️ GP200 마스터 정보 (세션 등록)**")
    _c1, _c2 = st.columns(2)
    with _c1:
        _n = st.text_input("성함", key="gp200_master_name",
                           value=st.session_state.get("gp200_master_name", ""),
                           placeholder="예: 이세윤")
        _o = st.text_input("소속", key="gp200_master_org",
                           value=st.session_state.get("gp200_master_org", ""),
                           placeholder="예: 골드키지사")
    with _c2:
        _ph = st.text_input("연락처", key="gp200_master_phone",
                            value=st.session_state.get("gp200_master_phone", ""),
                            placeholder="010-0000-0000")
        _lic = st.text_input("자격번호 (옵션)", key="gp200_master_license",
                             value=st.session_state.get("gp200_master_license", ""))

    if st.button("💾 마스터 정보 저장 (세션)", key="gp200_save_btn",
                 use_container_width=True, type="primary"):
        st.success("✅ GP200 마스터 정보가 세션에 저장되었습니다. 모든 발송 메시지에 자동 포함됩니다.")
        st.rerun()
