# crm_app.py — Goldkey AI Masters CRM 2026
"""
[GP 마스터-그림자 Phase 3] 초경량 현장 기동대 CRM
- 복잡한 보험 계산식/정밀 상담 로직 없음
- 공통 모듈(shared_components.py) import 전용
- 역할: AI 아침 브리핑 · 고객 리스트 · 일정 · 딥링크 발사대

[동시 구동 방법]
  본 앱(HQ):  streamlit run app.py     --server.port 8501
  CRM 앱:    streamlit run crm_app.py --server.port 8502
  접속 URL:  http://localhost:8501  (HQ)
             http://localhost:8502  (CRM)
"""

import streamlit as st
import datetime
import urllib.parse
import os

# ── [Phase 1] 공통 모듈 import ────────────────────────────────────────────────
from shared_components import (
    CUSTOMER_SCHEMA,
    TIER_META,
    STATUS_META,
    customer_form,
    customer_input_form,
    render_customer_list,
    build_deeplink_to_hq,
    build_sso_redirect,
    HQ_APP_URL,
    CRM_APP_URL,
    get_env_secret,
    get_clean_phone,
    decrypt_pii,
    render_auth_screen as _sc_render_auth_screen,
    verify_sso_token as _sc_verify_sso_token,
    notify_admin_member_error as _sc_notify_admin_error,
    render_member_emergency_btn as _sc_emergency_btn,
    _NIBO_CONSENT_HTML as _crm_nibo_html,
    render_security_sidebar as _sc_render_security_sidebar,
)

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="골드키 CRM — 고객상담 앱",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── [GP-SEC §14] CRM 사이드바 보안 기준 준수 ──────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;padding:8px 0 4px;'>"
        "📱 골드키 CRM — 고객상담 앱</div>",
        unsafe_allow_html=True,
    )
    try:
        _sc_render_security_sidebar()
    except Exception:
        pass

# ── [GP-84 §11] 전역 CSS — Premium Design System v3 (모바일 우선) ──────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Noto+Sans+KR:wght@400;500;700;900&display=swap');

/* ══════════════════════════════════════════════════════
   [CRM] GP-84 Premium Design System v3 — Mobile-First
   Apple HIG · Inter Font · Indigo Accent · Glassmorphism
══════════════════════════════════════════════════════ */

/* §2-A GK RFS v1.0 — 반응형 폰트 스케일 (Mobile-First) */
html { font-size: 16px; }
@media (min-width: 601px) and (max-width: 1024px) {
  html { font-size: 18.4px; }
}
@media (max-width: 600px) {
  html { font-size: 17px; }
  [data-testid="stButton"] button,
  [data-testid="stFormSubmitButton"] button {
    min-height: 44px !important;
    font-weight: 800 !important;
  }
  [data-testid="stTextInput"] input,
  [data-testid="stTextArea"] textarea {
    font-size: 1rem !important;
  }
}

/* §2-B 파스텔 3색 그라디언트 배경 (GP-84 절대 규정) */
html, body {
  background: linear-gradient(145deg, #eef2ff 0%, #f8faff 40%, #f0fdf8 100%) !important;
  background-attachment: fixed !important;
  font-family: 'Inter', 'Noto Sans KR', 'Apple SD Gothic Neo', -apple-system, sans-serif !important;
  -webkit-font-smoothing: antialiased !important;
  letter-spacing: -0.01em !important;
}
[data-testid="stApp"], .stApp,
[data-testid="stAppViewContainer"],
section[data-testid="stMain"],
.main, .block-container {
  background: transparent !important;
}

/* §5-C CRM 콘테이너 전체 화면 활용 */
.block-container {
  max-width: 100% !important;
  padding-top: 12px !important;
  padding-left: 6px !important;
  padding-right: 6px !important;
  padding-bottom: 80px !important;
}
div[data-testid="stMainBlockContainer"] { padding-top: 0.75rem !important; }

/* §5-A Glassmorphism 카드 */
.gk-card {
  background: rgba(255,255,255,0.80) !important;
  backdrop-filter: blur(16px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
  border: 1px solid rgba(99,102,241,0.14) !important;
  border-radius: 16px !important;
  padding: 16px !important;
  margin-bottom: 12px !important;
  box-shadow: 0 4px 24px rgba(99,102,241,0.08), 0 1px 4px rgba(0,0,0,0.04) !important;
  transition: box-shadow 0.22s ease, transform 0.22s ease !important;
}
.gk-card:hover {
  box-shadow: 0 8px 32px rgba(99,102,241,0.14) !important;
  transform: translateY(-2px) !important;
}

/* §3-B 섹션 타이틀 — Inter 800 */
.gk-section-title {
  font-family: 'Inter', 'Noto Sans KR', sans-serif !important;
  font-size: 1.05rem !important;
  font-weight: 800 !important;
  letter-spacing: -0.02em !important;
  color: #0F172A !important;
  border-bottom: 2px solid rgba(99,102,241,0.25) !important;
  padding-bottom: 6px !important;
  margin-bottom: 12px !important;
}

/* 배지 스타일 */
.gk-badge {
  display: inline-block !important;
  font-size: 0.72rem !important;
  font-weight: 700 !important;
  padding: 2px 8px !important;
  border-radius: 6px !important;
  border: 1.5px solid currentColor !important;
  letter-spacing: 0.02em !important;
}

/* 딥링크 버튼 — GP-84 §4-A Primary 계열 */
.gk-deeplink-btn {
  display: inline-block !important;
  background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 8px 16px !important;
  font-size: 0.85rem !important;
  font-weight: 700 !important;
  text-decoration: none !important;
  margin-top: 8px !important;
  box-shadow: 0 3px 10px rgba(99,102,241,0.35) !important;
  transition: box-shadow 0.2s ease, transform 0.2s ease !important;
}
.gk-deeplink-btn:hover {
  box-shadow: 0 6px 18px rgba(99,102,241,0.50) !important;
  transform: translateY(-1px) !important;
}

/* §4-A 버튼 전역 — 48px 터치 타겟 (Apple HIG 44pt) */
.stButton > button {
  min-height: 48px !important;
  font-family: 'Inter', 'Noto Sans KR', sans-serif !important;
  font-size: 0.95rem !important;
  font-weight: 700 !important;
  border-radius: 12px !important;
  letter-spacing: -0.01em !important;
  transition: background 0.22s ease, box-shadow 0.22s ease, transform 0.3s cubic-bezier(0.34,1.56,0.64,1) !important;
}
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #4F46E5 0%, #6366F1 50%, #818CF8 100%) !important;
  color: #ffffff !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(99,102,241,0.40) !important;
}
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 8px 22px rgba(99,102,241,0.55) !important;
  transform: translateY(-2px) !important;
}
.stButton > button:not([kind]) {
  background: rgba(255,255,255,0.82) !important;
  backdrop-filter: blur(10px) !important;
  color: #1e293b !important;
  border: 1.5px solid rgba(99,102,241,0.18) !important;
}
.stButton > button:not([kind]):hover {
  background: rgba(238,242,255,0.95) !important;
  border-color: #6366F1 !important;
  color: #4F46E5 !important;
}
.stButton > button:active {
  transform: scale(0.96) !important;
}

/* §7 입력 필드 — 포커스 링 (GP-84 §7) */
input[type="text"], input[type="password"],
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
  background: rgba(255,255,255,0.90) !important;
  border: 1.5px solid rgba(99,102,241,0.22) !important;
  border-radius: 10px !important;
  font-family: 'Inter', 'Noto Sans KR', sans-serif !important;
  color: #0F172A !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
  outline: none !important;
}
input[type="text"]:focus, input[type="password"]:focus,
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border: 1.5px solid #6366F1 !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
  outline: none !important;
}

/* 메트릭 카드 (GP-84 §6) */
[data-testid="stMetric"] {
  background: rgba(255,255,255,0.78) !important;
  border: 1px solid rgba(99,102,241,0.12) !important;
  border-radius: 14px !important;
  padding: 14px 16px !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.5rem !important; font-weight: 800 !important;
  color: #4F46E5 !important; letter-spacing: -0.03em !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.75rem !important; font-weight: 600 !important;
  color: #64748B !important; text-transform: uppercase !important;
  letter-spacing: 0.03em !important;
}

/* 알림 박스 */
.stAlert { background: rgba(255,255,255,0.82) !important; border-radius: 12px !important; }

/* ================================================================
   [신규 전면 개정] GP 제2장 제6조~제11조 — Bright Corporate UI/UX System
   2026-03-18 개정 · 기존 제6~11조 전면 폐기 대체 · 후위 !important 강제 적용
================================================================ */

/* ── 제6조 [Bright Corporate 스타일] ─────────────────────────── */
html, body {
  background: #FFFFFF !important;
  background-image: none !important;
  background-attachment: initial !important;
}
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
.stApp,
section[data-testid="stMain"],
section[data-testid="stMain"] > div,
.main,
.main .block-container,
.block-container {
  background: #F8F9FA !important;
  background-image: none !important;
  background-attachment: initial !important;
}
p, li, span {
  color: #333333 !important;
  text-shadow: none !important;
}

