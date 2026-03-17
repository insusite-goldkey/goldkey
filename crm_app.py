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
)

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="골드키 CRM — 고객상담 앱",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
        # ── [GP-SEC §5] 공통 약관 동의 UI (제목 박스 포함, CSS 타겟팅) ────────
        st.markdown(
            "<div style='text-align:center;margin-bottom:0;'>"
            "<span style='background:#1e3a8a;border-radius:8px 8px 0 0;padding:6px 20px;"
            "font-size:0.92rem;font-weight:900;color:#ffffff;display:inline-block;'>"
            "🏆 Goldkey AI Masters 2026 이용약관</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        _crm_agreed = _sc_render_auth_screen(
            app_name="Goldkey AI Masters 2026",
            app_icon="🏆",
            terms_agree_key="_crm_terms_agreed",
            show_header=False,
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
                if _crm_lp == "A":
                    try:
                        _sc_emergency_btn(app_name="CRM", key_prefix="crm_login_emg", show_admin_login=True)
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
<div style="background:#1e3a5f;padding:14px 20px;border-radius:0;
  display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
  <div>
    <span style="font-size:1.3rem;font-weight:900;color:#ffd700;">📱 골드키 CRM</span>
    <span style="font-size:0.78rem;color:#93c5fd;margin-left:10px;">고객상담 앱</span>
  </div>
  <div style="font-size:0.82rem;color:#e2e8f0;">{_user_name} 설계사</div>
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
    if st.button("로그아웃", key="crm_logout_btn", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# [@st.fragment] 무거운 탭 렌더러 — 백화 방지 (GP-84 §11)
# ══════════════════════════════════════════════════════════════════════════════
@st.fragment
def _crm_render_tab4():
    """[GP-84 §11] TAB4: HQ 딥링크 발사대 + 내보험다보여 파이프라인 (부분 rerun)"""
    st.markdown('<div class="gk-section-title">🚀 HQ 모 앱 연결 — 정밀 분석 발사대</div>',
                unsafe_allow_html=True)
    st.caption("복잡한 보험 분석은 모 앱(Goldkey AI HQ)에 위임합니다.")

    _all_names = ["(고객 선택)"] + [c.get("name", "") for c in _load_customers(_user_id)]
    _sel_name  = st.selectbox("🎯 분석할 고객 선택", _all_names, key="crm_dl_cust")
    _sel_cust  = next((c for c in _load_customers(_user_id)
                       if c.get("name") == _sel_name), None)

    _sector_opts = {
        "KB 7대 보장 분석": "t3",
        "보험금 청구 상담": "t1",
        "실손보험 분석":   "t2",
        "암보험 분석":     "cancer",
        "뇌혈관 분석":     "brain",
        "심장 분석":       "heart",
        "화재보험 분석":   "fire",
        "AI 상담 리포트":  "home",
    }
    _sel_sector_label = st.selectbox("📍 이동할 분석 섹터", list(_sector_opts.keys()),
                                     key="crm_dl_sector")
    _sel_sector = _sector_opts[_sel_sector_label]

    if _sel_cust:
        _dl_url = build_deeplink_to_hq(
            cid=_sel_cust.get("person_id", ""),
            name=_sel_cust.get("name", ""),
            sector=_sel_sector,
            token=_token,
        )
        st.markdown(f"""
<div class="gk-card" style="text-align:center;padding:20px;">
  <div style="font-size:0.9rem;color:#374151;margin-bottom:12px;">
    <b>{_sel_cust.get('name')}</b> 고객 — <b>{_sel_sector_label}</b> 섹터로 이동
  </div>
  <a href="{_dl_url}" target="_blank" class="gk-deeplink-btn"
     style="font-size:1rem;padding:10px 24px;">
    🚀 HQ 모 앱에서 정밀 분석 진행
  </a>
</div>""", unsafe_allow_html=True)

        with st.expander("❓ 모 앱이 열리지 않는다면?", expanded=False):
            st.markdown(f"""
<div style="background:#eff6ff;border:1px dashed #000;border-radius:10px;padding:14px;font-size:0.85rem;">
  <b>📌 안내 데스크 (Fallback 가이드)</b><br><br>
  1️⃣ <b>웹 브라우저</b>로 직접 접속:<br>
  &nbsp;&nbsp;<a href="{HQ_APP_URL}" target="_blank">{HQ_APP_URL}</a><br><br>
  2️⃣ 로그인 후 상단 주소창에 아래 파라미터를 추가하세요:<br>
  &nbsp;&nbsp;<code>?gk_cid={_sel_cust.get('person_id','')}&amp;gk_sector={_sel_sector}</code><br><br>
  3️⃣ 모바일에서 앱이 미설치 시: 위 링크를 북마크에 추가하세요.
</div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            "<div style='background:#f0fdf4;border:1px dashed #059669;border-radius:10px;"
            "padding:10px 14px;font-size:0.82rem;margin-bottom:8px;'>"
            "<b style='color:#059669;'>📊 트리니티 완전 파이프라인 & HQ DB 저장</b><br>"
            "내보험다보여 JSON 또는 수동 입력 → 정규화 → 분석 → HQ 실시간 공유</div>",
            unsafe_allow_html=True,
        )
        if not st.session_state.get("nibo_consent_agreed", False):
            st.markdown(
                "<div style='background:#fffbeb;border:2px dashed #f59e0b;"
                "border-radius:10px;padding:12px 14px;margin-bottom:10px;'>"
                "<div style='font-size:0.84rem;font-weight:900;color:#92400e;margin-bottom:7px;'>"
                "🔐 내보험다보여 연동 동의 필요 — 신용정보법 제32조</div>"
                "<div style='font-size:0.76rem;color:#78350f;line-height:1.85;'>"
                "트리니티 분석 기능을 이용하려면 아래 동의가 필요합니다.<br>"
                "• <b>수집:</b> 보험사명 · 상품명 · 담보내역 · 계약상태<br>"
                "• <b>인증정보:</b> 데이터 추출 후 즉시 메모리 파기 — 서버 저장 불가<br>"
                "• <b>보유:</b> 분석 완료 후 30일 경과 시 자동 파기"
                "</div></div>",
                unsafe_allow_html=True,
            )
            with st.popover("📋 신용정보 조회 안내 전문 보기", use_container_width=True):
                try:
                    from shared_components import _NIBO_CONSENT_HTML as _crm_ng_nch
                    st.markdown(_crm_ng_nch, unsafe_allow_html=True)
                except Exception:
                    st.markdown("신용정보의 이용 및 보호에 관한 법률 제32조에 따른 안내문입니다.")
            _crm_nibo_inline = st.checkbox(
                "✅ **[즉석 동의]** '내보험다보여' 연동 및 신용정보 조회·분석에 동의합니다 (신용정보법 제32조)",
                value=False, key="crm_nibo_inline_agree",
            )
            if _crm_nibo_inline:
                try:
                    from shared_components import _NIBO_CONSENT_VERSION as _crm_ng_ncv
                except Exception:
                    _crm_ng_ncv = "2026-03-16-v1"
                st.session_state["nibo_consent_agreed"]    = True
                st.session_state["nibo_consent_version"]   = _crm_ng_ncv
                st.session_state["nibo_consent_timestamp"] = __import__("datetime").datetime.now().isoformat()
                st.success("✅ 동의 완료! 트리니티 분석이 활성화됩니다.")
                st.rerun()
        else:
            _crm_tri_t1, _crm_tri_t2 = st.tabs(["📡 내보험다보여 JSON 자동 파싱", "✏️ 수동 담보 입력"])
            with _crm_tri_t1:
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
                                    raw_external_data = _crm_raw_list,
                                    client_contact    = _c_raw_j,
                                    nhi_premium       = float(_crm_nhi_j),
                                    consultant_info   = {
                                        "소속":   st.session_state.get("crm_user_company", ""),
                                        "이름":   _user_name,
                                        "연락처": st.session_state.get("crm_user_phone", ""),
                                    },
                                    client_name     = _sel_cust.get("name", ""),
                                    agent_id        = _user_id,
                                    person_id       = _sel_cust.get("person_id", ""),
                                    consent_version = st.session_state.get("nibo_consent_version", ""),
                                    source          = "CRM-내보험다보여",
                                )
                                _crm_active = len([k for k, v in _crm_adata.items() if not str(k).startswith("_") and float(v.get("현재가입", 0) or 0) > 0])
                                if _crm_ok:
                                    st.success("✅ 파이프라인 완료! 담보 " + str(_crm_active) + "개 → HQ 전송")
                                else:
                                    st.warning("⚠️ 분석 완료 (" + str(_crm_active) + "개). DB 저장 실패")
                            except Exception as _crm_pe:
                                if "JSONDecodeError" in type(_crm_pe).__name__:
                                    st.error("❌ JSON 형식 오류. 올바른 JSON을 붙여넣어 주세요.")
                                else:
                                    st.error("❌ 파이프라인 오류: " + str(_crm_pe))
            with _crm_tri_t2:
                st.caption("담보 금액을 직접 입력하여 트리니티 분석을 실행합니다.")
                _t_nhi = st.number_input(
                    "월 건강보험료(원)", min_value=0, max_value=2_000_000,
                    value=0, step=10_000, key="crm_tri_nhi",
                    help="직장인: 보수월액×7.09% / 지역가입자: 고지서 확인",
                )
                _tc1, _tc2 = st.columns(2)
                with _tc1:
                    _t_cancer = st.number_input("암진단비 가입액(원)",      0, step=1_000_000,  key="crm_tri_cancer")
                    _t_stroke = st.number_input("뇌졸중진단비 가입액(원)",  0, step=1_000_000,  key="crm_tri_stroke")
                    _t_ci     = st.number_input("심근경색진단비 가입액(원)",0, step=1_000_000,  key="crm_tri_ci")
                with _tc2:
                    _t_acci   = st.number_input("상해후유장해 가입액(원)",  0, step=10_000_000, key="crm_tri_acci")
                    _t_surg   = st.number_input("수술비 가입액(원)",         0, step=1_000_000,  key="crm_tri_surgery")
                    _t_hosp   = st.number_input("입원일당 가입액(원)",       0, step=10_000,     key="crm_tri_hosp")
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
    else:
        st.info("위에서 고객을 먼저 선택해 주세요.")

    st.markdown("---")
    st.markdown("**빠른 HQ 바로가기**")
    _quick_cols = st.columns(4)
    for i, (label, sector) in enumerate([
        ("🛡️ KB7 분석", "t3"), ("📋 실손 분석", "t2"),
        ("🎗️ 암보험",   "cancer"), ("🏠 화재보험", "fire"),
    ]):
        with _quick_cols[i]:
            _q_url = f"{HQ_APP_URL}/?gk_sector={sector}&gk_token={_token}"
            st.markdown(
                f'<a href="{_q_url}" target="_blank" style="display:block;'
                f'text-align:center;background:#1e3a8a;color:#fff;border-radius:8px;'
                f'padding:8px;font-size:0.82rem;font-weight:900;text-decoration:none;'
                f'border:1px dashed #93c5fd;">{label}</a>',
                unsafe_allow_html=True,
            )


@st.fragment
def _crm_render_tab6():
    """[GP-84 §11] TAB6: AI 상담 시뮬레이터 (부분 rerun)"""
    st.markdown('<div class="gk-section-title">🎮 AI 상담 시나리오 시뮬레이터</div>',
                unsafe_allow_html=True)
    st.caption("페르소나 기반 AI 고객과 롤플레이 → 트리니티 핵심 키워드 채점 → 마스터의 코칭")
    try:
        from sim_trainer import render_simulation_dashboard as _crm_render_sim
        _crm_render_sim(compact=True)
    except Exception as _crm_sim_e:
        st.error("시뮬레이션 로드 오류: " + str(_crm_sim_e))


# ══════════════════════════════════════════════════════════════════════════════
# 탭 네비게이션
# ══════════════════════════════════════════════════════════════════════════════
TAB_BRIEFING  = "🌅 AI 브리핑"
TAB_CUSTOMERS = "👥 고객 목록"
TAB_SCHEDULE  = "📅 일정"
TAB_DEEPLINK  = "🚀 HQ 연결"
TAB_HQ_GUIDE  = "🏢 HQ 앱 안내"
TAB_SIM       = "🎮 AI 시뮬"

_active_tab = st.session_state.get("crm_tab", TAB_BRIEFING)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([TAB_BRIEFING, TAB_CUSTOMERS, TAB_SCHEDULE, TAB_DEEPLINK, TAB_HQ_GUIDE, TAB_SIM])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: AI 아침 브리핑 — 우선순위 고객 3명 + 오늘 일정
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="gk-section-title">🌅 AI 아침 브리핑</div>', unsafe_allow_html=True)
    today_str = datetime.date.today().strftime("%Y년 %m월 %d일 (%A)")
    st.caption(f"📅 {today_str}")

    with st.spinner("브리핑 데이터 불러오는 중..."):
        all_cust   = _load_customers(_user_id)
        today_sch  = _load_schedules_today(_user_id)
        today_mo   = datetime.date.today().month

    # 우선순위 3명: VVIP 우선, 이번 달 만기 고객, 최근 미연락 순
    def _priority_score(c: dict) -> int:
        score = 0
        tier = c.get("management_tier", 3)
        score += (4 - tier) * 100
        if c.get("auto_renewal_month") == today_mo: score += 50
        if c.get("fire_renewal_month") == today_mo: score += 40
        return score

    priority_3 = sorted(all_cust, key=_priority_score, reverse=True)[:3]

    col_brief, col_sch = st.columns([3, 2])
    with col_brief:
        st.markdown("**🎯 오늘의 우선 고객 TOP 3**")
        if priority_3:
            for rank, c in enumerate(priority_3, 1):
                tier_m = TIER_META.get(c.get("management_tier", 3), TIER_META[3])
                renewal_hint = ""
                if c.get("auto_renewal_month") == today_mo:
                    renewal_hint = f"  ⚡ 자동차보험 만기 이번 달!"
                if c.get("fire_renewal_month") == today_mo:
                    renewal_hint += f"  ⚡ 화재보험 만기 이번 달!"
                dl_url = build_deeplink_to_hq(
                    cid=c.get("person_id", ""),
                    name=c.get("name", ""),
                    sector="t3",
                    token=_token,
                )
                st.markdown(f"""
<div class="gk-card" style="border-left:4px solid {tier_m['color']};">
  <b style="font-size:1rem;color:#1e293b;">#{rank} {c.get('name', '')}</b>
  <span class="gk-badge" style="color:{tier_m['color']};background:{tier_m['bg']};
    margin-left:8px;">{tier_m['icon']} {tier_m['label']}</span>
  <div style="font-size:0.8rem;color:#6b7280;margin-top:3px;">
    {c.get('job', '')} · {decrypt_pii(c.get('contact', ''))}
  </div>
  <div style="font-size:0.78rem;color:#d97706;margin-top:2px;">{renewal_hint}</div>
  <a href="{dl_url}" target="_blank" class="gk-deeplink-btn">
    🚀 HQ 정밀 분석 진행
  </a>
</div>""", unsafe_allow_html=True)
        else:
            st.info("고객 데이터가 없습니다. 고객 목록 탭에서 추가해 주세요.")

    with col_sch:
        st.markdown("**📅 오늘의 일정**")
        if today_sch:
            for s in today_sch:
                st.markdown(f"""
<div class="gk-card">
  <b>{s.get('start_time', '')} {s.get('title', '')}</b>
  <div style="font-size:0.78rem;color:#6b7280;">{s.get('memo', '')}</div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("오늘 예정된 일정이 없습니다.")

        # 이번 달 만기 고객 요약
        renewal_this_month = [
            c for c in all_cust
            if c.get("auto_renewal_month") == today_mo
            or c.get("fire_renewal_month") == today_mo
        ]
        if renewal_this_month:
            st.markdown(f"**🔔 이번 달 만기 고객 ({len(renewal_this_month)}명)**")
            for c in renewal_this_month[:5]:
                st.markdown(
                    f"<div style='font-size:0.82rem;padding:3px 0;'>"
                    f"• {c['name']}  "
                    f"{'🚗' if c.get('auto_renewal_month')==today_mo else ''}"
                    f"{'🏠' if c.get('fire_renewal_month')==today_mo else ''}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: 고객 목록 + 입력 폼
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="gk-section-title">👥 담당 고객 목록</div>', unsafe_allow_html=True)

    c_search_col, c_add_col = st.columns([4, 1])
    with c_search_col:
        _search = st.text_input("🔍 이름 또는 연락처 검색",
                                placeholder="이름 검색...",
                                key="crm_search", label_visibility="collapsed")
    with c_add_col:
        if st.button("➕ 고객 추가", use_container_width=True, key="crm_add_btn"):
            st.session_state["crm_form_open"] = True
            st.session_state["crm_form_data"] = None

    # 고객 목록 로드
    _customers = _load_customers(_user_id, _search)
    st.caption(f"총 {len(_customers)}명")

    # 필터 컬럼
    f1, f2, f3 = st.columns(3)
    with f1:
        _tier_filter = st.selectbox("등급 필터", ["전체", "VVIP(1)", "핵심(2)", "일반(3)"],
                                    key="crm_tier_f", label_visibility="visible")
    with f2:
        _mo_filter = st.number_input("만기월 필터 (0=전체)", min_value=0, max_value=12,
                                     value=0, key="crm_mo_f")
    with f3:
        _status_filter = st.selectbox("상태 필터", ["전체", "가망", "진행중", "계약", "종료"],
                                      key="crm_stat_f")

    _status_map_rev = {"가망": "potential", "진행중": "active", "계약": "contracted", "종료": "closed"}
    _tier_map_rev   = {"VVIP(1)": 1, "핵심(2)": 2, "일반(3)": 3}

    _filtered = _customers
    if _tier_filter != "전체":
        _t = _tier_map_rev.get(_tier_filter)
        _filtered = [c for c in _filtered if c.get("management_tier") == _t]
    if _mo_filter:
        _filtered = [c for c in _filtered
                     if c.get("auto_renewal_month") == _mo_filter
                     or c.get("fire_renewal_month") == _mo_filter]
    if _status_filter != "전체":
        _s = _status_map_rev.get(_status_filter, "")
        _filtered = [c for c in _filtered if c.get("status") == _s]

    # 고객 폼 (추가/수정) — 공통 customer_form() 사용
    if st.session_state.get("crm_form_open"):
        with st.expander("✏️ 고객 정보 입력/수정", expanded=True):
            _init = st.session_state.get("crm_form_data")
            _form_data = customer_form(_init, key_prefix="crm_cf")
            _s1, _s2 = st.columns(2)
            with _s1:
                if st.button("💾 저장", key="crm_save", use_container_width=True, type="primary"):
                    try:
                        customer_input_form(_form_data, _user_id, _sb)
                        st.success("✅ 저장 완료!")
                        st.session_state["crm_form_open"] = False
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 오류: {e}")
            with _s2:
                if st.button("✕ 취소", key="crm_cancel", use_container_width=True):
                    st.session_state["crm_form_open"] = False
                    st.rerun()

    # [Phase 1] 공통 render_customer_list() 사용
    render_customer_list(_filtered, show_deeplink=True, agent_tab="t3")

    if len(_filtered) >= 20:
        st.caption("📌 최대 20건 표시. 검색어로 필터링 해 주세요.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: 일정 관리 (기본 조회)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="gk-section-title">📅 일정 관리</div>', unsafe_allow_html=True)

    _sch_date = st.date_input("날짜 선택", value=datetime.date.today(), key="crm_sch_date")

    if _sb:
        try:
            _sch_resp = (
                _sb.table("gk_schedules")
                .select("*, gk_people(name)")
                .eq("is_deleted", False)
                .eq("agent_id", _user_id)
                .eq("date", str(_sch_date))
                .order("start_time")
                .execute()
            )
            _sch_list = _sch_resp.data or []
        except Exception:
            _sch_list = []
    else:
        _sch_list = []

    if _sch_list:
        for _s in _sch_list:
            _cname = (_s.get("gk_people") or {}).get("name", "")
            _cat_icons = {"consult": "💬", "appointment": "📌", "call": "📞", "other": "📋"}
            _icon = _cat_icons.get(_s.get("category", ""), "📋")
            st.markdown(f"""
<div class="gk-card">
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="font-size:1.1rem;">{_icon}</span>
    <b>{_s.get('start_time', '')} — {_s.get('title', '')}</b>
    {f'<span style="font-size:0.78rem;color:#6b7280;">({_cname})</span>' if _cname else ''}
  </div>
  {f'<div style="font-size:0.8rem;color:#6b7280;margin-top:4px;">{_s.get("memo","")}</div>' if _s.get('memo') else ''}
</div>""", unsafe_allow_html=True)
    else:
        st.info(f"{_sch_date} 일정이 없습니다.")

    st.markdown("---")
    st.markdown("**➕ 일정 추가 (간단)**")
    _nt1, _nt2 = st.columns(2)
    with _nt1:
        _new_title = st.text_input("일정 제목", key="crm_new_sch_title")
        _new_time  = st.text_input("시작 시간 (HH:MM)", value="10:00", key="crm_new_sch_time")
    with _nt2:
        _new_memo  = st.text_area("메모", key="crm_new_sch_memo", height=68)

    if st.button("📅 일정 저장", key="crm_sch_save", use_container_width=False):
        if _new_title and _sb:
            try:
                import uuid as _uuid2
                _sb.table("gk_schedules").insert({
                    "schedule_id": str(_uuid2.uuid4()),
                    "agent_id":    _user_id,
                    "title":       _new_title,
                    "date":        str(_sch_date),
                    "start_time":  _new_time,
                    "memo":        _new_memo,
                    "is_deleted":  False,
                    "created_at":  datetime.datetime.utcnow().isoformat(),
                    "updated_at":  datetime.datetime.utcnow().isoformat(),
                }).execute()
                st.success("✅ 일정 저장 완료!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"일정 저장 오류: {e}")
        else:
            st.warning("제목을 입력해 주세요.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: HQ 딥링크 발사대 + Fallback (@st.fragment)
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    _crm_render_tab4()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: HQ 앱 설치 안내 — 온보딩 안내 데스크
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="gk-section-title">🏢 Goldkey HQ 마스터 앱 설치 센터</div>',
                unsafe_allow_html=True)

    with st.container(border=True):
        st.info(
            "더 깊고 정밀한 증권분석과 세부 상담(암·뇌혈관·화재 등)은 **HQ 마스터 앱**에서 진행됩니다.\n\n"
            "완벽한 상담을 위해 태블릿이나 스마트폰에 정식 앱을 다운로드해 주세요."
        )

        # ── 역할 분담 안내 ──────────────────────────────────────────────────────
        st.markdown(
            "<div style='background:#eff6ff;border:1px dashed #000;border-radius:10px;"
            "padding:12px 16px;margin-bottom:12px;font-size:0.85rem;color:#1e3a8a;'>"
            "<b>📌 역할 분담</b><br>"
            "<span style='color:#374151;'>"
            "✅ <b>CRM 앱 (현재 앱)</b> — 현장 스캐너 · 고객 리스트 · 일정 · 빠른 딥링크 발사대<br>"
            "🏢 <b>HQ 마스터 앱</b> — 정밀 암/뇌혈관/화재 분석 · KB 7대 보장공백 진단 · AI 종합 리포트"
            "</span></div>",
            unsafe_allow_html=True,
        )

        st.divider()

        # ── 스토어 설치 버튼 ────────────────────────────────────────────────────
        st.markdown("**📲 정식 앱 다운로드**")
        _inst_c1, _inst_c2 = st.columns(2)
        with _inst_c1:
            st.link_button(
                "🤖 Google Play 다운로드",
                "https://play.google.com/",
                use_container_width=True,
            )
        with _inst_c2:
            st.link_button(
                "🍎 App Store 다운로드",
                "https://www.apple.com/app-store/",
                use_container_width=True,
            )

        st.link_button(
            "💻 웹 버전 즉시 실행 (PC / 태블릿)",
            HQ_APP_URL,
            use_container_width=True,
        )

        st.divider()

        # ── 사용법 가이드 (아코디언) ─────────────────────────────────────────────
        with st.expander("💡 HQ 앱과 CRM 앱, 어떻게 같이 쓰나요?", expanded=True):
            st.markdown(
                "<div style='border:1px dashed #000;border-radius:10px;"
                "padding:14px 18px;background:#ffffff;font-size:0.87rem;line-height:2.0;'>"
                "<b style='color:#1e3a8a;font-size:0.95rem;'>3단계 연동 워크플로우</b><br><br>"
                "1️⃣ <b>현장 스캔</b><br>"
                "&nbsp;&nbsp;&nbsp;CRM 앱(현재 앱)으로 고객 증권을 스캔하고 상담 일정을 잡습니다.<br><br>"
                "2️⃣ <b>HQ 호출</b><br>"
                "&nbsp;&nbsp;&nbsp;정밀 분석이 필요할 때, 고객 카드의 "
                "<b style='background:#1e3a8a;color:#fff;padding:1px 6px;border-radius:4px;'>"
                "🚀 HQ 정밀 분석 진행</b> 버튼을 누릅니다.<br><br>"
                "3️⃣ <b>마법 같은 연동</b><br>"
                "&nbsp;&nbsp;&nbsp;추가 로그인 없이 HQ 앱이 즉시 열리며, "
                "<b>해당 고객의 분석 화면으로 자동 이동</b>합니다!"
                "</div>",
                unsafe_allow_html=True,
            )

        st.divider()

        # ── QR 코드 힌트 ────────────────────────────────────────────────────────
        st.markdown(
            "<div style='background:#f9fafb;border:1px dashed #000;border-radius:10px;"
            "padding:12px 16px;font-size:0.82rem;color:#374151;text-align:center;'>"
            "📱 <b>태블릿 사용자 팁</b> — 태블릿에서 QR 코드를 스캔하면 바로 HQ 웹 버전이 실행됩니다.<br>"
            f"<span style='font-size:0.75rem;color:#6b7280;'>웹 주소: {HQ_APP_URL}</span>"
            "</div>",
            unsafe_allow_html=True,
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6: AI 상담 시뮬레이션 — 설계사 교육 롤플레이
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    _crm_render_tab6()

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
with st.expander("🛠️ Admin Console · CRM", expanded=False):
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
            if _cadm_id_v.lower() in ("admin", "이세윤") and _cadm_code_v == _cadm_env:
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
