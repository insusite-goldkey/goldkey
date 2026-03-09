# ==========================================================================
# modules/kakao_memo.py — 카카오 '나에게 보내기' (Memo Default API)
# ==========================================================================
# [가이딩 프로토콜 제241조]
#   - 사업자 채널·알림톡 템플릿 심사 없이 REST API KEY만으로 즉시 발송
#   - 마스터 본인의 카카오톡 '나와의 채팅'으로 리포트 전송
#   - 마스터가 확인 후 고객 채팅방으로 '전달하기' 실행
#
# 필요 권한 (카카오 개발자 콘솔):
#   - 앱 → 카카오 로그인 → 동의항목 → talk_message (카카오톡 메시지 전송) 활성화
#   - 플랫폼 → Web → 사이트 도메인에 배포 URL 등록 필수
#
# 인증 흐름:
#   1. 마스터가 [카카오 로그인] 버튼 클릭 → OAuth2.0 인증 URL로 리다이렉트
#   2. 카카오 로그인 후 redirect_uri로 code 수신
#   3. code → access_token 교환
#   4. access_token으로 /v2/api/talk/memo/default/send 호출
# ==========================================================================

from __future__ import annotations
import os
import json
import urllib.parse
import urllib.request
from typing import Optional


# ==========================================================================
# [CONFIG] 환경변수 / secrets 로드
# ==========================================================================
def _get_cfg(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        val = st.secrets.get(key, "") or ""
    except Exception:
        val = ""
    if not val:
        val = os.environ.get(key, default)
    return str(val).strip()


def get_rest_api_key() -> str:
    return _get_cfg("KAKAO_REST_API_KEY") or _get_cfg("KAKAO_API_KEY")


def get_redirect_uri() -> str:
    uri = _get_cfg("KAKAO_REDIRECT_URI")
    if uri:
        return uri
    # Cloud Run 배포 URL 자동 감지
    cr = _get_cfg("K_SERVICE")  # Cloud Run 자동 환경변수
    if cr:
        return "https://goldkey-ai-817097913199.asia-northeast3.run.app/"
    return "http://localhost:8501/"


# ==========================================================================
# [STEP 1] OAuth2.0 인증 URL 생성
# ==========================================================================
def get_auth_url() -> str:
    """
    마스터가 클릭할 카카오 로그인 URL 생성.
    talk_message scope 포함 → '나에게 보내기' 권한 요청.
    """
    rest_key = get_rest_api_key()
    redirect_uri = get_redirect_uri()
    params = {
        "client_id": rest_key,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "talk_message",
    }
    return "https://kauth.kakao.com/oauth/authorize?" + urllib.parse.urlencode(params)


# ==========================================================================
# [STEP 2] Authorization Code → Access Token 교환
# ==========================================================================
def exchange_code_for_token(code: str) -> dict:
    """
    카카오 OAuth 인증 코드를 access_token으로 교환.
    반환: {"access_token": str, "refresh_token": str, ...} 또는 {"error": str}
    """
    rest_key = get_rest_api_key()
    redirect_uri = get_redirect_uri()
    if not rest_key:
        return {"error": "KAKAO_REST_API_KEY 미설정"}

    payload = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": rest_key,
        "redirect_uri": redirect_uri,
        "code": code,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://kauth.kakao.com/oauth/token",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return {"error": f"HTTP {e.code}", "detail": body}
    except Exception as e:
        return {"error": str(e)}


# ==========================================================================
# [STEP 3] Access Token 갱신 (Refresh)
# ==========================================================================
def refresh_access_token(refresh_token: str) -> dict:
    """만료된 access_token을 refresh_token으로 갱신."""
    rest_key = get_rest_api_key()
    if not rest_key:
        return {"error": "KAKAO_REST_API_KEY 미설정"}

    payload = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": rest_key,
        "refresh_token": refresh_token,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://kauth.kakao.com/oauth/token",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


# ==========================================================================
# [STEP 4] 나에게 보내기 — 메모 기본 템플릿
# ==========================================================================
def send_memo(
    access_token: str,
    report_text: str,
    *,
    title: str = "골드키 마스터 리포트",
    planner_info: Optional[dict] = None,
) -> dict:
    """
    POST /v2/api/talk/memo/default/send
    별도 SENDER_KEY·채널·템플릿 심사 없이 access_token만으로 발송.
    반환: {"result_code": 0} 성공 / {"error": ...} 실패
    """
    if not access_token:
        return {"error": "access_token 없음 — 먼저 카카오 로그인이 필요합니다."}

    # 메시지 본문 요약 (카카오 기본 템플릿 text 최대 200자 권장)
    _summary = _build_summary(report_text, title=title, planner_info=planner_info)

    # 기본 텍스트 템플릿 (link 필수 → 앱 URL 삽입)
    _app_url = _get_cfg("KAKAO_REDIRECT_URI") or "https://goldkey-ai-817097913199.asia-northeast3.run.app/"
    template = {
        "object_type": "text",
        "text": _summary,
        "link": {
            "web_url": _app_url,
            "mobile_web_url": _app_url,
        },
        "button_title": "골드키 앱에서 보기",
    }

    payload = urllib.parse.urlencode(
        {"template_object": json.dumps(template, ensure_ascii=False)}
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {access_token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("result_code") == 0:
                return {"success": True, "result_code": 0}
            return {"error": f"발송 실패 (result_code={result.get('result_code')})", "raw": result}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        _parsed = {}
        try:
            _parsed = json.loads(body)
        except Exception:
            pass
        _msg = _parsed.get("msg") or body[:200]
        return {"error": f"HTTP {e.code}: {_msg}", "detail": body}
    except Exception as e:
        return {"error": str(e)}


# ==========================================================================
# [UTIL] 리포트 텍스트 → 카카오톡 메시지 요약 변환
# ==========================================================================
def _build_summary(
    report_text: str,
    *,
    title: str = "골드키 마스터 리포트",
    planner_info: Optional[dict] = None,
    max_len: int = 400,
) -> str:
    """
    분석 결과 텍스트를 카카오톡 기본 템플릿용 요약문으로 변환.
    [GP241조] 핵심 내용 위주, 400자 이내.
    """
    _header = f"[{title}]\n"

    # GP200조 브랜딩 푸터
    _footer = ""
    if planner_info:
        _co = (planner_info.get("company") or "").strip()
        _nm = (planner_info.get("name") or "").strip()
        if _co or _nm:
            _footer = f"\n\n[발송: {' '.join(filter(None, [_co, _nm]))} 설계사]\n확인 후 고객님께 전달해 주세요."

    _body_limit = max_len - len(_header) - len(_footer) - 10
    _body = (report_text or "분석 결과를 확인하세요.").strip()
    if len(_body) > _body_limit:
        _body = _body[:_body_limit] + "…"

    return _header + _body + _footer


# ==========================================================================
# [GP250] 질병 경제적 위협액 → 카카오톡 메시지 변환
# ==========================================================================
def build_gp250_report(
    disease_name: str,
    loss: dict,
    *,
    period_label: str = "2년",
    big5_mode: bool = False,
    income_man: float = 0.0,
    client_name: str = "",
    planner_info: Optional[dict] = None,
) -> str:
    """
    GP250 위젯의 _gp68_calc_loss() 결과 dict를 받아
    카카오톡 '나에게 보내기'용 리포트 텍스트를 생성합니다.

    loss dict 키: treatment, nursing, room_extra, adv_cost, income_loss, total, source
    """
    def _fmt(v_man: int) -> str:
        if v_man >= 10000:
            e = v_man // 10000
            r = v_man % 10000
            return f"{e}억 {r:,}만원" if r else f"{e}억원"
        return f"{v_man:,}만원"

    _mode = "서울 5대병원 마스터형" if big5_mode else "국가 표준형"
    _cname = f"{client_name}님 " if client_name else ""
    _inc_line = (
        f"• 소득 손실 ({income_man:.0f}만원/월 기준): {_fmt(loss.get('income_loss', 0))}\n"
        if income_man > 0 else
        "• 소득 손실: 미반영 (소득 미입력)\n"
    )
    _room_line = (
        f"• 1인실 입원비: {_fmt(loss.get('room_extra', 0))}\n"
        if loss.get("room_extra", 0) > 0 else ""
    )
    _adv_line = (
        f"• 첨단치료비 추가: {_fmt(loss.get('adv_cost', 0))}\n"
        if loss.get("adv_cost", 0) > 0 else ""
    )
    _source = loss.get("source", "건강보험심사평가원 통계")

    _body = (
        f"[골드키AI] {_cname}질병 경제적 위협 분석 ({_mode})\n"
        f"{'=' * 26}\n"
        f"📋 질병명: {disease_name}\n"
        f"📅 분석 기간: {period_label}\n\n"
        f"💸 예상 손실 내역\n"
        f"• 치료비: {_fmt(loss.get('treatment', 0))}\n"
        f"• 간병비: {_fmt(loss.get('nursing', 0))}\n"
        f"{_room_line}"
        f"{_adv_line}"
        f"{_inc_line}"
        f"{'─' * 26}\n"
        f"🚨 총 경제적 위협액: {_fmt(loss.get('total', 0))}\n\n"
        f"📌 출처: {_source}\n"
        f"※ 개인차 있음. 참고용 통계치입니다.\n"
    )

    # GP200 브랜딩 푸터
    if planner_info:
        _co = (planner_info.get("company") or "").strip()
        _nm = (planner_info.get("name") or "").strip()
        _ct = (planner_info.get("contact") or "").strip()
        _parts = list(filter(None, [_co, _nm]))
        if _parts:
            _body += f"\n[발송: {' '.join(_parts)} 설계사"
            if _ct:
                _body += f" | {_ct}"
            _body += "]\n확인 후 고객님께 전달해 주세요."

    return _body


# ==========================================================================
# [SESSION] access_token session_state 관리 헬퍼
# ==========================================================================
_TOKEN_KEY = "_kakao_memo_access_token"
_REFRESH_KEY = "_kakao_memo_refresh_token"


def save_tokens(access_token: str, refresh_token: str = "") -> None:
    try:
        import streamlit as st
        st.session_state[_TOKEN_KEY] = access_token
        if refresh_token:
            st.session_state[_REFRESH_KEY] = refresh_token
    except Exception:
        pass


def load_access_token() -> str:
    try:
        import streamlit as st
        return st.session_state.get(_TOKEN_KEY, "")
    except Exception:
        return ""


def load_refresh_token() -> str:
    try:
        import streamlit as st
        return st.session_state.get(_REFRESH_KEY, "")
    except Exception:
        return ""


def clear_tokens() -> None:
    try:
        import streamlit as st
        st.session_state.pop(_TOKEN_KEY, None)
        st.session_state.pop(_REFRESH_KEY, None)
    except Exception:
        pass


def is_logged_in() -> bool:
    return bool(load_access_token())


# ==========================================================================
# [UI] Streamlit 나에게 보내기 UI 헬퍼
# ==========================================================================
def render_memo_ui(
    report_text: str,
    *,
    title: str = "골드키 마스터 리포트",
    session_key: str = "_memo_send",
    planner_info: Optional[dict] = None,
    compact: bool = False,
) -> None:
    """
    [GP241조] 나에게 보내기 UI 렌더링.
    - 미로그인: [카카오 로그인] 버튼 표시
    - 로그인 후: [카카오톡으로 결과 받기] 버튼 표시
    """
    try:
        import streamlit as st
    except ImportError:
        return

    _rest_key = get_rest_api_key()
    if not _rest_key:
        st.caption("⚠️ KAKAO_REST_API_KEY 미설정 — GitHub Secrets에 등록하세요.")
        return

    def _inner():
        # ── OAuth code 수신 처리 (redirect 후 URL params) ──────────────
        _params = st.query_params
        _code = _params.get("code", "")
        _error = _params.get("error", "")

        if _error:
            st.error(f"카카오 로그인 실패: {_params.get('error_description', _error)}")
            st.query_params.clear()

        if _code and not is_logged_in():
            with st.spinner("🔐 카카오 인증 처리 중..."):
                _result = exchange_code_for_token(_code)
            if "access_token" in _result:
                save_tokens(
                    _result["access_token"],
                    _result.get("refresh_token", ""),
                )
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"토큰 교환 실패: {_result.get('error', '')} {_result.get('detail', '')}")
                st.query_params.clear()

        # ── 이전 발송 결과 ────────────────────────────────────────────
        _prev = st.session_state.get(f"{session_key}_result")
        if _prev and _prev.get("success"):
            st.markdown("""
<div style="background:linear-gradient(135deg,#EBF5FF,#DBEAFE);
  border-radius:12px;padding:14px 18px;margin-bottom:12px;
  border-left:4px solid #3B82F6;box-shadow:0 2px 8px rgba(59,130,246,0.15);">
  <div style="font-size:0.95rem;font-weight:900;color:#1D4ED8;">
    📲 마스터님의 카카오톡으로 리포트가 전송되었습니다!
  </div>
  <div style="font-size:0.82rem;color:#3B82F6;margin-top:4px;">
    확인 후 고객님께 전달해 주세요. 카카오톡 → '나와의 채팅' 확인
  </div>
</div>""", unsafe_allow_html=True)

        # ── 안내 배너 ────────────────────────────────────────────────
        st.markdown("""
<div style="background:linear-gradient(135deg,#F0F9FF,#E0F2FE);
  border-radius:10px;padding:12px 16px;margin-bottom:10px;
  border-left:4px solid #0EA5E9;">
  <div style="font-size:0.93rem;font-weight:900;color:#0369A1;">
    📩 카카오톡 '나에게 보내기'
    <span style="font-size:0.72rem;background:#0EA5E9;color:#fff;
    border-radius:4px;padding:1px 6px;margin-left:6px;font-weight:700;">
    사업자 불필요</span>
  </div>
  <div style="font-size:0.75rem;color:#0369A1;margin-top:3px;">
    마스터 본인 카카오톡으로 리포트 수신 → 고객에게 전달하기
  </div>
</div>""", unsafe_allow_html=True)

        # ── 로그인 상태 분기 ──────────────────────────────────────────
        if not is_logged_in():
            _auth_url = get_auth_url()

            # ── [GP241조 §보안] 데이터 보안 및 권한 활용 안내 게이트 ──────────
            st.markdown("""
<div style="background:linear-gradient(135deg,#EFF6FF,#DBEAFE);
  border:1.5px solid #3B82F6;border-left:5px solid #1D4ED8;
  border-radius:12px;padding:16px 18px 12px 18px;margin-bottom:12px;
  box-shadow:0 3px 12px rgba(59,130,246,0.18);">
  <div style="font-size:0.95rem;font-weight:900;color:#1E3A8A;margin-bottom:10px;
    display:flex;align-items:center;gap:8px;">
    🔒 데이터 보안 및 권한 활용 안내
    <span style="font-size:0.68rem;background:#1D4ED8;color:#fff;
      border-radius:4px;padding:1px 7px;font-weight:700;">금융권 수준</span>
  </div>
  <div style="font-size:0.80rem;color:#1E3A8A;line-height:1.85;">
    <div style="margin-bottom:5px;">
      <span style="font-weight:800;color:#1D4ED8;">① 권한 목적</span><br>
      <span style="color:#1e40af;">AI 분석 리포트를 마스터님의 카카오톡으로
      안전하게 전송하기 위한 목적으로만 사용됩니다.</span>
    </div>
    <div style="margin-bottom:5px;">
      <span style="font-weight:800;color:#1D4ED8;">② 보안 범위</span><br>
      <span style="color:#1e40af;">대화 내용 열람 및 친구 목록 수집은
      <b>기술적으로 불가능</b>합니다.
      (요청 권한: <code style="background:#DBEAFE;padding:1px 4px;border-radius:3px;">talk_message</code> 발송 전용)</span>
    </div>
    <div>
      <span style="font-weight:800;color:#1D4ED8;">③ 데이터 보존</span><br>
      <span style="color:#1e40af;">전송 데이터는 TLS 암호화 처리 후
      발송 즉시 파기됩니다. 서버에 저장되지 않습니다.</span>
    </div>
  </div>
  <div style="margin-top:10px;padding-top:8px;border-top:1px solid rgba(59,130,246,0.25);
    font-size:0.72rem;color:#3B82F6;">
    🔗 권한 철회: 카카오톡 설정 → 자산 → 서비스 관리에서 언제든지 철회 가능
  </div>
</div>""", unsafe_allow_html=True)

            # ── 동의 체크박스 (체크 전 로그인 버튼 비활성화) ─────────────────
            _consent_key = f"{session_key}_security_consent"
            _consented = st.checkbox(
                "보안 가이드를 확인하였으며, 리포트 전송 권한 승인에 동의합니다",
                key=_consent_key,
                value=st.session_state.get(_consent_key, False),
            )

            if _consented:
                st.markdown(f"""
<div style="text-align:center;margin:12px 0;">
  <a href="{_auth_url}" target="_self"
     style="display:inline-block;background:#FEE500;color:#3C1E1E;
     font-size:0.95rem;font-weight:900;padding:12px 28px;
     border-radius:10px;text-decoration:none;
     box-shadow:0 4px 14px rgba(0,0,0,0.18);
     transition:box-shadow 0.2s;">
    🔑 카카오 로그인 (나에게 보내기 권한 승인)
  </a>
</div>
<div style="text-align:center;font-size:0.73rem;color:#6B7280;margin-top:4px;">
  최초 1회만 로그인하면 이후 자동으로 발송됩니다.
</div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
<div style="text-align:center;margin:12px 0;">
  <div style="display:inline-block;background:#D1D5DB;color:#9CA3AF;
    font-size:0.95rem;font-weight:900;padding:12px 28px;
    border-radius:10px;cursor:not-allowed;
    box-shadow:0 2px 6px rgba(0,0,0,0.08);">
    🔑 카카오 로그인 (위 안내 동의 후 활성화)
  </div>
</div>
<div style="text-align:center;font-size:0.73rem;color:#9CA3AF;margin-top:4px;">
  위 체크박스에 동의하시면 로그인 버튼이 활성화됩니다.
</div>""", unsafe_allow_html=True)

        else:
            # ── 메시지 미리보기 ─────────────────────────────────────
            _summary = _build_summary(report_text, title=title, planner_info=planner_info)
            with st.expander("📄 전송될 메시지 미리보기", expanded=False):
                st.markdown(f"""
<div style="background:#FEE500;border-radius:12px;padding:14px 16px;
  max-width:360px;font-size:0.82rem;line-height:1.75;color:#3C1E1E;
  white-space:pre-wrap;font-family:'Noto Sans KR','Malgun Gothic',sans-serif;
  box-shadow:0 2px 8px rgba(0,0,0,0.12);">
  <div style="font-size:0.88rem;font-weight:900;margin-bottom:6px;
    border-bottom:1px solid rgba(0,0,0,0.1);padding-bottom:6px;">
    💬 나와의 채팅 미리보기
  </div>
  {_summary.replace(chr(10), '<br>')}
</div>""", unsafe_allow_html=True)

            # ── 전송 버튼 행 ────────────────────────────────────────
            _c1, _c2 = st.columns([3, 1])
            with _c1:
                _send_btn = st.button(
                    "📲 카카오톡으로 결과 받기",
                    key=f"{session_key}_send",
                    use_container_width=True,
                    type="primary",
                )
            with _c2:
                _logout_btn = st.button(
                    "로그아웃",
                    key=f"{session_key}_logout",
                    use_container_width=True,
                )

            if _send_btn:
                if not report_text or not report_text.strip():
                    st.warning("발송할 보고서가 없습니다. 먼저 AI 분석을 실행하세요.")
                else:
                    with st.spinner("📲 카카오톡으로 전송 중..."):
                        _tok = load_access_token()
                        _res = send_memo(
                            _tok,
                            report_text,
                            title=title,
                            planner_info=planner_info,
                        )

                    if _res.get("success"):
                        st.session_state[f"{session_key}_result"] = _res
                        st.rerun()
                    elif "401" in str(_res.get("error", "")):
                        # access_token 만료 → refresh 시도
                        _rt = load_refresh_token()
                        if _rt:
                            _refreshed = refresh_access_token(_rt)
                            if "access_token" in _refreshed:
                                save_tokens(
                                    _refreshed["access_token"],
                                    _refreshed.get("refresh_token", _rt),
                                )
                                _res2 = send_memo(
                                    _refreshed["access_token"],
                                    report_text,
                                    title=title,
                                    planner_info=planner_info,
                                )
                                if _res2.get("success"):
                                    st.session_state[f"{session_key}_result"] = _res2
                                    st.rerun()
                                else:
                                    st.error(f"재시도 실패: {_res2.get('error', '')}")
                            else:
                                clear_tokens()
                                st.warning("로그인이 만료되었습니다. 다시 로그인하세요.")
                                st.rerun()
                        else:
                            clear_tokens()
                            st.warning("로그인이 만료되었습니다. 다시 로그인하세요.")
                            st.rerun()
                    else:
                        st.error(f"전송 실패: {_res.get('error', '알 수 없는 오류')}")

            if _logout_btn:
                clear_tokens()
                st.session_state.pop(f"{session_key}_result", None)
                st.rerun()

    if compact:
        import streamlit as st
        with st.expander("📩 카카오톡 나에게 보내기", expanded=False):
            _inner()
    else:
        _inner()