/* ── 제7조 [프리미엄 그라데이션 박스 — Bright Cyan] ────────────── */
.premium-gradient-box {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
  border-radius: 15px !important;
  box-shadow: 0 8px 20px rgba(0, 192, 255, 0.2) !important;
  padding: 16px 20px !important;
}
.premium-gradient-box,
.premium-gradient-box * {
  color: #FFFFFF !important;
  text-shadow: none !important;
}

/* ── 제8조 [레드 얼럿 시스템] ──────────────────────────────────── */
.red-alert-box {
  border: 1.5px solid #FF4B4B !important;
  background-color: rgba(255, 75, 75, 0.05) !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
}
.red-alert-box,
.red-alert-box * {
  color: #FF4B4B !important;
  text-shadow: none !important;
}
.red-text {
  color: #FF4B4B !important;
  text-shadow: none !important;
}

/* ── 제9조 [공간 구획 및 경계] ──────────────────────────────────── */
[data-testid="stExpander"],
[data-testid="stForm"] {
  border: 1px solid #E0E0E0 !important;
  border-radius: 10px !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] > details > summary {
  border: 1px solid #E0E0E0 !important;
  background: #FFFFFF !important;
  backdrop-filter: none !important;
}
[data-testid="stVerticalBlock"] { margin-bottom: 6px !important; }

/* ── 제10조 [전역 컴팩트 레이아웃] ─────────────────────────────── */
[data-testid="stExpanderDetails"] p,
[data-testid="stExpanderDetails"] li {
  line-height: 1.25 !important;
  letter-spacing: -0.02em !important;
}

/* ── 제11조 [반응형 타이포그래피 — Fluid Typography] ────────────── */
p, li, span {
  font-size: clamp(13px, 1.2vw + 10px, 16px) !important;
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
}
h1 { font-size: clamp(20px, 3vw + 12px, 28px) !important; word-break: keep-all !important; overflow-wrap: break-word !important; }
h2 { font-size: clamp(18px, 2.5vw + 10px, 24px) !important; word-break: keep-all !important; overflow-wrap: break-word !important; }
h3 { font-size: clamp(16px, 2vw + 10px, 20px) !important; word-break: keep-all !important; overflow-wrap: break-word !important; }
[data-testid="stExpanderDetails"] p,
[data-testid="stExpanderDetails"] li,
[data-testid="stExpanderDetails"] span {
  font-size: clamp(12px, 1vw + 10px, 14px) !important;
}
*, *::before, *::after {
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# [Phase 2] SSO 인증 처리
# 세션 없으면 모 앱으로 자동 리다이렉트 (?return_to=crm_url)
# ══════════════════════════════════════════════════════════════════════════════
# ── 환경 감지: 로컬 개발 vs 프로덕션 ──────────────────────────────────────────
_IS_LOCAL = (
    os.environ.get("STREAMLIT_ENV", "") == "local"
    or get_env_secret("ENV", "") == "local"
    or os.environ.get("GAE_ENV", "") == ""
    and not os.environ.get("K_SERVICE", "")  # Cloud Run 환경변수 없으면 로컬
)
CRM_URL = get_env_secret("CRM_URL", CRM_APP_URL)

def _check_sso_token() -> bool:
    """[GP-SEC §2] URL에서 auth_token + user_id 수신 → HMAC 검증 → 세션 설정."""
    _auth_token = st.query_params.get("auth_token", "")
    _user_id    = st.query_params.get("user_id", "")
    if _auth_token and _user_id:
        _valid = False
        try:
            _valid = _sc_verify_sso_token(_auth_token, _user_id)
        except Exception:
            _valid = bool(_auth_token)
        if _valid:
            st.session_state["crm_authenticated"] = True
            st.session_state["crm_user_id"]       = _user_id
            st.session_state["crm_user_name"]     = st.session_state.get("crm_user_name", "설계사")
            st.session_state["crm_role"]          = "agent"
            st.session_state["crm_token"]         = _auth_token
            st.query_params.clear()  # SSO 토큰 수신 즉시 URL에서 삭제
            return True
    return False

def _is_authenticated() -> bool:
    return st.session_state.get("crm_authenticated", False)

# SSO 토큰 수신 처리
if _check_sso_token():
    st.rerun()

# ── [GP-SEC §2] 미인증 처리 — 자체 로그인 화면 독립 렌더링 ─────────────────────
if not _is_authenticated():
    # ── 아바타 로드 (assets/goldkey_ai_avatar.jpg) ───────────────────
    import base64 as _b64av
    _av_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "goldkey_ai_avatar.jpg")
    _crm_av_src = ""
    try:
        if os.path.exists(_av_path):
            with open(_av_path, "rb") as _f:
                _crm_av_src = "data:image/jpeg;base64," + _b64av.b64encode(_f.read()).decode()
    except Exception:
        pass
    _crm_av_html = (
        f'<img src="{_crm_av_src}" width="100" height="100" loading="eager"'
        ' style="border-radius:50%;border:4px solid #D4AF37;'
        'box-shadow:0 4px 18px rgba(212,175,55,0.4);object-fit:cover;'
        'display:block;margin:0 auto 12px auto;" />'
        if _crm_av_src else
        '<div style="width:100px;height:100px;border-radius:50%;'
        'background:linear-gradient(135deg,#1e3a8a,#D4AF37);'
        'margin:0 auto 12px auto;border:4px solid #D4AF37;"></div>'
    )
    _crm_c1, _crm_c2, _crm_c3 = st.columns([0.01, 0.98, 0.01])
    with _crm_c2:
        st.markdown(
            f"<div style='text-align:center;padding:24px 0 8px;'>"
            f"{_crm_av_html}"
            "<div style='font-size:1.6rem;font-weight:900;color:#1e3a8a;margin-bottom:3px;'>"
            "🏆 Goldkey AI Masters 2026</div>"
            "<div style='font-size:1.05rem;font-weight:900;color:#374151;margin-bottom:14px;'>"
            "📱 골드키 CRM — 고객상담 앱</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        # ── [GP-SEC §5] 공통 약관 동의 UI (필수동의 상단, 파스텔 톤) ────────
        if st.session_state.pop("_crm_logout_success", False):
            st.success("✅ 안전하게 로그아웃되었습니다. 모든 임시 세션 정보가 보안 파기되었습니다.")
        _crm_agreed = _sc_render_auth_screen(
            app_name="Goldkey AI Masters 2026",
            app_icon="🏆",
            terms_agree_key="_crm_terms_agreed",
            show_header=False,
            show_terms_scroll=False,
            show_nibo_box=False,
            show_checkboxes=True,
            consent_header_text="📋 필수동의 (아래 항목 동의해 주세요)",
            consent_header_bg="#dbeafe",
            consent_header_fg="#1e3a8a",
        )

        if _crm_agreed:
            # ── [GP-SEC §1] 이름 + 연락처 직접 로그인 (HQ와 동일 방식) ─────
            import hashlib as _hl
            _crm_lp = st.session_state.get("_crm_login_phase", "A")
            if _crm_lp == "A":
                with st.form("crm_direct_login"):
                    _crm_name_in    = st.text_input("👤 이름", placeholder="가입 시 등록한 이름",
                                                    label_visibility="collapsed", key="crm_login_name")
                    _crm_contact_in = st.text_input("📱 연락처", type="password",
                                                    placeholder="연락처 (숫자만, - 제외)",
                                                    label_visibility="collapsed", key="crm_login_contact")
                    _crm_login_btn  = st.form_submit_button("🔐 로그인",
                                                             use_container_width=True, type="primary")
                if _crm_login_btn:
                    _cn = (_crm_name_in    or "").strip()
                    _cc = (_crm_contact_in or "").strip()
                    # ── [GP-SEC §1] 관리자 로그인 — HQ 동일: ADMIN_CODE/MASTER_CODE 우선, SHA-256 폴백 ──
                    import hashlib as _hl_adm
                    _env_admin_code  = get_env_secret("ADMIN_CODE", "")
                    _env_master_code = get_env_secret("MASTER_CODE", "")
                    _adm_default_hash = _hl_adm.sha256(b"kgagold6803").hexdigest()
                    _adm_pw_hash      = get_env_secret("CRM_ADMIN_PW_HASH", _adm_default_hash)
                    _adm_input_hash   = _hl_adm.sha256((_cc or "").encode()).hexdigest()
                    _is_admin_name    = _cn.lower() in ("admin", "이세윤")
                    _is_admin_auth    = False
                    if _is_admin_name:
                        if _env_admin_code and _cc == _env_admin_code:
                            _is_admin_auth = True       # Track A: ADMIN_CODE 평문 (HQ와 동일)
                        elif _env_master_code and _cc == _env_master_code:
                            _is_admin_auth = True       # Track B: MASTER_CODE 평문
                        elif _adm_input_hash == _adm_pw_hash:
                            _is_admin_auth = True       # Track C: SHA-256 해시 폴백
                    if _is_admin_auth:
                        st.session_state["crm_authenticated"] = True
                        st.session_state["crm_user_id"]       = "admin"
                        st.session_state["crm_user_name"]     = "관리자"
                        st.session_state["crm_role"]          = "admin"
                        st.session_state["crm_token"]         = "admin-direct"
                        st.session_state.pop("_crm_login_phase", None)
                        st.rerun()
                    elif not _cn or len(_cn) < 2:
                        st.error("⚠️ 이름을 2자 이상 입력해 주세요.")
                    elif not _cc:
                        st.error("⚠️ 연락처를 입력해 주세요.")
                    else:
                        # Supabase members 테이블 조회
                        _crm_sb = None
                        try:
                            from supabase import create_client as _cc_sb
                            _crm_sb = _cc_sb(
                                get_env_secret("SUPABASE_URL", ""),
                                get_env_secret("SUPABASE_SERVICE_ROLE_KEY",
                                               get_env_secret("SUPABASE_KEY", "")),
                            )
                        except Exception:
                            pass
                        _crm_member = None
                        if _crm_sb:
                            try:
                                _resp = _crm_sb.table("gk_members").select("*") \
                                    .eq("name", _cn).execute()
                                _rows = _resp.data or []
                                if _rows:
                                    _crm_member = _rows[0]
                            except Exception:
                                pass
                        if _crm_member is None:
                            st.error("❌ 등록되지 않은 이름입니다. HQ 앱에서 먼저 가입해 주세요.")
                        else:
                            # [GP-SEC §1][GP-회원관리 §연락처표준] 4-track 연락처 검증
                            _clean_cc = get_clean_phone(_cc)
                            _input_hash = _hl.sha256(_clean_cc.encode()).hexdigest()
                            _m_pin      = _crm_member.get("pin_hash", "")
                            _m_contact  = _crm_member.get("contact", "")
                            # Track 1: pin_hash vs 입력 해시
                            _pin_ok     = bool(_m_pin) and (_m_pin == _input_hash)
                            # Track 2: contact(SHA-256) vs 입력 해시
                            _chash_ok   = bool(_m_contact) and (_m_contact == _input_hash)
                            # Track 3: contact(Fernet) 복호화 비교 — 키 파생 폴백 포함
                            _fernet_ok  = False
                            if not _pin_ok and not _chash_ok and _m_contact:
                                try:
                                    import base64 as _b64, hashlib as _hsha
                                    from cryptography.fernet import Fernet as _F
                                    _fk = get_env_secret("FERNET_KEY", "")
                                    if not _fk:  # [오류5 수정] ENCRYPTION_KEY 기반 자동 파생
                                        _seed = get_env_secret("ENCRYPTION_KEY", "gk_token_secret_2026")
                                        _fk = _b64.urlsafe_b64encode(_hsha.sha256(_seed.encode()).digest()).decode()
                                    _dec = _F(_fk.encode() if isinstance(_fk, str) else _fk).decrypt(_m_contact.encode()).decode()
                                    _fernet_ok = (_dec == _clean_cc) or (_dec == _cc)
                                except Exception:
                                    pass
                            # Track 4: Legacy — 하이픈 포함 입력으로 가입한 기존 회원 복구
                            _legacy_ok = False
                            if not _pin_ok and not _chash_ok and not _fernet_ok:
                                _hyp = f"{_clean_cc[:3]}-{_clean_cc[3:7]}-{_clean_cc[7:]}" if len(_clean_cc) == 11 else \
                                       (f"{_clean_cc[:3]}-{_clean_cc[3:6]}-{_clean_cc[6:]}" if len(_clean_cc) == 10 else "")
                                if _hyp:
                                    _hyp_hash = _hl.sha256(_hyp.encode()).hexdigest()
                                    _legacy_ok = (bool(_m_pin) and _m_pin == _hyp_hash) or \
                                                 (bool(_m_contact) and _m_contact == _hyp_hash)
                            if _pin_ok or _chash_ok or _fernet_ok or _legacy_ok:
                                # [GP-회원관리 §연락처표준 §7-SU] Track 4 성공 시 Silent Update
                                if _legacy_ok and not (_pin_ok or _chash_ok or _fernet_ok):
                                    try:
                                        _new_h = _hl.sha256(_clean_cc.encode()).hexdigest()
                                        _crm_sb.table("gk_members").update({"pin_hash": _new_h}).eq("name", _cn).execute()
                                    except Exception:
                                        pass
                                _uid = _crm_member.get("user_id", _cn)
                                st.session_state["crm_authenticated"] = True
                                st.session_state["crm_user_id"]       = _uid
                                st.session_state["crm_user_name"]     = _cn
                                st.session_state["crm_role"]          = "agent"
                                st.session_state["crm_token"]         = "direct-login"
                                st.session_state.pop("_crm_login_phase", None)
                                st.rerun()
                            else:
                                st.error("❌ 연락처가 일치하지 않습니다.")
                                try:
                                    _sc_notify_admin_error(_cn, "AUTH_MISMATCH", "CRM")
                                except Exception:
                                    pass
        # ── 하단 통합 안내문 (이용약관 + 내보험다보여) ───────────────────────────
        st.markdown(
            "<hr style='margin:24px 0 14px;border:1px solid #e5e7eb;'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='background:#eff6ff;border-radius:8px 8px 0 0;"
            "padding:7px 14px;margin-bottom:0;'>"
            "<span style='font-size:0.85rem;font-weight:900;color:#1e3a8a;'>"
            "📋 Goldkey AI Masters 2026 이용약관 · 내보험다보여(신용정보법 제32조) 통합 안내문</span></div>",
            unsafe_allow_html=True,
        )
        _sc_render_auth_screen(
            app_name="Goldkey AI Masters 2026",
            app_icon="🏆",
            terms_agree_key="_crm_terms_view",
            show_header=False,
            show_terms_scroll=True,
            show_nibo_box=False,
            show_checkboxes=False,
        )
        st.markdown(
            "<div style='background:#fffbeb;border:1px dashed #f59e0b;"
            "border-radius:0 0 8px 8px;padding:12px 14px;'>"
            "<div style='font-size:0.82rem;font-weight:900;color:#92400e;margin-bottom:6px;'>"
            "🔐 내보험다보여 연동 — 신용정보의 이용 및 보호에 관한 법률 제32조 안내</div>"
            "<div style='font-size:0.75rem;color:#78350f;line-height:1.85;'>"
            "• <b>수집:</b> 보험사명·상품명·담보내역·계약상태 (신용정보원 등록 데이터)<br>"
            "• <b>목적:</b> AI 트리니티 엔진 — 보장 적정성 분석 및 실질 생계비 기반 리모델링<br>"
            "• <b>보유:</b> 분석 완료 후 30일 경과 시 자동 파기 (리포트 이력 최대 3년 암호화)<br>"
            "• <b>인증정보:</b> 데이터 추출 후 <b>즉시 메모리 파기</b> — 서버 저장 절대 불가<br>"
            "• <b>미동의 시:</b> AI 증권분석 · 트리니티 리포트 기능 비활성화"
            "</div></div>",
            unsafe_allow_html=True,
        )
        with st.popover("📋 신용정보의 이용 및 보호에 관한 법률 제32조 안내문 전문 보기", use_container_width=True):
            st.markdown(
                "<div style='font-size:0.78rem;color:#92400e;font-weight:700;"
                "margin-bottom:6px;'>📌 신용정보의 이용 및 보호에 관한 법률 제32조 적용</div>",
                unsafe_allow_html=True,
            )
            st.markdown(_crm_nibo_html, unsafe_allow_html=True)
    # ── 앱 바닥 — 관리자 로그인 · 오류신고 (미인증 사용자도 접근 가능) ────────
    try:
        _sc_emergency_btn(app_name="CRM", key_prefix="crm_emg_bottom", show_admin_login=True)
    except Exception:
        pass
    st.stop()

# ── 인증 완료 후 메인 ─────────────────────────────────────────────────────────
_user_id   = st.session_state.get("crm_user_id", "")
_user_name = st.session_state.get("crm_user_name", "설계사")
_token     = st.session_state.get("crm_token", "")

# ── Supabase 클라이언트 (lazy init) ────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _get_supabase():
    try:
        from supabase import create_client
        url = get_env_secret("SUPABASE_URL", "")
        key = get_env_secret("SUPABASE_SERVICE_ROLE_KEY",
                              get_env_secret("SUPABASE_KEY", ""))
        return create_client(url, key)
    except Exception:
        return None

_sb = _get_supabase()

# ── 고객 목록 로드 ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def _load_customers(agent_id: str, query: str = "") -> list:
    if not _sb:
        return []
    try:
        q = _sb.table("gk_people").select("*").eq("is_deleted", False)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        if query:
            q = q.ilike("name", f"%{query}%")
        q = q.order("management_tier").order("name")
        resp = q.execute()
        return resp.data or []
    except Exception:
        return []

# ── 일정 로드 ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def _load_schedules_today(agent_id: str) -> list:
    if not _sb:
        return []
    try:
        today = datetime.date.today().isoformat()
        resp = (
            _sb.table("gk_schedules")
            .select("*")
            .eq("is_deleted", False)
            .eq("agent_id", agent_id)
            .gte("date", today)
            .lte("date", today)
            .order("start_time")
            .execute()
        )
        return resp.data or []
    except Exception:
        return []

# ══════════════════════════════════════════════════════════════════════════════
# 헤더
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);padding:14px 20px;
  border-radius:10px;display:flex;align-items:center;justify-content:space-between;
  margin-bottom:16px;border:1px dashed #3b82f6;">
  <div>
    <span style="font-size:1.3rem;font-weight:900;color:#1e3a8a;">📱 골드키 CRM</span>
    <span style="font-size:0.78rem;color:#2563eb;margin-left:10px;">고객상담 앱</span>
  </div>
  <div style="font-size:0.82rem;color:#374151;font-weight:700;">{_user_name} 설계사</div>
</div>
""", unsafe_allow_html=True)
# ── [GP-SEC] 로그아웃 버튼 — 세션 완전 초기화 (공유 디바이스 보호) ──────────────
_hdr_c1, _hdr_c2 = st.columns([6, 1])
with _hdr_c1:
    st.markdown(
        f"<div style='font-size:0.78rem;color:#6b7280;padding:2px 0;'>"
        f"🔒 {_user_name} 로그인 중 &nbsp;|&nbsp; "
        f"<span style='color:#f59e0b;'>nibo 동의: {'✅' if st.session_state.get('nibo_consent_agreed') else '⬜'}</span>"
        "</div>",
        unsafe_allow_html=True,
    )
with _hdr_c2:
    if st.button("🔒 로그아웃", key="crm_logout_btn", use_container_width=True):
        try:
            _sb_lo = _get_supabase()
            if _sb_lo:
                _sb_lo.auth.sign_out()
        except Exception:
            pass
        st.session_state.clear()
        st.session_state["_crm_logout_success"] = True
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# [GP SPA §0] 아웃룩 컴포넌트 + DB 유틸 로드 (st.tabs 금지)
# ══════════════════════════════════════════════════════════════════════════════
try:
    from components import (
        inject_outlook_css,
        render_spa_nav,
        render_outlook_customer_list,
        render_mini_calendar,
        손보사_standard_form,
    )
    from db_utils import (
        load_schedules         as _du_schedules,
        load_schedules_range   as _du_range,
        save_schedule          as _du_save_sched,
    )
    inject_outlook_css()
    _OUTLOOK_OK = True
except Exception:
    _OUTLOOK_OK = False

# ══════════════════════════════════════════════════════════════════════════════
# [GP SPA §1] 상태 초기화
# ══════════════════════════════════════════════════════════════════════════════
if "crm_spa_mode"     not in st.session_state: st.session_state["crm_spa_mode"]     = "list"
if "crm_selected_pid" not in st.session_state: st.session_state["crm_selected_pid"] = ""
if "crm_spa_screen"   not in st.session_state: st.session_state["crm_spa_screen"]   = "contact"

_spa_mode = st.session_state.get("crm_spa_mode",    "list")
_sel_pid  = st.session_state.get("crm_selected_pid", "")
_sel_cust: dict | None = None
if _sel_pid:
    _sel_cust = next((_c for _c in _load_customers(_user_id) if _c.get("person_id") == _sel_pid), None)

# ══════════════════════════════════════════════════════════════════════════════
# [GP SPA §2] MODE: LIST — 아웃룩 고객 목록
# ══════════════════════════════════════════════════════════════════════════════
if _spa_mode == "list":
    st.markdown(
        "<div style='background:#F8FBFA;padding:10px 14px;border-radius:10px;"
        "border:1px dashed #000;margin-bottom:12px;'>"
        "<span style='font-size:1.05rem;font-weight:900;color:#1e3a8a;'>👥 전체 고객 대시보드</span>"
        "<span style='font-size:0.78rem;color:#64748b;margin-left:10px;'>고객 선택 → 6대 메뉴</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    _sr_c1, _sr_c2 = st.columns([5, 1])
    with _sr_c1:
        _search_q = st.text_input("🔍 고객 이름 검색", placeholder="이름 입력...",
                                  key="spa_search", label_visibility="collapsed")
    with _sr_c2:
        if st.button("➕ 신규 등록", use_container_width=True, key="spa_add_btn"):
            st.session_state["spa_add_form"] = True

    _fc1, _fc2, _fc3 = st.columns(3)
    with _fc1:
        _tier_f = st.selectbox("등급", ["전체", "VVIP(1)", "핵심(2)", "일반(3)"],
                               key="spa_tier_f")
    with _fc2:
        _mo_f = st.number_input("만기월 (0=전체)", 0, 12, 0, key="spa_mo_f")
    with _fc3:
        _stat_f = st.selectbox("상태", ["전체", "가망", "진행중", "계약", "종료"],
                               key="spa_stat_f")

    _all_custs = _load_customers(_user_id, _search_q or "")
    _tier_map_r  = {"VVIP(1)": 1, "핵심(2)": 2, "일반(3)": 3}
    _stat_map_r  = {"가망": "potential", "진행중": "active", "계약": "contracted", "종료": "closed"}
    if _tier_f != "전체": _all_custs = [c for c in _all_custs if c.get("management_tier") == _tier_map_r.get(_tier_f)]
    if _mo_f:             _all_custs = [c for c in _all_custs if c.get("auto_renewal_month") == _mo_f or c.get("fire_renewal_month") == _mo_f]
    if _stat_f != "전체": _all_custs = [c for c in _all_custs if c.get("status") == _stat_map_r.get(_stat_f, "")]

    st.caption(f"📋 총 {len(_all_custs)}명")

    if st.session_state.get("spa_add_form"):
        with st.expander("✏️ 신규 고객 등록", expanded=True):
            if _OUTLOOK_OK:
                _new_data = 손보사_standard_form(None, key_prefix="spa_new")
            else:
                _new_data = customer_form(None, key_prefix="spa_new")
            _nc1, _nc2 = st.columns(2)
            with _nc1:
                if st.button("💾 저장", key="spa_new_save", type="primary", use_container_width=True):
                    try:
                        customer_input_form(_new_data, _user_id, _sb)
                        st.success("✅ 등록 완료!")
                        st.session_state["spa_add_form"] = False
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as _ne:
                        st.error(f"저장 오류: {_ne}")
            with _nc2:
                if st.button("✕ 취소", key="spa_new_cancel", use_container_width=True):
                    st.session_state["spa_add_form"] = False
                    st.rerun()

    if _OUTLOOK_OK:
        render_outlook_customer_list(_all_custs, _sel_pid)
    else:
        render_customer_list(_all_custs, show_deeplink=True, agent_tab="t3")

# ══════════════════════════════════════════════════════════════════════════════
# [GP SPA §3] MODE: CUSTOMER — 6대 SPA 화면
# ══════════════════════════════════════════════════════════════════════════════
elif _spa_mode == "customer":
    _spa_screen = st.session_state.get("crm_spa_screen", "contact")

    if _sel_cust:
        _cn = _sel_cust.get("name", "")
        _ct = _sel_cust.get("management_tier", 3)
        _tm = TIER_META.get(_ct, TIER_META[3])
        st.markdown(
            f"<div style='background:#F8FBFA;padding:8px 14px;border-radius:10px;"
            f"border:1px dashed #000;margin-bottom:8px;display:flex;align-items:center;gap:10px;'>"
            f"<span style='font-size:1.1rem;font-weight:900;color:#1e293b;'>{_cn}</span>"
            f"<span style='font-size:0.72rem;font-weight:900;padding:2px 8px;border-radius:10px;"
            f"background:{_tm['bg']};color:{_tm['color']};'>{_tm['icon']} {_tm['label']}</span>"
            f"<span style='font-size:0.75rem;color:#64748b;margin-left:auto;'>{_sel_cust.get('job','')}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if _OUTLOOK_OK:
        render_spa_nav(_spa_screen)
    else:
        _scr_opts = {"👥 연락처 상세": "contact", "📅 스케줄": "schedule",
                     "🌐 내보험다보여": "nibo",  "📊 증권분석": "analysis",
                     "🤖 AI 브리핑": "ai_brief", "💬 카카오 발송": "kakao"}
        _scr_label = st.selectbox("화면 선택", list(_scr_opts.keys()), key="spa_screen_sel")
        if _scr_opts[_scr_label] != _spa_screen:
            st.session_state["crm_spa_screen"] = _scr_opts[_scr_label]
            st.rerun()
        _bk, _ = st.columns([2, 8])
        with _bk:
            if st.button("🔙 목록으로", key="spa_back_fb"):
                st.session_state["crm_spa_mode"] = "list"
                st.session_state["crm_selected_pid"] = ""
                st.rerun()

    # ── SCREEN 1: 👥 연락처 상세 ────────────────────────────────────────────
    if _spa_screen == "contact":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "👥 연락처 상세 — 손보사 표준 정보 관리</div>",
            unsafe_allow_html=True,
        )
        _edit_key = f"spa_edit_{_sel_pid}"
        if st.session_state.get(_edit_key):
            if _OUTLOOK_OK:
                _upd_data = 손보사_standard_form(_sel_cust, key_prefix=f"spa_cf_{_sel_pid}")
            else:
                _upd_data = customer_form(_sel_cust, key_prefix=f"spa_cf_{_sel_pid}")
            _sv1, _sv2 = st.columns(2)
            with _sv1:
                if st.button("💾 저장", key=f"spa_save_{_sel_pid}", type="primary", use_container_width=True):
                    try:
                        customer_input_form(_upd_data, _user_id, _sb)
                        st.success("✅ 저장 완료!")
                        st.session_state[_edit_key] = False
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as _ue:
                        st.error(f"저장 오류: {_ue}")
            with _sv2:
                if st.button("취소", key=f"spa_cancel_{_sel_pid}", use_container_width=True):
                    st.session_state[_edit_key] = False
                    st.rerun()
        else:
            if _sel_cust:
                _lbl_map = {"potential": "가망", "active": "진행중",
                            "contracted": "계약", "closed": "종료"}
                _d1, _d2 = st.columns(2)
                _flds_l = [("이름", "name"), ("연락처", "_ct_disp"), ("생년월일", "birth_date"), ("성별", "gender")]
                _flds_r = [("직업", "job"), ("주소", "address"), ("등급", "_tier_lbl"), ("상태", "_stat_lbl")]
                with _d1:
                    for _lbl, _fk in _flds_l:
                        if _fk == "_ct_disp":
                            _fv = decrypt_pii(_sel_cust.get("contact", ""))
                        elif _fk == "_tier_lbl":
                            _fv = TIER_META.get(_sel_cust.get("management_tier", 3), TIER_META[3])["label"]
                        elif _fk == "_stat_lbl":
                            _fv = _lbl_map.get(_sel_cust.get("status", ""), "-")
                        else:
                            _fv = _sel_cust.get(_fk, "-") or "-"
                        st.markdown(
                            f"<div style='margin-bottom:10px;'>"
                            f"<div style='font-size:0.7rem;font-weight:700;color:#64748b;text-transform:uppercase;'>{_lbl}</div>"
                            f"<div style='font-size:0.9rem;color:#1e293b;font-weight:500;'>{_fv}</div></div>",
                            unsafe_allow_html=True,
                        )
                with _d2:
                    for _lbl, _fk in _flds_r:
                        if _fk == "_tier_lbl":
                            _fv = TIER_META.get(_sel_cust.get("management_tier", 3), TIER_META[3])["label"]
                        elif _fk == "_stat_lbl":
                            _fv = _lbl_map.get(_sel_cust.get("status", ""), "-")
                        else:
                            _fv = _sel_cust.get(_fk, "-") or "-"
                        st.markdown(
                            f"<div style='margin-bottom:10px;'>"
                            f"<div style='font-size:0.7rem;font-weight:700;color:#64748b;text-transform:uppercase;'>{_lbl}</div>"
                            f"<div style='font-size:0.9rem;color:#1e293b;font-weight:500;'>{_fv}</div></div>",
                            unsafe_allow_html=True,
                        )
                _sp_flags = []
                if _sel_cust.get("has_motorcycle"):      _sp_flags.append("🏍️ 이륜차")
                if _sel_cust.get("is_commercial_driver"): _sp_flags.append("🚛 유상운송")
                if _sel_cust.get("has_foreign_stay"):    _sp_flags.append("✈️ 해외장기체류")
                if _sp_flags:
                    st.markdown(
                        f"<div style='background:#fef3c7;border:1px dashed #f59e0b;border-radius:8px;"
                        f"padding:8px 12px;font-size:0.82rem;font-weight:900;color:#92400e;margin-top:8px;'>"
                        f"⚠️ 손보사 고지: {' · '.join(_sp_flags)}</div>",
                        unsafe_allow_html=True,
                    )
                _memo_v = _sel_cust.get("memo", "")
                if _memo_v:
                    st.markdown(
                        f"<div style='background:#FDFD96;border:1px dashed #d97706;border-radius:8px;"
                        f"padding:10px 14px;font-size:0.85rem;margin-top:10px;'>"
                        f"<b>📝 상담 메모</b><br>{_memo_v}</div>",
                        unsafe_allow_html=True,
                    )
                if st.button("✏️ 정보 수정", key=f"spa_edit_btn_{_sel_pid}", use_container_width=True):
                    st.session_state[_edit_key] = True
                    st.rerun()

    # ── SCREEN 2: 📅 스케줄 ─────────────────────────────────────────────────
    elif _spa_screen == "schedule":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "📅 스케줄 — 아웃룩 3분할 캘린더 뷰</div>",
            unsafe_allow_html=True,
        )
        if "spa_cal_ym" not in st.session_state:
            _td = datetime.date.today()
            st.session_state["spa_cal_ym"] = (_td.year, _td.month)
        _cal_yr, _cal_mo = st.session_state.get("spa_cal_ym", (datetime.date.today().year, datetime.date.today().month))
        if "spa_cal_sel" not in st.session_state:
            st.session_state["spa_cal_sel"] = datetime.date.today().isoformat()
        _sel_date = st.session_state.get("spa_cal_sel", datetime.date.today().isoformat())

        import calendar as _cal_mod
        _last_day_n = _cal_mod.monthrange(_cal_yr, _cal_mo)[1]
        _mo_start   = f"{_cal_yr}-{_cal_mo:02d}-01"
        _mo_end     = f"{_cal_yr}-{_cal_mo:02d}-{_last_day_n:02d}"
        try:
            _month_schs = _du_range(_user_id, _mo_start, _mo_end) if _OUTLOOK_OK else []
        except Exception:
            _month_schs = []
        _sched_dates = {s.get("date", "") for s in _month_schs}

        _cal_col, _list_col, _memo_col = st.columns([2, 3, 3])
        with _cal_col:
            st.markdown("<b style='font-size:0.82rem;'>📅 달력</b>", unsafe_allow_html=True)
            if _OUTLOOK_OK:
                _new_sel = render_mini_calendar(_cal_yr, _cal_mo, _sched_dates, _sel_date, session_key="spa_cal_sel")
                if _new_sel != _sel_date:
                    st.session_state["spa_cal_sel"] = _new_sel
                    st.rerun()
            else:
                _sel_dt = st.date_input("날짜 선택", value=datetime.date.fromisoformat(_sel_date),
                                        key="spa_cal_dt", label_visibility="collapsed")
                _sel_date = str(_sel_dt)
                st.session_state["spa_cal_sel"] = _sel_date

        with _list_col:
            st.markdown(f"<b style='font-size:0.82rem;'>🗓️ {_sel_date} 일정</b>", unsafe_allow_html=True)
            try:
                _day_schs = _du_schedules(_user_id, _sel_date) if _OUTLOOK_OK else (
                    _sb.table("gk_schedules").select("*, gk_people(name)")
                    .eq("is_deleted", False).eq("agent_id", _user_id)
                    .eq("date", _sel_date).order("start_time").execute().data or []
                ) if _sb else []
            except Exception:
                _day_schs = []
            if _day_schs:
                for _s in _day_schs:
                    _ci = {"consult": "💬", "appointment": "📌", "call": "📞", "other": "📋"}.get(_s.get("category", ""), "📋")
                    _pn = (_s.get("gk_people") or {}).get("name", "")
                    _pn_span   = (f' <span style="font-size:0.72rem;color:#6b7280;">({_pn})</span>' if _pn else "")
                    _memo_div  = (f'<div style="font-size:0.75rem;color:#64748b;margin-top:3px;">{_s.get("memo","")}</div>' if _s.get("memo") else "")
                    st.markdown(
                        f"<div style='background:#E6E6FA;border:1px solid #c4b5fd;border-radius:8px;"
                        f"padding:8px 12px;margin-bottom:6px;font-size:0.82rem;'>"
                        f"<span style='font-size:0.72rem;font-weight:700;color:#7c3aed;'>{_ci} {_s.get('start_time','')}</span>"
                        f"<b style='color:#3b0764;'> {_s.get('title','')}</b>"
                        f"{_pn_span}{_memo_div}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info(f"{_sel_date} 일정 없음")
            with st.expander("➕ 일정 추가", expanded=False):
                _nt1, _nt2 = st.columns(2)
                with _nt1:
                    _new_title = st.text_input("제목 *", key="spa_sched_title")
                    _new_time  = st.text_input("시간 (HH:MM)", value="10:00", key="spa_sched_time")
                with _nt2:
                    _new_cat = st.selectbox("분류", ["consult", "appointment", "call", "other"],
                                            format_func=lambda x: {"consult": "💬 상담", "appointment": "📌 방문",
                                                                    "call": "📞 통화", "other": "📋 기타"}[x],
                                            key="spa_sched_cat")
                    _new_smemo = st.text_area("메모", key="spa_sched_memo", height=60)
                if st.button("📅 저장", key="spa_sched_save", use_container_width=True, type="primary"):
                    if _new_title:
                        try:
                            if _OUTLOOK_OK:
                                _du_save_sched(_user_id, _new_title, _sel_date, _new_time,
                                               _new_smemo, _new_cat, _sel_pid)
                            elif _sb:
                                import uuid as _uid3
                                _sb.table("gk_schedules").insert({
                                    "schedule_id": str(_uid3.uuid4()), "agent_id": _user_id,
                                    "title": _new_title, "date": _sel_date, "start_time": _new_time,
                                    "memo": _new_smemo, "category": _new_cat, "person_id": _sel_pid,
                                    "is_deleted": False,
                                    "created_at": datetime.datetime.utcnow().isoformat(),
                                    "updated_at": datetime.datetime.utcnow().isoformat(),
                                }).execute()
                            st.success("✅ 저장!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as _se:
                            st.error(f"오류: {_se}")
                    else:
                        st.warning("제목을 입력해 주세요.")

        with _memo_col:
            st.markdown("<b style='font-size:0.82rem;'>📝 상담 메모장</b>", unsafe_allow_html=True)
            _cust_memo_v = _sel_cust.get("memo", "") if _sel_cust else ""
            _new_memo_v = st.text_area(
                "메모 (파스텔 노트)", value=_cust_memo_v, height=280,
                key="spa_memo_pad",
            )
            if st.button("💾 메모 저장", key="spa_memo_save", use_container_width=True):
                if _sel_cust and _sb:
                    try:
                        _sb.table("gk_people").update({
                            "memo": _new_memo_v,
                            "updated_at": datetime.datetime.utcnow().isoformat(),
                        }).eq("person_id", _sel_pid).execute()
                        st.success("✅ 메모 저장 완료!")
                        st.cache_data.clear()
                    except Exception as _me:
                        st.error(f"오류: {_me}")

    # ── SCREEN 3: 🌐 내보험다보여 (기존 로직 100% 보존) ────────────────────
    elif _spa_screen == "nibo":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "🌐 내보험다보여 — 신용정보 수집 · 트리니티 분석 파이프라인</div>",
            unsafe_allow_html=True,
        )
        if not _sel_cust:
            st.info("고객을 먼저 선택해 주세요.")
        elif not st.session_state.get("nibo_consent_agreed", False):
            st.markdown(
                "<div style='background:#fffbeb;border:2px dashed #f59e0b;border-radius:10px;"
                "padding:12px 14px;margin-bottom:10px;'>"
                "<div style='font-size:0.84rem;font-weight:900;color:#92400e;margin-bottom:7px;'>"
                "🔐 내보험다보여 연동 동의 필요 — 신용정보법 제32조</div>"
                "<div style='font-size:0.76rem;color:#78350f;line-height:1.85;'>"
                "• <b>수집:</b> 보험사명 · 상품명 · 담보내역 · 계약상태<br>"
                "• <b>인증정보:</b> 데이터 추출 후 즉시 메모리 파기 — 서버 저장 불가<br>"
                "• <b>보유:</b> 분석 완료 후 30일 경과 시 자동 파기</div></div>",
                unsafe_allow_html=True,
            )
            with st.popover("📋 신용정보 조회 안내 전문 보기", use_container_width=True):
                try:
                    from shared_components import _NIBO_CONSENT_HTML as _nibo_html_v
                    st.markdown(_nibo_html_v, unsafe_allow_html=True)
                except Exception:
                    st.markdown("신용정보의 이용 및 보호에 관한 법률 제32조에 따른 안내문입니다.")
            _nibo_inline_agree = st.checkbox(
                "✅ **[즉석 동의]** '내보험다보여' 연동 및 신용정보 조회·분석에 동의합니다 (신용정보법 제32조)",
                value=False, key="crm_nibo_inline_agree",
            )
            if _nibo_inline_agree:
                try:
                    from shared_components import _NIBO_CONSENT_VERSION as _nibo_ver
                except Exception:
                    _nibo_ver = "2026-03-16-v1"
                st.session_state["nibo_consent_agreed"]    = True
                st.session_state["nibo_consent_version"]   = _nibo_ver
                st.session_state["nibo_consent_timestamp"] = datetime.datetime.now().isoformat()
                st.success("✅ 동의 완료! 트리니티 분석이 활성화됩니다.")
                st.rerun()
        else:
            _nibo_mode = st.radio(
                "분석 방법",
                ["📡 내보험다보여 JSON 자동 파싱", "✏️ 수동 담보 입력"],
                horizontal=True, key="nibo_mode_radio", label_visibility="collapsed",
            )
            if _nibo_mode == "📡 내보험다보여 JSON 자동 파싱":
                st.caption("내보험다보여 API JSON → data_normalizer 정규화 → 트리니티 분석 → HQ DB 저장")
                _crm_nibo_raw = st.text_area(
                    "내보험다보여 API JSON 붙여넣기",
                    value=st.session_state.get("crm_nibo_raw_json", ""),
                    placeholder='[{"prodName":"삼성생명 종신","traitName":"암진단비","amt":"3000만원","status":"유효"}]',
                    height=120, key="crm_lsec_nibo_json",
                )
                _crm_nhi_j = st.number_input(
                    "월 건강보험료(원)", min_value=0, max_value=2_000_000,
                    value=0, step=10_000, key="crm_tri_nhi_json",
                    help="직장인: 보수월액×7.09% | 트리니티 소득 역산 기준",
                )
                if st.button("⚡ JSON 파싱 → 분석 → HQ 전송", key="crm_json_pipeline_run",
                             use_container_width=True, type="primary"):
                    if not _crm_nibo_raw.strip():
                        st.warning("JSON 데이터를 붙여넣어 주세요.")
                    elif _crm_nhi_j <= 0:
                        st.warning("월 건강보험료를 입력해 주세요.")
                    else:
                        with st.spinner("🤖 AI가 증권을 정밀 분석 중입니다..."):
                            try:
                                import json as _js_crm
                                from trinity_engine import execute_integrated_analysis as _crm_exec
                                _crm_raw_list = _js_crm.loads(_crm_nibo_raw.strip())
                                if isinstance(_crm_raw_list, dict):
                                    _crm_raw_list = [_crm_raw_list]
                                st.session_state["crm_nibo_raw_json"] = _crm_nibo_raw
                                _c_raw_j = decrypt_pii(_sel_cust.get("contact", ""))
                                _crm_adata, _crm_unmapped, _crm_ok = _crm_exec(
                                    raw_external_data=_crm_raw_list,
                                    client_contact=_c_raw_j,
                                    nhi_premium=float(_crm_nhi_j),
                                    consultant_info={
                                        "소속":   st.session_state.get("crm_user_company", ""),
                                        "이름":   _user_name,
                                        "연락처": st.session_state.get("crm_user_phone", ""),
                                    },
                                    client_name=_sel_cust.get("name", ""),
                                    agent_id=_user_id,
                                    person_id=_sel_cust.get("person_id", ""),
                                    consent_version=st.session_state.get("nibo_consent_version", ""),
                                    source="CRM-내보험다보여",
                                )
                                _crm_active = len([
                                    k for k, v in _crm_adata.items()
                                    if not str(k).startswith("_") and float(v.get("현재가입", 0) or 0) > 0
                                ])
                                if _crm_ok:
                                    st.success("✅ 파이프라인 완료! 담보 " + str(_crm_active) + "개 → HQ 전송")
                                else:
                                    st.warning("⚠️ 분석 완료 (" + str(_crm_active) + "개). DB 저장 실패")
                            except Exception as _crm_pe:
                                if "JSONDecodeError" in type(_crm_pe).__name__:
                                    st.error("❌ JSON 형식 오류.")
                                else:
                                    st.error("❌ 파이프라인 오류: " + str(_crm_pe))
            else:
                st.caption("담보 금액을 직접 입력하여 트리니티 분석을 실행합니다.")
                _t_nhi = st.number_input("월 건강보험료(원)", 0, 2_000_000, 0, 10_000,
                                         key="crm_tri_nhi", help="직장인: 보수월액×7.09%")
                _tc1, _tc2 = st.columns(2)
                with _tc1:
                    _t_cancer = st.number_input("암진단비 가입액(원)",       0, step=1_000_000,  key="crm_tri_cancer")
                    _t_stroke = st.number_input("뇌졸중진단비 가입액(원)",   0, step=1_000_000,  key="crm_tri_stroke")
                    _t_ci     = st.number_input("심근경색진단비 가입액(원)", 0, step=1_000_000,  key="crm_tri_ci")
                with _tc2:
                    _t_acci   = st.number_input("상해후유장해 가입액(원)",   0, step=10_000_000, key="crm_tri_acci")
                    _t_surg   = st.number_input("수술비 가입액(원)",          0, step=1_000_000,  key="crm_tri_surgery")
                    _t_hosp   = st.number_input("입원일당 가입액(원)",        0, step=10_000,     key="crm_tri_hosp")
                if st.button("🔬 분석 실행 & HQ 전송", key="crm_tri_run",
                             use_container_width=True, type="primary"):
                    if _t_nhi > 0:
                        with st.spinner("트리니티 분석 및 DB 저장 중..."):
                            try:
                                from trinity_engine import (
                                    run_trinity_analysis  as _tri_run,
                                    save_analysis_to_db   as _tri_save,
                                    render_trinity_report as _tri_rdr,
                                )
                                _t_cov = {
                                    "암진단비":       float(_t_cancer),
                                    "뇌졸중진단비":   float(_t_stroke),
                                    "심근경색진단비": float(_t_ci),
                                    "상해후유장해":   float(_t_acci),
                                    "수술비":         float(_t_surg),
                                    "입원일당":       float(_t_hosp),
                                }
                                _tri_adata, _tri_income = _tri_run(_t_cov, float(_t_nhi))
                                _c_raw = decrypt_pii(_sel_cust.get("contact", ""))
                                _rpt_t = _tri_rdr(
                                    analysis_data=_tri_adata,
                                    estimated_income=_tri_income,
                                    consultant_info={
                                        "소속":   st.session_state.get("crm_user_company", ""),
                                        "이름":   _user_name,
                                        "연락처": st.session_state.get("crm_user_phone", ""),
                                    },
                                    client_name=_sel_cust.get("name", ""),
                                    show_kakao=True,
                                )
                                _ok = _tri_save(
                                    client_contact=_c_raw,
                                    analysis_data=_tri_adata,
                                    estimated_income=_tri_income,
                                    agent_id=_user_id,
                                    report_text=_rpt_t,
                                    person_id=_sel_cust.get("person_id", ""),
                                )
                                if _ok:
                                    st.success("✅ 분석 완료! HQ 본부로 데이터가 전송되었습니다.")
                                else:
                                    st.warning("⚠️ 분석 완료. DB 저장 실패 (연결 확인 필요)")
                            except Exception as _te:
                                st.error("분석 오류: " + str(_te))
                    else:
                        st.warning("월 건강보험료를 입력해 주세요.")
        st.markdown("---")
        st.markdown("**빠른 HQ 바로가기**")
        _quick_cols = st.columns(4)
        for _qi, (_ql, _qs) in enumerate([
            ("🛡️ KB7 분석", "t3"), ("📋 실손 분석", "t2"),
            ("🎗️ 암보험", "cancer"), ("🏠 화재보험", "fire"),
        ]):
            with _quick_cols[_qi]:
                _q_url = f"{HQ_APP_URL}/?gk_sector={_qs}&gk_token={_token}"
                st.markdown(
                    f'<a href="{_q_url}" target="_blank" style="display:block;text-align:center;'
                    f'background:#1e3a8a;color:#fff;border-radius:8px;padding:8px;'
                    f'font-size:0.82rem;font-weight:900;text-decoration:none;'
                    f'border:1px dashed #93c5fd;">{_ql}</a>',
                    unsafe_allow_html=True,
                )

    # ── SCREEN 4: 📊 증권분석 (HQ 딥링크 브릿지) ────────────────────────────
    elif _spa_screen == "analysis":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "📊 증권분석 — HQ 정밀 분석 발사대</div>",
            unsafe_allow_html=True,
        )
        _sector_opts = {
            "KB 7대 보장 분석": "t3", "보험금 청구 상담": "t1",
            "실손보험 분석": "t2",    "암보험 분석": "cancer",
            "뇌혈관 분석": "brain",   "심장 분석": "heart",
            "화재보험 분석": "fire",  "AI 상담 리포트": "home",
        }
        _sel_sector_label = st.selectbox("📍 분석 섹터 선택", list(_sector_opts.keys()), key="spa_sector_sel")
        _sel_sector = _sector_opts[_sel_sector_label]
        if _sel_cust:
            _dl_url = build_deeplink_to_hq(
                cid=_sel_cust.get("person_id", ""),
                name=_sel_cust.get("name", ""),
                sector=_sel_sector,
                token=_token,
            )
            st.markdown(
                f"<div style='background:#F8FBFA;border:1px dashed #000;border-radius:10px;"
                f"padding:18px;text-align:center;margin-top:8px;'>"
                f"<div style='font-size:0.9rem;color:#374151;margin-bottom:12px;'>"
                f"<b>{_sel_cust.get('name')}</b> — <b>{_sel_sector_label}</b></div>"
                f"<a href='{_dl_url}' target='_blank' style='background:#1e3a8a;color:#fff;"
                f"padding:12px 28px;border-radius:8px;font-size:1rem;font-weight:900;"
                f"text-decoration:none;border:1px dashed #93c5fd;'>"
                f"🚀 HQ 마스터 앱에서 분석 시작</a></div>",
                unsafe_allow_html=True,
            )
            with st.expander("❓ HQ 앱이 열리지 않는다면?", expanded=False):
                st.markdown(
                    f"<div style='background:#eff6ff;border:1px dashed #000;border-radius:10px;"
                    f"padding:14px;font-size:0.85rem;'>"
                    f"웹 주소: <a href='{HQ_APP_URL}' target='_blank'>{HQ_APP_URL}</a></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("고객을 먼저 선택해 주세요.")

    # ── SCREEN 5: 🤖 AI 브리핑 + 시뮬레이터 ──────────────────────────────────
    elif _spa_screen == "ai_brief":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "🤖 AI 브리핑 — 오늘의 우선순위 & 상담 시뮬레이터</div>",
            unsafe_allow_html=True,
        )
        today_str_b = datetime.date.today().strftime("%Y년 %m월 %d일")
        st.caption(f"📅 {today_str_b} 기준")
        with st.spinner("AI 브리핑 데이터 준비 중..."):
            _brief_custs = _load_customers(_user_id)
            _brief_schs  = _load_schedules_today(_user_id)
            _today_mo    = datetime.date.today().month

        def _prio_score(c: dict) -> int:
            _s = (4 - c.get("management_tier", 3)) * 100
            if c.get("auto_renewal_month") == _today_mo: _s += 50
            if c.get("fire_renewal_month") == _today_mo: _s += 40
            return _s

        _p3 = sorted(_brief_custs, key=_prio_score, reverse=True)[:3]
        _bf1, _bf2 = st.columns([3, 2])
        with _bf1:
            st.markdown("**🎯 오늘의 우선 고객 TOP 3**")
            for _rk, _c in enumerate(_p3, 1):
                _tm2 = TIER_META.get(_c.get("management_tier", 3), TIER_META[3])
                _rh  = ""
                if _c.get("auto_renewal_month") == _today_mo: _rh += " ⚡ 자동차 만기!"
                if _c.get("fire_renewal_month") == _today_mo: _rh += " ⚡ 화재 만기!"
                _rdl = build_deeplink_to_hq(cid=_c.get("person_id", ""),
                                            name=_c.get("name", ""), sector="t3", token=_token)
                st.markdown(
                    f"<div style='background:#F8FBFA;border:1px dashed #000;border-radius:10px;"
                    f"border-left:4px solid {_tm2['color']};padding:10px 14px;margin-bottom:8px;'>"
                    f"<b>#{_rk} {_c.get('name','')}</b>"
                    f"<span style='font-size:0.7rem;font-weight:900;padding:1px 6px;border-radius:10px;"
                    f"background:{_tm2['bg']};color:{_tm2['color']};margin-left:6px;'>"
                    f"{_tm2['icon']} {_tm2['label']}</span>"
                    f"<div style='font-size:0.78rem;color:#d97706;'>{_rh}</div>"
                    f"<a href='{_rdl}' target='_blank' style='font-size:0.78rem;color:#1d4ed8;'>"
                    f"🚀 HQ 정밀 분석 →</a></div>",
                    unsafe_allow_html=True,
                )
        with _bf2:
            st.markdown("**📅 오늘의 일정**")
            if _brief_schs:
                for _s in _brief_schs:
                    st.markdown(
                        f"<div style='background:#E6E6FA;border:1px solid #c4b5fd;"
                        f"border-radius:8px;padding:8px 12px;margin-bottom:6px;font-size:0.82rem;'>"
                        f"<b>{_s.get('start_time','')} {_s.get('title','')}</b>"
                        f"<div style='font-size:0.75rem;color:#64748b;'>{_s.get('memo','')}</div></div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("오늘 예정된 일정이 없습니다.")

        st.markdown("---")
        st.markdown("**🎮 AI 상담 시나리오 시뮬레이터**")
        st.caption("실제 고객 상황을 입력하면 AI가 최적 상담 전략을 제시합니다.")
        try:
            from sim_trainer import render_simulation_dashboard as _crm_render_sim
            _crm_render_sim(compact=True)
        except Exception:
            _sim_input = st.text_area(
                "상담 상황 입력",
                placeholder="예: 35세 남성, 현재 암보험 없음, 월 보험료 30만원 예산...",
                height=100, key="crm_sim_input",
            )
            if st.button("🤖 AI 전략 생성", key="crm_sim_run", use_container_width=True, type="primary"):
                if _sim_input.strip():
                    with st.spinner("AI 전략 분석 중..."):
                        try:
                            from shared_components import get_env_secret as _genv_sim
                            import google.generativeai as genai
                            genai.configure(api_key=_genv_sim("GOOGLE_API_KEY", ""))
                            _m_sim  = genai.GenerativeModel("gemini-1.5-flash")
                            _prompt = (
                                f"당신은 골드키 AI 보험 상담 코치입니다.\n"
                                f"설계사가 다음 상황에서 고객과 상담합니다:\n\n{_sim_input}\n\n"
                                f"최적 상담 전략, 예상 질문 3가지, 추천 보장 순서를 간결하게 한국어로 작성해 주세요."
                            )
                            _r_sim = _m_sim.generate_content(_prompt)
                            st.markdown(
                                f"<div style='background:#F8FBFA;border:1px dashed #000;border-radius:10px;"
                                f"padding:14px;font-size:0.85rem;line-height:1.8;'>"
                                f"{_r_sim.text.replace(chr(10), '<br>')}</div>",
                                unsafe_allow_html=True,
                            )
                        except Exception as _sim_e:
                            st.error(f"AI 시뮬레이터 오류: {_sim_e}")
                else:
                    st.warning("상담 상황을 입력해 주세요.")

    # ── SCREEN 6: 💬 카카오 발송 ─────────────────────────────────────────────
    elif _spa_screen == "kakao":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "💬 카카오 발송 — 알림톡 / 상담 링크 전송</div>",
            unsafe_allow_html=True,
        )
        if not _sel_cust:
            st.info("고객을 먼저 선택해 주세요.")
        else:
            _kk1, _kk2 = st.columns(2)
            with _kk1:
                st.markdown(
                    "<div style='background:#F8FBFA;border:1px dashed #000;border-radius:10px;padding:14px;'>"
                    "<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;margin-bottom:10px;'>"
                    "📤 알림톡 발송</div>",
                    unsafe_allow_html=True,
                )
                _kk_phone = decrypt_pii(_sel_cust.get("contact", ""))
                _kk_name  = _sel_cust.get("name", "")
                _kk_tmpl  = st.selectbox("템플릿",
                                         ["상담 안내", "만기 알림", "분석 리포트 전달", "맞춤형 메시지"],
                                         key="kakao_tmpl_sel")
                _kk_msg = st.text_area(
                    "메시지 내용",
                    value=f"{_kk_name} 고객님, 안녕하세요. 골드키 AI 설계사입니다.",
                    height=100, key="kakao_msg_inp",
                )
                if st.button("📤 발송", key="kakao_send_btn", use_container_width=True, type="primary"):
                    try:
                        from modules.kakao_service import send_kakao_alimtalk
                        _kk_ok = send_kakao_alimtalk(
                            phone=_kk_phone, name=_kk_name,
                            template=_kk_tmpl, message=_kk_msg,
                        )
                        if _kk_ok:
                            st.success(f"✅ {_kk_name} 님께 카카오톡 발송 완료!")
                        else:
                            st.warning("발송 실패 (카카오 API 설정 확인)")
                    except Exception as _ke:
                        st.error(f"발송 오류: {_ke}")
                st.markdown("</div>", unsafe_allow_html=True)
            with _kk2:
                st.markdown(
                    "<div style='background:#F8FBFA;border:1px dashed #000;border-radius:10px;padding:14px;'>"
                    "<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;margin-bottom:10px;'>"
                    "🔗 HQ 딥링크 공유</div>",
                    unsafe_allow_html=True,
                )
                _sh_sector = st.selectbox(
                    "공유할 분석 섹터",
                    ["t3", "t2", "cancer", "brain"],
                    format_func=lambda x: {"t3": "KB7 분석", "t2": "실손", "cancer": "암보험", "brain": "뇌혈관"}.get(x, x),
                    key="kakao_share_sector",
                )
                _sh_url = build_deeplink_to_hq(
                    cid=_sel_cust.get("person_id", ""),
                    name=_sel_cust.get("name", ""),
                    sector=_sh_sector,
                    token=_token,
                )
                st.markdown(
                    f"<div style='background:#eff6ff;border:1px dashed #93c5fd;border-radius:8px;"
                    f"padding:8px 12px;font-size:0.74rem;word-break:break-all;'>{_sh_url}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)
# ══════════════════════════════════════════════════════════════════════════════
# [GP-PHASE-4] 반응형 통합 증권분석 센터 — CRM 이식 (HQ와 완전 동일)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
try:
    from shared_components import render_unified_analysis_center as _crm_render_uac
    _crm_render_uac(key_prefix="_uac_crm")
except Exception as _crm_uac_e:
    st.error(f"통합 증권분석 센터 로드 오류: {_crm_uac_e}")

# ── 푸터 ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;font-size:0.72rem;color:#9ca3af;padding:8px 0;">
  본 앱은 Goldkey AI Masters 2026의 서브 애플리케이션(Shadow App)입니다.<br>
  모든 AI 분석 및 정밀 상담 로직은 모 앱의 보안 프로토콜을 따릅니다.<br>
  GP 마스터-그림자 원칙 Phase 1~4 준수
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 관리자 콘솔 (최하단) — HQ Admin Console 동일 패턴
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
with st.expander("🛠️ Admin Console · Goldkey_AI_M", expanded=False):
    _cadm_already = (
        st.session_state.get("crm_is_admin")
        or st.session_state.get("crm_role") == "admin"
    )
    if not _cadm_already:
        with st.form("crm_admin_login_form", clear_on_submit=False):
            _cadm_id   = st.text_input("관리자 ID", key="crm_admin_id_f",
                                        placeholder="admin 또는 이세윤")
            _cadm_code = st.text_input("관리자 코드", key="crm_admin_code_f",
                                        type="password", placeholder="코드 입력")
            _cadm_sub  = st.form_submit_button("🔐 관리자 로그인",
                                                use_container_width=True)
        if _cadm_sub:
            _cadm_id_v   = (_cadm_id   or "").strip()
            _cadm_code_v = (_cadm_code or "").strip()
            _cadm_env    = get_env_secret("ADMIN_CODE", "")
            _master_env  = get_env_secret("MASTER_CODE", "")
            import hashlib as _hl_cadm
            _cadm_default_hash = _hl_cadm.sha256(b"kgagold6803").hexdigest()
            _cadm_pw_hash      = get_env_secret("CRM_ADMIN_PW_HASH", _cadm_default_hash)
            _cadm_input_hash   = _hl_cadm.sha256(_cadm_code_v.encode()).hexdigest()
            if _cadm_id_v.lower() in ("admin", "이세윤") and _cadm_code_v == _cadm_env and _cadm_env:
                st.session_state["crm_is_admin"]  = True
                st.session_state["crm_user_id"]   = "ADMIN_MASTER"
                st.session_state["crm_user_name"] = "이세윤"
                st.session_state["crm_role"]      = "admin"
                st.rerun()
            elif _cadm_code_v == _master_env and _master_env:
                _mname = get_env_secret("MASTER_NAME", "이세윤")
                st.session_state["crm_is_admin"]  = True
                st.session_state["crm_user_id"]   = "PERMANENT_MASTER"
                st.session_state["crm_user_name"] = _mname
                st.session_state["crm_role"]      = "admin"
                st.rerun()
            elif _cadm_id_v.lower() in ("admin", "이세윤") and _cadm_input_hash == _cadm_pw_hash:
                st.session_state["crm_is_admin"]  = True
                st.session_state["crm_user_id"]   = "ADMIN_MASTER"
                st.session_state["crm_user_name"] = "이세윤"
                st.session_state["crm_role"]      = "admin"
                st.rerun()
            else:
                st.error("ID 또는 코드가 올바르지 않습니다.")
    else:
        _cadm_name = st.session_state.get("crm_user_name", "관리자")
        st.success(f"✅ 관리자 로그인 중: **{_cadm_name}**")
        st.markdown("---")

        # ── Supabase DB 관리 ──────────────────────────────────────────────
        st.markdown("**🗄️ Supabase DB 관리**")
        try:
            _cadm_sb_url  = get_env_secret("SUPABASE_URL", "")
            _cadm_sb_proj = _cadm_sb_url.replace("https://", "").split(".")[0] if _cadm_sb_url else ""
        except Exception:
            _cadm_sb_proj = ""
        if _cadm_sb_proj:
            _cadm_sql_url = f"https://supabase.com/dashboard/project/{_cadm_sb_proj}/sql/new"
            st.markdown(
                f'<a href="{_cadm_sql_url}" target="_blank">'
                f'<button style="width:100%;padding:8px;background:#3ecf8e;color:#fff;'
                f'border:none;border-radius:6px;font-size:0.85rem;font-weight:700;cursor:pointer;">'
                f'🔗 Supabase SQL Editor 열기</button></a>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<a href="https://supabase.com/dashboard" target="_blank">'
                '<button style="width:100%;padding:8px;background:#3ecf8e;color:#fff;'
                'border:none;border-radius:6px;font-size:0.85rem;font-weight:700;cursor:pointer;">'
                '🔗 Supabase 대시보드 열기</button></a>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # ── 전체 회원 현황 ───────────────────────────────────────────────
        st.markdown("**👥 전체 회원 현황**")
        try:
            _cadm_db = _get_supabase()
            if _cadm_db:
                _cadm_rows = (
                    _cadm_db.table("members")
                    .select("user_id,user_name,join_date,is_deleted")
                    .eq("is_deleted", False)
                    .execute()
                )
                _cadm_list = _cadm_rows.data or []
                st.caption(f"총 등록 회원: {len(_cadm_list)}명")
                if _cadm_list:
                    import pandas as _pd_adm
                    _cadm_df = _pd_adm.DataFrame([{
                        "이름":  m.get("user_name", ""),
                        "ID":    str(m.get("user_id", ""))[:10] + "…",
                        "가입일": str(m.get("join_date", ""))[:10],
                    } for m in _cadm_list[:30]])
                    st.dataframe(_cadm_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Supabase 연결 없음")
        except Exception as _cadm_err:
            st.caption(f"회원 조회 오류: {_cadm_err}")

        st.markdown("---")
        if st.button("🚪 관리자 로그아웃", key="crm_admin_logout_btn",
                     use_container_width=True):
            st.session_state.pop("crm_is_admin", None)
            if st.session_state.get("crm_role") == "admin":
                st.session_state["crm_role"] = "agent"
            st.rerun()

