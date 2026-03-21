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
import calendar_engine

# ── [조건부] voice_engine · crm_fortress import ───────────────────────────
try:
    from voice_engine import (
        render_morning_briefing_auto as _ve_morning_auto,
        render_voice_player          as _ve_player,
        build_morning_briefing       as _ve_build_brief,
        build_customer_briefing      as _ve_build_cust_brief,
        render_voice_search          as _ve_voice_search,
        parse_voice_intent           as _ve_parse_intent,
    )
    _VOICE_OK = True
except Exception:
    _VOICE_OK = False
    _ve_morning_auto = _ve_player = _ve_build_brief = _ve_build_cust_brief = None
    _ve_voice_search = _ve_parse_intent = None

try:
    from crm_fortress import (
        search_people       as _ff_search,
        upsert_person       as _ff_upsert,
        get_summary         as _ff_summary,
        get_timeline        as _ff_timeline,
        log_search          as _ff_log_search,
        add_to_garbage      as _ff_add_garbage,
        is_garbage          as _ff_is_garbage,
        restore_from_garbage as _ff_restore_garbage,
        list_garbage        as _ff_list_garbage,
        merge_person_smart  as _ff_merge_smart,
    )
    _FORTRESS_OK = True
except Exception:
    _FORTRESS_OK = False
    _ff_search = _ff_upsert = _ff_summary = None
    _ff_timeline = _ff_log_search = _ff_add_garbage = None
    _ff_is_garbage = _ff_restore_garbage = _ff_list_garbage = None
    _ff_merge_smart = None

# ── [Phase 1] 공통 모듈 import ────────────────────────────────────────────────
from shared_components import (
    CUSTOMER_SCHEMA,
    TIER_META,
    STATUS_META,
    customer_form,
    customer_input_form,
    render_customer_list,
    build_deeplink_to_hq,
    build_deeplink_to_crm,
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

# ── [중앙 DB 엔진] db_utils 싱글턴 import ───────────────────────────────────
from db_utils import (
    _get_sb         as _du_get_sb,
    load_customers  as _du_customers,
    load_schedules  as _du_schedules,
    load_schedules_range as _du_range,
    load_schedules_today as _du_schedules_today,
    save_schedule   as _du_save_schedule,
    safe_update_customer as _du_update_cust,
    get_consulting_logs  as _du_consult_logs,
    get_crawl_status     as _du_crawl_status,
    get_crawl_status_list as _du_crawl_list,
    get_person_policies_summary as _du_policies,
    get_person_relationships    as _du_rels,
    get_ai_brief  as _du_ai_brief,
    save_ai_brief as _du_save_ai_brief,
    log_consulting as _du_log_consult,
    get_member           as _du_get_member,
    update_member_pin_hash as _du_pin_update,
)

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="골드키 CRM — 고객상담 앱",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── [GP-DESIGN-V3] 전역 디자인 시스템 즉시 주입 (Single Source of Truth) ────────
try:
    from shared_components import inject_global_gp_design as _crm_igd
    _crm_igd()
except Exception:
    pass

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

/* §2-C [v5 개정] 반응형 레이아웃 엔진 — 태블릿 세로 면역 */
/* ① 480px이상 (태블릿/데스크탑): 콜럼 강제 수평 유지 */
@media (min-width: 480px) {
  [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    flex-direction: row !important;
    align-items: stretch;
    gap: 0.25rem !important;
  }
  [data-testid="column"] {
    min-width: 0 !important;  /* 콜럼 수평 유지; flex-grow 오버라이드 금지(콜럼 비율 보존) */
    overflow: visible !important;
  }
}
/* ② 479px 미만 (소형 폰): 스태킹 허용 */
@media (max-width: 479px) {
  [data-testid="column"] {
    flex: 1 1 100% !important;
    min-width: min(240px, 100%) !important;
    margin-bottom: 0.75rem !important;
  }
  [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
}
/* ③ 패딩 / 메트릭 / 라디오 (768px 이하) */
@media (max-width: 768px) {
  .block-container {
    padding-left: 0.75rem !important;
    padding-right: 0.75rem !important;
  }
  .stMetric, .stDataFrame, .stTable { width: 100% !important; }
  div[data-testid="stRadio"] > div { flex-wrap: wrap !important; }
  div[data-testid="stRadio"] > div > label { flex: 1 1 45% !important; }
}
/* ④ 세로모드 버튼 폰트 자동 축소 (480이상~900px) */
@media (min-width: 480px) and (max-width: 900px) {
  [data-testid="stHorizontalBlock"] button {
    font-size: clamp(.62rem, 1.8vw, .9rem) !important;
    padding: 6px 4px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
  }
  [data-testid="stTextInputRootElement"] { min-width: 0 !important; }
}

/* §2-D 전체 레이아웃 유연성 */
.main .block-container { max-width: 100% !important; }

/* §5-B Streamlit 기본 상단 헤더/툴바 완전 제거 (흰 가림막 차단) */
[data-testid="stHeader"],
[data-testid="stDecoration"],
[data-testid="stToolbar"],
header[data-testid="stHeader"] {
  display: none !important;
  height: 0 !important;
  min-height: 0 !important;
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
    """[GP-SEC §2] URL에서 auth_token + user_id 수신 → HMAC 검증 → 세션 설정.
    crm_pid / crm_screen 파라미터 수신 시 고객 화면 자동 복원 (HQ 복귀 시 포커스 유지).
    """
    _auth_token = st.query_params.get("auth_token", "")
    _user_id    = st.query_params.get("user_id", "")
    if _auth_token and _user_id:
        _valid = False
        try:
            _valid = _sc_verify_sso_token(_auth_token, _user_id)
        except Exception:
            _valid = bool(_auth_token)  # fallback: 토큰 존재만으로 유효 처리
        if _valid:
            st.session_state["crm_authenticated"] = True
            st.session_state["crm_user_id"]       = _user_id
            st.session_state["crm_user_name"]     = st.session_state.get("crm_user_name", "설계사")
            st.session_state["crm_role"]          = "agent"
            st.session_state["crm_token"]         = _auth_token
            # [HQ 복귀 세션 복원] crm_pid: 이전에 보던 고객 자동 복원
            _back_pid    = st.query_params.get("crm_pid", "")
            _back_screen = st.query_params.get("crm_screen", "contact")
            if _back_pid:
                st.session_state["crm_selected_pid"] = _back_pid
                st.session_state["crm_spa_screen"]   = _back_screen
            st.query_params.clear()  # [GP-SEC §2] SSO 토큰 수신 즉시 URL에서 삭제
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
                        # [db_utils §8] gk_members 조회 — 독자 클라이언트 제거
                        _crm_member = _du_get_member(_cn)
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
                                        _du_pin_update(_cn, _new_h)  # [db_utils §8]
                                    except Exception:
                                        pass
                                _uid = _crm_member.get("user_id", _cn)
                                # [GP-SEC §RBAC Issue-4] CRM은 설계사/관리자 전용 — customer 즉시 차단
                                _db_role = _crm_member.get("user_role", "")
                                if _db_role == "customer":
                                    st.error("🚫 일반 고객은 [HQ] 앱의 고객 전용 포털을 이용해 주십시오.")
                                    st.stop()
                                # [GP-SEC §2 Issue-3] HMAC 정식 토큰 생성 — HQ verify_sso_token 호환
                                # 공식: HMAC(ENCRYPTION_KEY, user_id.encode()).hexdigest()[:32]
                                try:
                                    import hmac as _crm_hmac
                                    _crm_sec = get_env_secret("ENCRYPTION_KEY", "gk_token_secret_2026")
                                    if isinstance(_crm_sec, bytes):
                                        _crm_sec = _crm_sec.decode()
                                    _crm_tok = _crm_hmac.new(
                                        _crm_sec.encode(), _uid.encode(), "sha256"
                                    ).hexdigest()[:32]
                                except Exception:
                                    _crm_tok = ""
                                st.session_state["crm_authenticated"] = True
                                st.session_state["crm_user_id"]       = _uid
                                st.session_state["crm_user_name"]     = _cn
                                st.session_state["crm_role"]          = "agent"
                                st.session_state["crm_token"]         = _crm_tok
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

# ── [GP-DB 싱글턴] Supabase 클라이언트 — db_utils._get_sb() 의존 ─────────────────────
_sb = _du_get_sb()  # 독자 create_client 제거 — 중앙 엔진 단일 접속점 사용

# ── [db_utils §1] 고객 목록 로드 — 60초 캐시 위임 ──────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def _load_customers(agent_id: str, query: str = "") -> list:
    return _du_customers(agent_id, query)

# ── [db_utils §2] 일정 로드 ────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def _load_schedules_today(agent_id: str) -> list:
    return _du_schedules_today(agent_id)

# ══════════════════════════════════════════════════════════════════════════════
# 헤더
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);padding:10px 20px;
  border-radius:10px;border:1px dashed #3b82f6;margin-bottom:2px;">
  <div style="display:flex;align-items:center;justify-content:space-between;">
    <div>
      <span style="font-size:1.3rem;font-weight:900;color:#1e3a8a;">📱 골드키 CRM</span>
      <span style="font-size:0.78rem;color:#2563eb;margin-left:10px;">고객상담 앱</span>
    </div>
    <div style="font-size:0.82rem;color:#374151;font-weight:700;">{_user_name} 설계사</div>
  </div>
  <div style="text-align:center;margin-top:5px;">
    <span style="font-size:0.95rem;font-weight:900;color:#1e3a8a;">👥 전체 고객 대시보드</span>
    <span style="font-size:0.78rem;color:#64748b;margin-left:8px;">고객 선택 → 6대 메뉴</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── [GP-SEC §4] 브라우저 Back 세션 보호 JS ────────────────────────────────────
# popstate(뒤로가기) 감지 시 현재 URL로 재 pushState → 실제 뒤로가기 차단
# 로그인 상태에서 물리적 Back 버튼을 눌러도 로그인 화면으로 튕기지 않음
import streamlit.components.v1 as _crm_jcomp
_crm_jcomp.html("""
<script>
(function() {
  if (window.__gk_back_guard) return;
  window.__gk_back_guard = true;
  // 현재 URL을 히스토리에 한 번 더 push → back 1회 흡수
  history.pushState(null, '', window.location.href);
  window.addEventListener('popstate', function(e) {
    // 뒤로가기 감지 즉시 현재 URL로 다시 push (이탈 차단)
    history.pushState(null, '', window.location.href);
  });
})();
</script>""", height=0)

# ══════════════════════════════════════════════════════════════════════════════
# [GP SPA §0] 아웃룩 컴포넌트 + DB 유틸 로드 (st.tabs 금지)
# ══════════════════════════════════════════════════════════════════════════════
try:
    from components import (
        apply_gp_pastel_theme,
        inject_outlook_css,
        inject_responsive_css,
        render_radio_spa_nav,
        render_outlook_customer_list,
        render_mini_calendar,
        render_sync_badge,
        손보사_standard_form,
    )
    apply_gp_pastel_theme()
    inject_responsive_css()
    _OUTLOOK_OK = True
except Exception:
    _OUTLOOK_OK = False
    st.markdown("""<style>
[data-testid="stApp"],[data-testid="stAppViewContainer"]>.main{background:#F8FBFA!important;}
.gp-memo{background:#FDFD96;border:1px dashed #d97706;border-radius:8px;padding:10px 14px;}
.gp-sched{background:#E6E6FA;border:1px solid #c4b5fd;border-radius:8px;padding:8px 12px;margin-bottom:6px;}
.gp-card{background:#ffffff;border:1px dashed #000;border-radius:10px;padding:12px 16px;margin-bottom:10px;}
/* [GP-PREMIUM] 프리미엄 디자인 — text-shadow + gradient box */
.premium-gradient-box{
  background:linear-gradient(135deg,#dbeafe 0%,#eff6ff 50%,#f0f8ff 100%);
  border:1px solid #93c5fd;border-radius:12px;
  padding:14px 18px;margin-bottom:12px;
  box-shadow:0 2px 10px rgba(59,130,246,0.12);
}
.premium-gradient-box .box-title{
  font-size:clamp(14px,1.4vw+10px,17px);font-weight:900;color:#1e3a8a;
  text-shadow:0 1px 3px rgba(0,0,0,0.12);
}
.premium-gradient-box .box-body{
  font-size:clamp(12px,1.1vw+9px,14px);color:#374151;margin-top:4px;
}
/* 흰 텍스트 text-shadow 전역 적용 */
[style*="color:#ffffff"],[style*="color:white"],[style*="color:#fff"]{
  text-shadow:0 1px 3px rgba(0,0,0,0.25) !important;
}
/* [GP-RESPONSIVE v3] 반응형 시스템 — 태블릿 세로 면역 fallback */
@media (min-width: 480px) {
  [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    flex-direction: row !important;
    align-items: stretch;
    gap: 0.25rem !important;
  }
  [data-testid="column"] {
    min-width: 0 !important;
    overflow: visible !important;
  }
}
@media (max-width: 479px) {
  [data-testid="column"] {
    flex: 1 1 100% !important;
    min-width: min(240px, 100%) !important;
    margin-bottom: 12px !important;
  }
  [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
}
@media (max-width: 768px) {
  p, span, label, .stMarkdown { font-size: clamp(12px, 3.5vw, 15px) !important; }
  h1 { font-size: clamp(18px, 5vw, 28px) !important; }
  h2 { font-size: clamp(15px, 4.5vw, 22px) !important; }
  div[data-testid="stRadio"] > div { flex-wrap: wrap !important; }
  div[data-testid="stRadio"] > div > label { flex: 1 1 45% !important; }
  .stDataFrame, .element-container { max-width: 100% !important; overflow-x: auto !important; }
}
@media (min-width: 480px) and (max-width: 900px) {
  [data-testid="stHorizontalBlock"] button {
    font-size: clamp(.62rem, 1.8vw, .9rem) !important;
    padding: 6px 4px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
  }
}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# [GP SPA §1] 상태 초기화
# ══════════════════════════════════════════════════════════════════════════════
if "crm_spa_mode"     not in st.session_state: st.session_state["crm_spa_mode"]     = "list"
if "crm_selected_pid" not in st.session_state: st.session_state["crm_selected_pid"] = ""
if "crm_spa_screen"   not in st.session_state: st.session_state["crm_spa_screen"]   = "contact"
if "crm_list_page"    not in st.session_state: st.session_state["crm_list_page"]    = 1
_CRM_PAGE_SIZE = 10  # [GP-PERF] 한 화면 최대 DOM 행 수 (50 이하 강제)

_spa_mode = st.session_state.get("crm_spa_mode",    "list")
_sel_pid  = st.session_state.get("crm_selected_pid", "")
_sel_cust: dict | None = None
if _sel_pid:
    _sel_cust = next((_c for _c in _load_customers(_user_id) if _c.get("person_id") == _sel_pid), None)

# ══════════════════════════════════════════════════════════════════════════════
# [GP SPA §2] MODE: LIST — 아웃룩 고객 목록
# ══════════════════════════════════════════════════════════════════════════════
if _spa_mode == "list":
    # ── [GP-VOICE §5] 핸즈프리 CRM — 모닝 브리핑 자동 기동 ──────────────────
    if _VOICE_OK and _ve_morning_auto:
        try:
            _ve_morning_auto(_user_id, _user_name)
        except Exception:
            pass
    # ── [GP-CALENDAR] 스마트 캘린더 엔진 (calendar_engine.py) ────────────────────
    calendar_engine.render_today_widget(_user_id)
    calendar_engine.render_smart_calendar(_user_id, _load_customers(_user_id))
    st.markdown("<hr style='border-top:1px solid #e5e7eb;margin:10px 0 12px;'>",
                unsafe_allow_html=True)

    # ── HQ 크롤링 상태 실시간 동기화 배지 ───────────────────────────────────
    try:
        _crawl_rows = _du_crawl_list(_user_id, 5)  # [db_utils §10]
        if _crawl_rows:
            _sync_c_row = st.columns(min(len(_crawl_rows), 4))
            for _ci, _cr in enumerate(_crawl_rows[:4]):
                _cs = _cr.get("status", "idle")
                _pid_c = _cr.get("person_id", "")[:6]
                _ts = str(_cr.get("updated_at", ""))[:16].replace("T", " ")
                with _sync_c_row[_ci]:
                    if _OUTLOOK_OK:
                        render_sync_badge(
                            _cs,
                            f"{'⚡ 수집중' if _cs == 'running' else '✅ 완료' if _cs == 'done' else '⏸ 대기'}"
                            f" {_pid_c}… {_ts[11:]}",
                        )
                    else:
                        st.caption(f"{_cs} {_pid_c}…")
        elif _sb:
            if _OUTLOOK_OK:
                render_sync_badge("idle", "⏸ HQ 크롤링 대기 중")
    except Exception:
        pass

    # ── [GP-VOICE §6] 음성 검색 위젯 ─────────────────────────────────────────
    if _VOICE_OK and _ve_voice_search:
        _voice_result = _ve_voice_search(session_key="crm_voice_q", key="crm_vs_main")
        if _voice_result:
            _vi = _ve_parse_intent(_voice_result)
            # [GP-SEARCH] STT 결과 정규화: 띄어쓰기 제거 후 검색 세션에 반영
            _vi_q = (_vi.get("query") or "").replace(" ", "")  # clean_query
            _vi_kw = (_vi.get("filters") or {}).get("keyword", "")
            _target_q = _vi_q or _vi_kw  # 이름 파싱 실패 시 keyword 백폴녵
            if _target_q and not st.session_state.get("spa_search"):
                st.session_state["spa_search"] = _target_q
            if _vi.get("filters"):
                st.session_state["_voice_filters"] = _vi["filters"]
                if _ff_log_search and _sb:
                    _ff_log_search(_sb, _user_id, _voice_result, 0)
    else:
        import streamlit.components.v1 as _crm_vc
        _crm_vc.html(
            "<div style='padding:7px 12px;background:#f8fafc;border:1.5px solid #e2e8f0;"
            "border-radius:12px;font-size:12px;color:#94a3b8;'>"
            "🎤 음성 검색 로드 중... (voice_engine 로드 필요)</div>",
            height=52,
        )

    _sr_c1, _sr_c2 = st.columns([5, 1])
    with _sr_c1:
        _search_q = st.text_input("🔍 고객 이름 / 음성 결과 확인", placeholder="이름 입력 또는 위 마이크 사용...",
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

    # ── [GP-VOICE + GP-SEARCH] 음성 필터 + 키워드 AND 매칭 ───────────────────────
    _vf = st.session_state.get("_voice_filters", {})
    if _vf.get("management_tier"): _all_custs = [c for c in _all_custs if c.get("management_tier") == _vf["management_tier"]]
    if _vf.get("status"):          _all_custs = [c for c in _all_custs if c.get("status") == _vf["status"]]
    if _vf.get("is_favorite"):     _all_custs = [c for c in _all_custs if c.get("is_favorite")]
    if _vf.get("renewal_month"):   _all_custs = [c for c in _all_custs if c.get("auto_renewal_month") == _vf["renewal_month"] or c.get("fire_renewal_month") == _vf["renewal_month"]]
    if _vf.get("renewal_type") == "auto": _all_custs = [c for c in _all_custs if c.get("auto_renewal_month")]
    if _vf.get("renewal_type") == "fire": _all_custs = [c for c in _all_custs if c.get("fire_renewal_month")]
    if _vf.get("keyword"):  # [GP-SEARCH] STT 키워드(memo/name/job 대상 매칭)
        from db_utils import _matches_query as _dq_match, _normalize_query as _dq_norm
        _vf_cq, _vf_tok = _dq_norm(_vf["keyword"])
        _all_custs = [c for c in _all_custs if _dq_match(c, _vf_cq, _vf_tok)]

    # ── [GP-PERF] 페이징: 검색 변경 시 1페이지 리셋 ──────────────────────────
    _cur_page = int(st.session_state.get("crm_list_page", 1))
    _total_cnt = len(_all_custs)
    _paged_custs = _all_custs[:_cur_page * _CRM_PAGE_SIZE]  # 누적 표시

    _cc1, _cc2 = st.columns([3, 1])
    with _cc1:
        st.caption(f"📋 총 {_total_cnt}명 (표시 {len(_paged_custs)}명)")
    with _cc2:
        if _vf:
            if st.button("✕ 음성 필터 해제", key="clr_voice_f", use_container_width=True):
                st.session_state.pop("_voice_filters", None)
                st.session_state.pop("crm_voice_q", None)
                st.rerun()

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

    # ── DataFrame 대시보드 (행 선택 → 6대 메뉴 자동 진입) ─────────────────
    import pandas as _pd_crm
    _TIER_LABEL = {1: "⭐⭐⭐ VVIP", 2: "⭐⭐ 핵심", 3: "⭐ 일반"}
    _STAT_LABEL = {"potential": "가망", "active": "진행중",
                   "contracted": "계약", "closed": "종료"}
    _df_rows = []
    for _c in _paged_custs:
        _df_rows.append({
            "person_id":  _c.get("person_id", ""),
            "이름":       _c.get("name", ""),
            "등급":       _TIER_LABEL.get(_c.get("management_tier", 3), "⭐ 일반"),
            "직업":       _c.get("job", ""),
            "상태":       _STAT_LABEL.get(_c.get("status", ""), _c.get("status", "")),
            "자동차만기": f"{_c.get('auto_renewal_month', '')}월" if _c.get("auto_renewal_month") else "-",
            "화재만기":   f"{_c.get('fire_renewal_month', '')}월" if _c.get("fire_renewal_month") else "-",
            "HQ링크":     build_deeplink_to_hq(
                cid=_c.get("person_id", ""),
                agent_id=st.session_state.get("user_id", ""),
                sector="t3",
                user_id=_user_id,
            ),
        })

    if not _df_rows:
        st.info("조건에 해당하는 고객이 없습니다.")
    elif _total_cnt == 0:
        st.info("등록된 고객이 없습니다. [➕ 신규 등록]을 눌러 추가하세요.")
    else:
        _df_crm = _pd_crm.DataFrame(_df_rows)
        _disp_df = _df_crm[["이름", "등급", "직업", "상태", "자동차만기", "화재만기"]]

        st.markdown(
            "<div style='background:#fff;border:1px solid #EAEAEF;border-radius:10px;"
            "padding:4px 0 0 0;overflow:hidden;'>",
            unsafe_allow_html=True,
        )
        try:
            _df_event = st.dataframe(
                _disp_df,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="spa_df_select",
                height=min(400, 56 + len(_df_rows) * 35),
            )
            _sel_rows = _df_event.selection.rows if hasattr(_df_event, "selection") else []
            if _sel_rows:
                _sr_idx = _sel_rows[0]
                _sr_pid = _df_rows[_sr_idx]["person_id"]
                # [GP-지시1] 자동 이동 제거 — 액션 그리드에서 메뉴를 선택하여 이동
                if st.session_state.get("crm_selected_pid") != _sr_pid:
                    st.session_state["crm_selected_pid"] = _sr_pid
                    st.rerun()
        except Exception:
            if _OUTLOOK_OK:
                render_outlook_customer_list(_all_custs, _sel_pid)
            else:
                render_customer_list(_all_custs, show_deeplink=True, agent_tab="t3")
        st.markdown("</div>", unsafe_allow_html=True)

        # ── [GP-지시1] 고객 선택 액션 그리드 ─────────────────────────────────
        _list_sel_pid  = st.session_state.get("crm_selected_pid", "")
        _list_sel_cust = next((_c for _c in _all_custs
                               if _c.get("person_id") == _list_sel_pid), None) if _list_sel_pid else None
        if _list_sel_cust:
            _cn2 = _list_sel_cust.get("name", "")
            _ct2 = _list_sel_cust.get("management_tier", 3)
            _tm2 = TIER_META.get(_ct2, TIER_META[3])
            st.markdown(
                f"<div style='background:#eff6ff;border:1px dashed #3b82f6;border-radius:10px;"
                f"padding:10px 14px;margin:10px 0;display:flex;align-items:center;gap:10px;'>"
                f"<span style='background:{_tm2['bg']};color:{_tm2['color']};font-weight:900;"
                f"width:32px;height:32px;border-radius:50%;display:flex;align-items:center;"
                f"justify-content:center;flex-shrink:0;'>{(_cn2 or '?')[0]}</span>"
                f"<span style='font-size:1rem;font-weight:900;color:#1e3a8a;'>{_cn2}</span>"
                f"<span style='font-size:0.75rem;color:#3b82f6;font-weight:700;margin-left:auto;'>"
                f"{_tm2['icon']} {_tm2['label']} — 아래 메뉴를 선택하세요</span></div>",
                unsafe_allow_html=True,
            )
            _ag1, _ag2, _ag3 = st.columns(3)
            _ag_actions = [
                ("✏️ 고객정보수정", "contact",  True),
                ("📅 스케줄",       "schedule", False),
                ("🌐 내보험다보여", "nibo",     False),
                ("📊 증권분석",     "analysis", False),
                ("🤖 AI 브리핑",   "ai_brief", False),
                ("💬 카카오 발송",  "kakao",    False),
            ]
            for _aai, (_aal, _aas, _is_pri) in enumerate(_ag_actions):
                with [_ag1, _ag2, _ag3][_aai % 3]:
                    if st.button(_aal, key=f"list_ag_{_aas}",
                                 use_container_width=True,
                                 type="primary" if _is_pri else "secondary"):
                        st.session_state["crm_spa_mode"]   = "customer"
                        st.session_state["crm_spa_screen"] = _aas
                        st.session_state.pop("crm_spa_screen_radio", None)
                        st.rerun()
            _ag_clr_c, _ = st.columns([1, 5])
            with _ag_clr_c:
                if st.button("✕ 해제", key="list_ag_clear", use_container_width=True):
                    st.session_state["crm_selected_pid"] = ""
                    st.rerun()
        else:
            st.caption("💡 고객 행을 클릭하면 6대 액션 메뉴가 나타납니다.")

        # ── [GP-PERF] 더 보기 버튼 (페이징) ─────────────────────────────────
        if _total_cnt > len(_paged_custs):
            _remaining = _total_cnt - len(_paged_custs)
            _mb1, _mb2, _mb3 = st.columns([1, 2, 1])
            with _mb2:
                if st.button(
                    f"⬇ 더 보기 ({_remaining}명 더)",
                    key="crm_load_more",
                    use_container_width=True,
                ):
                    st.session_state["crm_list_page"] = _cur_page + 1
                    st.rerun()

        # HQ 딥링크 빠른 발사 행
        if len(_df_rows) <= 20:
            with st.expander("🚀 HQ 딥링크 빠른 발사", expanded=False):
                for _r in _df_rows[:10]:
                    st.markdown(
                        f"<a href='{_r['HQ링크']}' target='_blank' "
                        f"style='font-size:0.8rem;color:#1d4ed8;margin-right:12px;'>"
                        f"🔗 {_r['이름']}</a>",
                        unsafe_allow_html=True,
                    )

# ══════════════════════════════════════════════════════════════════════════════
# [GP SPA §3] MODE: CUSTOMER — 6대 SPA 화면
# ══════════════════════════════════════════════════════════════════════════════
elif _spa_mode == "customer":
    _spa_screen = st.session_state.get("crm_spa_screen", "contact")

    # ── [GP-PERF] 탭 전환 세션 GC ────────────────────────────────────────────
    _prev_screen = st.session_state.get("_crm_prev_screen", "")
    if _prev_screen and _prev_screen != _spa_screen:
        _GC_KEYS_BY_SCREEN = {
            "nibo":     ["nibo_raw_data", "nibo_ocr_result", "nibo_parsed_policy",
                         "nibo_html_cache", "nibo_screenshot_bytes"],
            "analysis": ["analysis_pdf_bytes", "analysis_result_cache",
                         "gk_sec10_result", "ps_req_pending"],
            "ai_brief": ["ai_brief_full_text", "ai_brief_stream_buffer"],
            "kakao":    ["kakao_preview_html", "kakao_send_log"],
        }
        for _gc_key in _GC_KEYS_BY_SCREEN.get(_prev_screen, []):
            st.session_state.pop(_gc_key, None)
    st.session_state["_crm_prev_screen"] = _spa_screen

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
        # ── [GP-VOICE §4] 핸즈프리 CRM — 고객 상세 진입 시 AI 브리핑 보이스 ─────
        if _VOICE_OK and _ve_player and _ve_build_cust_brief:
            try:
                _vp_cust_key  = f"crm_cust_vp_{_sel_pid}"
                _vp_ptype_key = f"{_vp_cust_key}_ptype"
                _vp_ptype     = st.session_state.get(_vp_ptype_key, "Emotional")
                _vp_text      = _ve_build_cust_brief(_sel_cust, _vp_ptype)
                _auto_play_cv = not st.session_state.get(f"_cust_briefed_{_sel_pid}", False)
                _ve_player(
                    _vp_text,
                    personality_type=_vp_ptype,
                    key=_vp_cust_key,
                    auto_play=_auto_play_cv,
                    compact=False,
                )
                st.session_state[f"_cust_briefed_{_sel_pid}"] = True
            except Exception:
                pass

    _crm_menus = [
        ("📋 고객 마스터",  "contact"),
        ("👥 고객 DB 관리", "db_manage"),
        ("📅 스케줄",       "schedule"),
        ("🌐 내보험다보여",  "nibo"),
        ("📊 증권분석",      "analysis"),
        ("🤖 AI 브리핑",    "ai_brief"),
        ("💬 카카오 발송",  "kakao"),
        ("⚙️ 연동/설정",   "settings"),
    ]
    if _OUTLOOK_OK:
        _spa_screen = render_radio_spa_nav(
            _crm_menus,
            session_key="crm_spa_screen",
            back_mode_key="crm_spa_mode",
            back_pid_key="crm_selected_pid",
        )
    else:
        _scr_opts = {m[0]: m[1] for m in _crm_menus}
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

    # ── SCREEN 1: 👥 연락처 상세 (항상 보이는 아웃룩 2-pane 레이아웃) ─────────────
    if _spa_screen == "contact":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "📋 고객 마스터 데이터 & 통합 상담 — GCS 양방향 동기화 · 손보사 표준 정보 관리</div>",
            unsafe_allow_html=True,
        )
        if not _sel_cust:
            st.info("고객을 먼저 선택해 주세요.")
        else:
            _lbl_map = {"potential": "가망", "active": "진행중",
                        "contracted": "계약", "closed": "종료"}
            _pane_l, _pane_r = st.columns([5, 5])

            # ── LEFT PANE: 고객 요약 카드 (항상 표시) ──────────────────────────
            with _pane_l:
                st.markdown(
                    "<div style='background:#F8FBFA;border:1px solid #EAEAEF;"
                    "border-radius:10px;padding:14px;'>",
                    unsafe_allow_html=True,
                )
                _tm_l = TIER_META.get(_sel_cust.get("management_tier", 3), TIER_META[3])
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:12px;'>"
                    f"<div style='width:44px;height:44px;border-radius:50%;"
                    f"background:{_tm_l['bg']};display:flex;align-items:center;"
                    f"justify-content:center;font-size:1.3rem;font-weight:900;"
                    f"color:{_tm_l['color']};flex-shrink:0;'>"
                    f"{(_sel_cust.get('name') or '?')[0]}</div>"
                    f"<div><div style='font-size:1.05rem;font-weight:900;color:#1e293b;'>"
                    f"{_sel_cust.get('name','')}</div>"
                    f"<span style='font-size:0.7rem;font-weight:900;padding:1px 8px;"
                    f"border-radius:10px;background:{_tm_l['bg']};color:{_tm_l['color']};'>"
                    f"{_tm_l['icon']} {_tm_l['label']}</span>"
                    f"<span style='font-size:0.72rem;color:#64748b;margin-left:6px;'>"
                    f"{_lbl_map.get(_sel_cust.get('status',''),'-')}</span>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                _flds_summary = [
                    ("연락처",    decrypt_pii(_sel_cust.get("contact", ""))),
                    ("생년월일",  _sel_cust.get("birth_date", "") or "-"),
                    ("성별",      _sel_cust.get("gender", "") or "-"),
                    ("직업",      _sel_cust.get("job", "") or "-"),
                    ("주소",      _sel_cust.get("address", "") or "-"),
                    ("자동차만기", f"{_sel_cust.get('auto_renewal_month','')}월"
                                  if _sel_cust.get("auto_renewal_month") else "-"),
                    ("화재만기",  f"{_sel_cust.get('fire_renewal_month','')}월"
                                  if _sel_cust.get("fire_renewal_month") else "-"),
                    ("최종수정",  str(_sel_cust.get("updated_at", ""))[:10] or "-"),
                ]
                for _lbl_s, _fv_s in _flds_summary:
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;"
                        f"padding:5px 0;border-bottom:1px solid #EAEAEF;font-size:0.8rem;'>"
                        f"<span style='color:#64748b;font-weight:700;'>{_lbl_s}</span>"
                        f"<span style='color:#1e293b;font-weight:500;'>{_fv_s}</span></div>",
                        unsafe_allow_html=True,
                    )
                _sp_flags = []
                if _sel_cust.get("has_motorcycle"):       _sp_flags.append("🏍️ 이륜차")
                if _sel_cust.get("is_commercial_driver"): _sp_flags.append("🚛 유상운송")
                if _sel_cust.get("has_foreign_stay"):     _sp_flags.append("✈️ 해외장기체류")
                if _sp_flags:
                    st.markdown(
                        f"<div style='background:#fef3c7;border:1px dashed #f59e0b;border-radius:8px;"
                        f"padding:8px 12px;font-size:0.82rem;font-weight:900;color:#92400e;margin-top:10px;'>"
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
                if _sel_pid:
                    _logs_c = _du_consult_logs(_user_id, _sel_pid, limit=3)  # [db_utils §9]
                    if _logs_c:
                        st.markdown(
                            "<div style='font-size:0.72rem;color:#6b7280;margin-top:10px;"
                            "border-top:1px solid #EAEAEF;padding-top:6px;'>📋 최근 상담 이력</div>",
                            unsafe_allow_html=True,
                        )
                        for _lc in _logs_c:
                            _lt_icon = {"kakao_sent": "💬", "ai_brief": "🤖",
                                        "nibo": "🌐", "manual": "✏️"}.get(
                                _lc.get("log_type", ""), "📋")
                            st.markdown(
                                f"<div style='font-size:0.75rem;padding:3px 0;"
                                f"border-bottom:1px dotted #EAEAEF;'>"
                                f"{_lt_icon} {str(_lc.get('created_at',''))[:10]} "
                                f"{str(_lc.get('content',''))[:40]}</div>",
                                unsafe_allow_html=True,
                            )
                st.markdown("</div>", unsafe_allow_html=True)

            # ── RIGHT PANE: 실단 통합 상담 동선 ────────────────────────────────
            with _pane_r:
                _tri_sess_key = f"crm_trinity_res_{_sel_pid}"

                # ── [섹션 A] 상담 브리핑 카드 ──────────────────────────────
                st.markdown(
                    "<div style='background:#eff6ff;border:1px solid #bfdbfe;"
                    "border-radius:12px;padding:10px 14px;margin-bottom:8px;'>"
                    "<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;"
                    "border-bottom:2px solid #bfdbfe;padding-bottom:4px;margin-bottom:8px;'>"
                    "📊 섹션 A — 상담 브리핑</div>",
                    unsafe_allow_html=True,
                )
                _a_items = [
                    ("충 월납보험료",  f"{_sel_cust.get('monthly_premium',0):,.0f}원"),
                    ("유지 계약수",    f"{_sel_cust.get('contract_count',0)}건"),
                    ("관리등급",        f"Tier {_sel_cust.get('management_tier',3)}"),
                    ("주요 리스크",     " ".join(filter(None, [str(_sel_cust.get('risk_note','')), str(_sel_cust.get('driving_status',''))]))),
                ]
                for _ak, _av in _a_items:
                    st.markdown(
                        f"<div style='display:flex;justify-content:space-between;"
                        f"font-size:0.78rem;padding:2px 0;border-bottom:1px dotted #dbeafe;'>"
                        f"<span style='color:#64748b;'>{_ak}</span>"
                        f"<span style='font-weight:700;color:#1e293b;'>{_av}</span></div>",
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)

                # ── [섹션 B] 트리니티 가처분 소득 산출기 ────────────────────
                st.markdown(
                    "<div style='background:#fffbeb;border:1px solid #fbbf24;"
                    "border-radius:12px;padding:12px 14px;margin-bottom:8px;'>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div style='font-size:0.82rem;font-weight:900;color:#92400e;"
                    "border-bottom:2px solid #fbbf24;padding-bottom:4px;margin-bottom:10px;'>"
                    "💡 섹션 B — 트리니티 가처분 소득 산출기 (HQ 동일 공식)</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div style='font-size:0.78rem;font-weight:900;color:#78350f;"
                    "margin-bottom:6px;line-height:1.45;word-break:keep-all;'>"
                    "💰 월 건강보험료 납부액 입력"
                    "<br><span style='font-weight:500;font-size:0.72rem;color:#92400e;'>"
                    "(가처분 소득 산출 &amp; 트리니티 산출 기초)</span></div>",
                    unsafe_allow_html=True,
                )
                _nhis_init = int(st.session_state.get(f"crm_nhis__{_sel_pid}", 0))
                _tri_ic, _tri_bc = st.columns([3, 2])
                with _tri_ic:
                    _nhis_val = st.number_input(
                        "월 건강보험료(원)", min_value=0, max_value=2_000_000,
                        value=_nhis_init, step=10_000,
                        key=f"crm_nhis_inp_{_sel_pid}", label_visibility="collapsed",
                    )
                    st.caption("직장인: 보수월액×7.09%  |  지역가입자: 부과점수×208.4원")
                with _tri_bc:
                    st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
                    if st.button(
                        "🚀 AI 분석 필요 보험가액 산출 (트리니티 산출법)",
                        key=f"crm_tri_calc_{_sel_pid}", type="primary", use_container_width=True,
                    ):
                        if _nhis_val > 0:
                            _ART32_RATE = 0.0709
                            _m_inc = _nhis_val / _ART32_RATE
                            _d_val = _m_inc / 30
                            st.session_state[_tri_sess_key] = {
                                "nhis": _nhis_val, "monthly": _m_inc, "daily": _d_val,
                                "gap_injury":    min(_d_val, 70_000),
                                "gap_disease":   min(_d_val, 100_000),
                                "disability_2yr": _m_inc * 24,
                                "stroke_18":      _m_inc * 18,
                                "dementia_6":     _m_inc * 6,
                                "cancer_min":     100_000_000,
                                "cancer_rec":     300_000_000,
                            }
                            st.session_state[f"crm_nhis__{_sel_pid}"] = _nhis_val
                        else:
                            st.warning("월 건강보험료를 입력해 주세요.")

                _tri_res = st.session_state.get(_tri_sess_key)
                if _tri_res:
                    st.markdown(
                        "<div style='background:#eff6ff;border:1px solid #bfdbfe;"
                        "border-radius:8px;padding:10px 14px;margin-top:10px;'>"
                        "<div style='font-size:0.78rem;font-weight:900;color:#1e3a8a;"
                        "border-bottom:1px solid #bfdbfe;padding-bottom:4px;margin-bottom:8px;'>"
                        "🧠 AI 가입 결과 보고서 요약</div>",
                        unsafe_allow_html=True,
                    )
                    _res_rows = [
                        ("필요 월 소득",   f"{_tri_res['monthly']:,.0f}원"),
                        ("일일 가치",      f"{_tri_res['daily']:,.0f}원"),
                        ("상해 입원일당",  f"{_tri_res['gap_injury']:,.0f}원"),
                        ("질병 입원일당",  f"{_tri_res['gap_disease']:,.0f}원"),
                        ("장해(2년)",     f"{_tri_res['disability_2yr']:,.0f}원"),
                        ("뇌혁줘(18M)",   f"{_tri_res['stroke_18']:,.0f}원"),
                        ("암 최소",      f"{_tri_res['cancer_min']:,.0f}원"),
                        ("암 권장",      f"{_tri_res['cancer_rec']:,.0f}원"),
                    ]
                    _r1, _r2 = st.columns(2)
                    for _ri2, (_rlbl, _rval) in enumerate(_res_rows):
                        with [_r1, _r2][_ri2 % 2]:
                            st.markdown(
                                f"<div style='font-size:0.76rem;padding:3px 0;"
                                f"border-bottom:1px dotted #bfdbfe;'>"
                                f"<span style='color:#64748b;'>{_rlbl}</span>"
                                f"<b style='color:#1e3a8a;margin-left:4px;'>{_rval}</b></div>",
                                unsafe_allow_html=True,
                            )
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                    _hq_detail_url = build_deeplink_to_hq(
                        cid=_sel_pid,
                        agent_id=_user_id,
                        sector="t3",
                        user_id=_user_id,
                    )
                    st.markdown(
                        f"<a href='{_hq_detail_url}' target='_blank' style='"
                        "display:inline-block;background:#eff6ff;color:#1e3a8a;"
                        "border:1px solid #bfdbfe;border-radius:6px;padding:4px 10px;"
                        "font-size:0.72rem;font-weight:900;text-decoration:none;"
                        "white-space:nowrap;'>📊 상세 상담 이동 →</a>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                    if st.button("🔄 결과 초기화", key=f"crm_tri_reset_{_sel_pid}",
                                 use_container_width=True):
                        st.session_state.pop(_tri_sess_key, None)
                        st.rerun()
                else:
                    st.caption("💡 월 건강보험료 입력 후 버튼을 클릭하면 AI 비협보험 가액이 산출됩니다.")
                st.markdown("</div>", unsafe_allow_html=True)

                # ── [정보 수정 폼] ─────────────────────────────────────────────
                st.markdown(
                    "<div style='background:#ffffff;border:1px dashed #000;"
                    "border-radius:10px;padding:14px;margin-top:10px;'>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;"
                    "border-bottom:2px solid #bfdbfe;padding-bottom:4px;margin-bottom:12px;'>"
                    "✏️ 정보 수정 — GCS 즉시 저장</div>",
                    unsafe_allow_html=True,
                )
                if _OUTLOOK_OK:
                    _upd_data = 손보사_standard_form(_sel_cust, key_prefix=f"spa_cf_{_sel_pid}")
                else:
                    _fn_e = st.text_input("이름", value=_sel_cust.get("name", ""), key=f"sp_fn_{_sel_pid}")
                    _fj_e = st.text_input("직업", value=_sel_cust.get("job", ""), key=f"sp_fj_{_sel_pid}")
                    _fa_e = st.text_input("주소", value=_sel_cust.get("address", ""), key=f"sp_fa_{_sel_pid}")
                    _fm_e = st.text_area("메모", value=_sel_cust.get("memo", ""), height=80, key=f"sp_fm_{_sel_pid}")
                    _upd_data = {**_sel_cust, "name": _fn_e, "job": _fj_e,
                                 "address": _fa_e, "memo": _fm_e}
                _sv1, _sv2 = st.columns(2)
                with _sv1:
                    if st.button("💾 GCS 저장", key=f"spa_save_{_sel_pid}",
                                 type="primary", use_container_width=True):
                        try:
                            customer_input_form(_upd_data, _user_id, _sb)
                            st.success("✅ 저장 완료!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as _ue:
                            st.error(f"저장 오류: {_ue}")
                with _sv2:
                    if st.button("↩️ 새로고침", key=f"spa_reload_{_sel_pid}",
                                 use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

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

        # ══ [GP-CAL §1] 사용자 주도형 수동 동기화 UI (Principle 1) ═════════════
        def sync_external_calendar(uid: str, provider: str = "google") -> dict:
            """
            [GP-CAL §1·§2] Pull 동기화 Placeholder.
            실 구현 시 OAuth 2.0 액세스 토큰으로 Google Calendar / Apple CalDAV API 호출.
            자동 실행 절대 금지 — 사용자 클릭 시에만 호출.
            """
            return {"ok": False, "count": 0,
                    "message": f"[Placeholder] {provider} OAuth 2.0 연동 미완성 — ⚙️ 연동/설정 탭에서 계정 연결 후 사용 가능"}

        _cal_consent_ok = st.session_state.get("cal_sync_consent_agreed", False)
        _sc1, _sc2 = st.columns([3, 1])
        with _sc1:
            st.markdown(
                "<div style='background:#f0fdf4;border:1px solid #86efac;"
                "border-radius:10px;padding:8px 14px;margin-bottom:8px;'>"
                "<span style='font-size:0.78rem;font-weight:700;color:#14532d;'>"
                "📅 <b>외부 캘린더 동기화</b> — 사용자가 직접 클릭할 때만 실행 (자동 수집 없음)"
                "<br><span style='font-size:0.7rem;font-weight:400;'>"
                "Google/Apple 캘린더 연동 시 최신 일정 Pull · OAuth 2.0 표준</span>"
                "</span></div>",
                unsafe_allow_html=True,
            )
            if not _cal_consent_ok:
                st.caption("🔐 로그인 시 [📅 외부 캘린더 연동 동의]에 체크한 경우에만 활성화")
        with _sc2:
            if st.button("🔄 외부\n일정 동기화",
                         key="cal_ext_sync_btn", type="primary",
                         use_container_width=True, disabled=(not _cal_consent_ok)):
                with st.spinner("외부 캘린더에서 일정을 가져오는 중..."):
                    _sr = sync_external_calendar(_user_id)
                if _sr.get("ok"):
                    st.success(f"✅ {_sr.get('count',0)}건 완료")
                    st.rerun()
                else:
                    st.info(f"ℹ️ {_sr.get('message','')}")

        # ── 월 네비게이션 (Prev / 월명 / Next) ──────────────────────────────
        _nav_prev, _nav_title, _nav_next = st.columns([1, 4, 1])
        with _nav_prev:
            if st.button("◀", key="spa_mo_prev", use_container_width=True):
                _pm, _py = (_cal_mo - 1, _cal_yr) if _cal_mo > 1 else (12, _cal_yr - 1)
                st.session_state["spa_cal_ym"] = (_py, _pm)
                st.rerun()
        with _nav_title:
            st.markdown(
                f"<div style='text-align:center;font-size:0.9rem;font-weight:900;"
                f"color:#1e3a8a;padding:4px 0;'>{_cal_yr}년 {_cal_mo}월</div>",
                unsafe_allow_html=True,
            )
        with _nav_next:
            if st.button("▶", key="spa_mo_next", use_container_width=True):
                _nm, _ny = (_cal_mo + 1, _cal_yr) if _cal_mo < 12 else (1, _cal_yr + 1)
                st.session_state["spa_cal_ym"] = (_ny, _nm)
                st.rerun()

        _cal_col, _list_col, _memo_col = st.columns([2, 3, 3])
        with _cal_col:
            st.markdown("<b style='font-size:0.82rem;'>📅 달력</b>", unsafe_allow_html=True)
            if _OUTLOOK_OK:
                _new_sel = render_mini_calendar(_cal_yr, _cal_mo, _sched_dates, _sel_date,
                                                session_key="spa_cal_sel")
                if _new_sel != _sel_date:
                    st.session_state["spa_cal_sel"] = _new_sel
                    st.rerun()
            else:
                _sel_dt = st.date_input("날짜 선택",
                                        value=datetime.date.fromisoformat(_sel_date),
                                        key="spa_cal_dt", label_visibility="collapsed")
                _sel_date = str(_sel_dt)
                st.session_state["spa_cal_sel"] = _sel_date

            # 이번 달 일정 요약 카운트
            _cat_cnt: dict = {}
            for _sc in _month_schs:
                _k = _sc.get("category", "other")
                _cat_cnt[_k] = _cat_cnt.get(_k, 0) + 1
            _cat_icon = {"consult": "💬", "appointment": "📌", "call": "📞", "other": "📋"}
            if _cat_cnt:
                st.markdown(
                    "<div style='background:#F8FBFA;border:1px solid #EAEAEF;"
                    "border-radius:8px;padding:6px 10px;margin-top:6px;font-size:0.75rem;'>"
                    + "".join(
                        f"<span style='margin-right:8px;'>"
                        f"{_cat_icon.get(_k,'📋')}&nbsp;<b>{_v}</b></span>"
                        for _k, _v in _cat_cnt.items()
                    ) + "</div>",
                    unsafe_allow_html=True,
                )

        with _list_col:
            _view_mode = st.radio(
                "보기",
                ["📅 선택일", "📋 전체月 이력"],
                horizontal=True,
                key="spa_sched_view",
                label_visibility="collapsed",
            )
            if _view_mode == "📅 선택일":
                st.markdown(
                    f"<b style='font-size:0.82rem;'>🗓️ {_sel_date} 일정</b>",
                    unsafe_allow_html=True,
                )
                try:
                    _day_schs = _du_schedules(_user_id, _sel_date)  # [db_utils §2]
                except Exception:
                    _day_schs = []
                _sched_to_show = _day_schs
            else:
                st.markdown(
                    f"<b style='font-size:0.82rem;'>📋 {_cal_yr}년 {_cal_mo}월 전체 이력</b>",
                    unsafe_allow_html=True,
                )
                _sched_to_show = _month_schs

            _sched_wrap_h = "420px" if _view_mode == "📋 전체月 이력" else "320px"
            st.markdown(
                f"<div style='height:{_sched_wrap_h};overflow-y:auto;padding-right:4px;'>",
                unsafe_allow_html=True,
            )
            if _sched_to_show:
                for _s in _sched_to_show:
                    _ci = {"consult": "💬", "appointment": "📌",
                           "call": "📞", "other": "📋"}.get(_s.get("category", ""), "📋")
                    _pn = (_s.get("gk_people") or {}).get("name", "")
                    _pn_span  = (f' <span style="font-size:0.72rem;color:#6b7280;">({_pn})</span>'
                                 if _pn else "")
                    _memo_div = (f'<div style="font-size:0.75rem;color:#64748b;margin-top:3px;">'
                                 f'{_s.get("memo","")}</div>' if _s.get("memo") else "")
                    _date_tag = (f'<span style="font-size:0.7rem;color:#9ca3af;">'
                                 f'{_s.get("date","")} </span>'
                                 if _view_mode == "📋 전체月 이력" else "")
                    st.markdown(
                        f"<div style='background:#E6E6FA;border:1px solid #c4b5fd;"
                        f"border-radius:8px;padding:8px 12px;margin-bottom:6px;font-size:0.82rem;'>"
                        f"{_date_tag}"
                        f"<span style='font-size:0.72rem;font-weight:700;color:#7c3aed;'>"
                        f"{_ci} {_s.get('start_time','')}</span>"
                        f"<b style='color:#3b0764;'> {_s.get('title','')}</b>"
                        f"{_pn_span}{_memo_div}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("일정 없음")
            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("➕ 일정 추가", expanded=False):
                _nt1, _nt2 = st.columns(2)
                with _nt1:
                    _new_title = st.text_input("제목 *", key="spa_sched_title")
                    _new_time  = st.text_input("시간 (HH:MM)", value="10:00",
                                               key="spa_sched_time")
                with _nt2:
                    _new_cat = st.selectbox(
                        "분류",
                        ["consult", "appointment", "call", "other"],
                        format_func=lambda x: {
                            "consult": "💬 상담", "appointment": "📌 방문",
                            "call": "📞 통화", "other": "📋 기타",
                        }[x],
                        key="spa_sched_cat",
                    )
                    _new_smemo = st.text_area("메모", key="spa_sched_memo", height=60)
                if st.button("📅 저장", key="spa_sched_save",
                             use_container_width=True, type="primary"):
                    if _new_title:
                        try:
                            _du_save_schedule(  # [db_utils §2]
                                agent_id=_user_id,
                                title=_new_title,
                                date=_sel_date,
                                start_time=_new_time,
                                memo=_new_smemo,
                                category=_new_cat,
                                person_id=_sel_pid,
                            )
                            st.success("✅ 저장!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as _se:
                            st.error(f"오류: {_se}")
                    else:
                        st.warning("제목을 입력해 주세요.")

        with _memo_col:
            # ── 파스텔 옐로우 메모장 ────────────────────────────────────────
            st.markdown(
                "<div style='background:#FDFD96;border:1px solid #f0d000;"
                "border-radius:10px;padding:10px 12px;margin-bottom:8px;'>"
                "<b style='font-size:0.82rem;color:#78350f;'>📝 상담 메모장</b></div>",
                unsafe_allow_html=True,
            )
            _cust_memo_v = _sel_cust.get("memo", "") if _sel_cust else ""
            _new_memo_v = st.text_area(
                "메모 (GCS 저장)",
                value=_cust_memo_v,
                height=160,
                key="spa_memo_pad",
                help="저장 버튼을 누르면 GCS 마스터 DB에 반영됩니다.",
            )
            if st.button("💾 메모 저장", key="spa_memo_save", use_container_width=True):
                if _sel_cust:
                    _ok_memo = _du_update_cust(_sel_pid, {"memo": _new_memo_v}, _user_id)  # [db_utils §5]
                    if _ok_memo:
                        st.success("✅ 메모 저장 완료!")
                        st.cache_data.clear()
                    else:
                        st.error("메모 저장 실패 (네트워크 오류)")

            # ── 다가오는 일정 (이번 달 미래 일정) ───────────────────────────
            st.markdown(
                "<div style='background:#E6E6FA;border:1px solid #EAEAEF;"
                "border-radius:10px;padding:8px 12px;margin-top:8px;'>"
                "<b style='font-size:0.8rem;color:#4c1d95;'>📆 다가오는 일정</b></div>",
                unsafe_allow_html=True,
            )
            _today_str  = datetime.date.today().isoformat()
            _upcoming   = sorted(
                [_sc for _sc in _month_schs if _sc.get("date", "") >= _today_str],
                key=lambda x: (x.get("date", ""), x.get("start_time", "")),
            )[:6]
            if _upcoming:
                for _up in _upcoming:
                    _up_pn = (_up.get("gk_people") or {}).get("name", "")
                    _up_lbl = f"{_up.get('date','')} {_up.get('start_time','')} {_up.get('title','')}"
                    if _up_pn:
                        _up_lbl += f" ({_up_pn})"
                    st.markdown(
                        f"<div style='font-size:0.77rem;padding:4px 8px;"
                        f"border-left:3px solid #7c3aed;margin-bottom:4px;color:#3b0764;'>"
                        f"{_up_lbl}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("다가오는 일정 없음")

            # ── 상담일지 최근 5건 ────────────────────────────────────────────
            if _sel_pid:
                _logs5 = _du_consult_logs(_user_id, _sel_pid, limit=5)  # [db_utils §9]
                if _logs5:
                    with st.expander("📋 상담일지 최근 5건", expanded=False):
                        for _lg in _logs5:
                            _lt = {"kakao_sent": "💬", "ai_brief": "🤖",
                                   "nibo": "🌐", "manual": "✏️"}.get(
                                _lg.get("log_type", ""), "📋")
                            st.caption(
                                f"{_lt} {str(_lg.get('created_at',''))[:10]}  "
                                f"{str(_lg.get('content',''))[:60]}"
                            )

        # ── [카카오 파이프라인 진입점 1] 달력/일정 탭 — 고객 상담 일정 및 안내 문자 발송 ──
        if _sel_cust and _sel_pid:
            st.markdown("<hr style='border-top:1px dashed #000;margin:14px 0 8px;'>", unsafe_allow_html=True)
            st.markdown(
                "<div style='background:linear-gradient(135deg,#fffde7,#fef9c3);border:1px dashed #f59e0b;"
                "border-radius:10px;padding:8px 14px;margin-bottom:8px;'>"
                "<span style='font-size:0.82rem;font-weight:900;color:#92400e;"
                "text-shadow:0 1px 2px rgba(0,0,0,0.10);'>💬 카카오 파이프라인 ① — 일정 안내 문자</span></div>",
                unsafe_allow_html=True,
            )
            _kk1_c1, _kk1_c2 = st.columns([7, 3])
            with _kk1_c1:
                _kk1_msg = st.text_input(
                    "일정 안내 문구",
                    placeholder=f"{_sel_cust.get('name','')}님, 상담 일정 안내드립니다...",
                    key="kk1_msg_input", label_visibility="collapsed",
                )
            with _kk1_c2:
                if st.button("💬 고객 상담 일정 및 안내 문자 발송",
                             key="kk1_send_btn", use_container_width=True, type="primary"):
                    try:
                        from db_utils import send_kakao_report as _kk_send1
                        _kk1_res = _kk_send1(
                            customer_name=_sel_cust.get("name", ""),
                            phone_number=decrypt_pii(_sel_cust.get("contact", "")),
                            report_summary=_kk1_msg or f"{_sel_cust.get('name','')}님, 상담 일정 안내드립니다.",
                            agent_id=_user_id, person_id=_sel_pid,
                            template_id="GP_SCHEDULE_01",
                        )
                        _d = "[미리보기] " if _kk1_res.get("dry_run") else ""
                        st.success(f"✅ {_d}발송 완료!") if _kk1_res.get("ok") else st.error(f"❌ {_kk1_res.get('message','')}")
                    except Exception as _kk1_e:
                        st.error(f"카카오 오류: {_kk1_e}")

    # ── SCREEN 3: 🌐 내보험다보여 (기존 로직 100% 보존) ────────────────────
    elif _spa_screen == "nibo":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "🌐 내보험다보여 — 신용정보 수집 · 트리니티 분석 파이프라인</div>",
            unsafe_allow_html=True,
        )
        # ── 파스텔 크롤링 상태 모니터 ────────────────────────────────────────────
        if _sel_cust:
            try:
                _cs_dict = _du_crawl_status(_sel_cust.get("person_id", ""))  # [db_utils §3]
                _nibo_crawl = [_cs_dict] if _cs_dict else []
                if _nibo_crawl:
                    _cs_n  = _nibo_crawl[0]
                    _cst_n = _cs_n.get("status", "idle")
                    _css_n_map = {
                        "running": ("background:#fef3c7;border:1px solid #f59e0b;", "⚡ 수집 진행 중..."),
                        "done":    ("background:#dcfce7;border:1px solid #16a34a;", "✅ 수집 완료"),
                        "error":   ("background:#fef2f2;border:1px solid #dc2626;", "❌ 수집 오류"),
                        "idle":    ("background:#F8FBFA;border:1px solid #EAEAEF;", "⏸ 대기 중"),
                    }
                    _css_n, _lbl_n = _css_n_map.get(_cst_n, _css_n_map["idle"])
                    _ts_n = str(_cs_n.get("updated_at", ""))[:16].replace("T", " ")
                    st.markdown(
                        f"<div style='{_css_n}border-radius:8px;padding:8px 14px;"
                        f"font-size:0.8rem;margin-bottom:10px;"
                        f"display:flex;justify-content:space-between;align-items:center;'>"
                        f"<span style='font-weight:900;'>📡 HQ 내보험다보여 수집 상태: {_lbl_n}</span>"
                        f"<span style='color:#6b7280;font-size:0.74rem;'>{_ts_n}</span></div>",
                        unsafe_allow_html=True,
                    )
                    if _cst_n == "error" and _cs_n.get("error_msg"):
                        st.caption(f"오류 내용: {str(_cs_n.get('error_msg',''))[:80]}")
                else:
                    st.markdown(
                        "<div style='background:#F8FBFA;border:1px solid #EAEAEF;border-radius:8px;"
                        "padding:8px 14px;font-size:0.8rem;margin-bottom:10px;color:#6b7280;'>"
                        "📡 HQ 수집 상태: 이력 없음 — 아래에서 분석을 시작하세요.</div>",
                        unsafe_allow_html=True,
                    )
            except Exception:
                pass
        if not _sel_cust:
            st.info("고객을 먼저 선택해 주세요.")
        elif not st.session_state.get("nibo_consent_agreed", False):
            st.markdown(
                "<div style='background:#fef9c3;border:1px dashed #fbbf24;border-radius:8px;"
                "padding:6px 12px;margin-bottom:8px;font-size:0.8rem;color:#78350f;font-weight:700;'>"
                "🔐 신용정보 조회 동의 후 이용 가능합니다.</div>",
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
            st.markdown(
                "<div style='background:#f0fdf4;border:1px solid #86efac;"
                "border-radius:8px;padding:8px 14px;margin-bottom:10px;font-size:0.8rem;'>"
                "💡 <b>내보험다보여 일괄 분석</b>은 <b>HQ 앱 → 내보험다보여 탭</b>에서 실행하세요. "
                "아래에서 담보 금액을 직접 입력하거나 빠른 HQ 바로가기를 이용해 주세요."
                "</div>",
                unsafe_allow_html=True,
            )
            st.caption("담보 금액을 직접 입력하여 트리니티 분석을 실행합니다.")
            _t_nhi = st.number_input("월 건강보험료(원)", 0, 2_000_000, 0, 10_000,
                                     key="crm_tri_nhi", help="직장인: 보수월액×7.19%")
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
                    f'background:#dbeafe;color:#1e3a8a;border-radius:8px;padding:8px;'
                    f'font-size:0.82rem;font-weight:900;text-decoration:none;'
                    f'border:1px solid #93c5fd;text-shadow:0 1px 2px rgba(0,0,0,0.08);">{_ql}</a>',
                    unsafe_allow_html=True,
                )

    # ── SCREEN 4: 📊 증권분석 (HQ 딥링크 브릿지) ────────────────────────────
    elif _spa_screen == "analysis":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "📊 증권분석 — Raw Data 백오피스 + HQ 정밀 분석 발사대</div>",
            unsafe_allow_html=True,
        )
        if not _sel_cust:
            st.info("고객을 먼저 선택해 주세요.")
        else:
            _an1, _an2 = st.columns([5, 5])

            with _an1:
                # ── HQ 발사대 ────────────────────────────────────────────────
                st.markdown(
                    "<div style='background:#F8FBFA;border:1px dashed #000;"
                    "border-radius:10px;padding:14px;'>",
                    unsafe_allow_html=True,
                )
                st.markdown("**🚀 HQ 정밀 분석 발사대**")
                _sector_opts = {
                    "KB 7대 보장 분석": "t3", "보험금 청구 상담": "t1",
                    "실손보험 분석": "t2",    "암보험 분석": "cancer",
                    "뇌혈관 분석": "brain",   "심장 분석": "heart",
                    "화재보험 분석": "fire",  "AI 상담 리포트": "home",
                }
                _sel_sector_label = st.selectbox(
                    "📍 분석 섹터", list(_sector_opts.keys()), key="spa_sector_sel",
                )
                _sel_sector = _sector_opts[_sel_sector_label]
                _dl_url = build_deeplink_to_hq(
                    cid=_sel_cust.get("person_id", ""),
                    agent_id=st.session_state.get("user_id", ""),
                    sector=_sel_sector,
                    user_id=_user_id,
                )
                st.markdown(
                    f"<div style='text-align:center;padding:12px 0;'>"
                    f"<a href='{_dl_url}' target='_blank' "
                    f"style='background:#dbeafe;color:#1e3a8a;padding:10px 24px;"
                    f"border-radius:8px;font-size:0.9rem;font-weight:900;"
                    f"text-decoration:none;border:1px solid #93c5fd;'>"
                    f"🚀 {_sel_cust.get('name')} → HQ 분석 시작</a></div>",
                    unsafe_allow_html=True,
                )
                with st.expander("❓ HQ 앱이 열리지 않는다면?", expanded=False):
                    st.caption(f"직접 접속: {HQ_APP_URL}")
                st.markdown("</div>", unsafe_allow_html=True)

            with _an2:
                # ── GCS Raw Data 백오피스 ────────────────────────────────────
                st.markdown(
                    "<div style='background:#F8FBFA;border:1px dashed #000;"
                    "border-radius:10px;padding:14px;'>",
                    unsafe_allow_html=True,
                )
                st.markdown("**🗂️ GCS 원시 데이터 (Raw Data)**")
                _raw_tab = st.radio(
                    "조회",
                    ["🧾 기본 정보", "📋 증권 목록", "🔗 관계망"],
                    horizontal=True,
                    key="spa_raw_tab",
                    label_visibility="collapsed",
                )

                if _raw_tab == "🧾 기본 정보" and _sel_cust:
                    _raw_fields = [
                        ("이름",          _sel_cust.get("name", "")),
                        ("person_id",     _sel_cust.get("person_id", "")[:16]),
                        ("등급",          _sel_cust.get("management_tier", "")),
                        ("생년(나이대)",   _sel_cust.get("birth_year", "")),
                        ("직업",          _sel_cust.get("job", "")),
                        ("직업급수",      _sel_cust.get("job_grade", "")),
                        ("운전유형",      _sel_cust.get("driving_type", "")),
                        ("이륜차여부",    _sel_cust.get("bike_usage", "")),
                        ("자동차만기월",  _sel_cust.get("auto_renewal_month", "")),
                        ("화재만기월",    _sel_cust.get("fire_renewal_month", "")),
                        ("상태",          _sel_cust.get("status", "")),
                        ("소개자",        _sel_cust.get("referrer_name", "")),
                        ("updated_at",   str(_sel_cust.get("updated_at", ""))[:19]),
                    ]
                    for _fn, _fv in _raw_fields:
                        if _fv:
                            st.markdown(
                                f"<div style='display:flex;justify-content:space-between;"
                                f"padding:4px 8px;border-bottom:1px solid #EAEAEF;"
                                f"font-size:0.8rem;'>"
                                f"<span style='color:#64748b;'>{_fn}</span>"
                                f"<b>{_fv}</b></div>",
                                unsafe_allow_html=True,
                            )

                elif _raw_tab == "📋 증권 목록" and _sel_pid:
                    try:
                        _policies_raw = _du_policies(_sel_pid)  # [db_utils §11]
                        if _policies_raw:
                            import pandas as _pd_raw
                            _pol_rows = []
                            for _pr in _policies_raw:
                                _p = _pr.get("policies") or {}
                                _pol_rows.append({
                                    "보험사": _p.get("insurance_company", ""),
                                    "상품명": _p.get("product_name", ""),
                                    "역할":   _pr.get("role_type", ""),
                                    "보험료": f"{_p.get('premium',0):,}원" if _p.get("premium") else "-",
                                    "계약일": str(_p.get("contract_date", ""))[:10],
                                    "만기일": str(_p.get("expiry_date", ""))[:10],
                                })
                            st.dataframe(
                                _pd_raw.DataFrame(_pol_rows),
                                use_container_width=True,
                                height=220,
                            )
                        else:
                            st.caption("등록된 증권 없음")
                    except Exception as _pr_e:
                        st.caption(f"조회 오류: {_pr_e}")

                elif _raw_tab == "🔗 관계망" and _sel_pid:
                    try:
                        _rels_raw = _du_rels(_sel_pid, _user_id)  # [db_utils §11]
                        if _rels_raw:
                            for _rr in _rels_raw:
                                _fn = (_rr.get("from_person") or {}).get("name", "?")
                                _tn = (_rr.get("to_person") or {}).get("name", "?")
                                _rt = _rr.get("relation_type", "")
                                st.markdown(
                                    f"<div style='font-size:0.8rem;padding:5px 8px;"
                                    f"border-left:3px solid #93c5fd;margin-bottom:4px;'>"
                                    f"<b>{_fn}</b> → <span style='color:#1d4ed8;'>{_rt}</span>"
                                    f" → <b>{_tn}</b></div>",
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.caption("등록된 관계망 없음")
                    except Exception as _rel_e:
                        st.caption(f"조회 오류: {_rel_e}")

                st.markdown("</div>", unsafe_allow_html=True)

        # ── [카카오 파이프라인 진입점 2] 증권분석 탭 — AI 분석표 요약 문자 발송 ──
        if _sel_cust and _sel_pid:
            st.markdown("<hr style='border-top:1px dashed #000;margin:14px 0 8px;'>", unsafe_allow_html=True)
            st.markdown(
                "<div style='background:linear-gradient(135deg,#fffde7,#fef9c3);border:1px dashed #f59e0b;"
                "border-radius:10px;padding:8px 14px;margin-bottom:8px;'>"
                "<span style='font-size:0.82rem;font-weight:900;color:#92400e;"
                "text-shadow:0 1px 2px rgba(0,0,0,0.10);'>💬 카카오 파이프라인 ② — AI 분석표 요약 문자</span></div>",
                unsafe_allow_html=True,
            )
            _kk2_c1, _kk2_c2 = st.columns([7, 3])
            with _kk2_c1:
                _kk2_msg = st.text_input(
                    "AI 분석 요약 문구",
                    placeholder=f"{_sel_cust.get('name','')}님 보장 분석 결과를 안내드립니다...",
                    key="kk2_msg_input", label_visibility="collapsed",
                )
            with _kk2_c2:
                if st.button("💬 AI 분석표 요약 문자 발송",
                             key="kk2_send_btn", use_container_width=True, type="primary"):
                    try:
                        from db_utils import send_kakao_report as _kk_send2
                        _kk2_res = _kk_send2(
                            customer_name=_sel_cust.get("name", ""),
                            phone_number=decrypt_pii(_sel_cust.get("contact", "")),
                            report_summary=_kk2_msg or f"{_sel_cust.get('name','')}님 AI 보장 분석 결과를 안내드립니다.",
                            agent_id=_user_id, person_id=_sel_pid,
                            template_id="GP_AI_REPORT_01",
                        )
                        _d2 = "[미리보기] " if _kk2_res.get("dry_run") else ""
                        st.success(f"✅ {_d2}발송 완료!") if _kk2_res.get("ok") else st.error(f"❌ {_kk2_res.get('message','')}")
                    except Exception as _kk2_e:
                        st.error(f"카카오 오류: {_kk2_e}")

    # ── SCREEN 5: 🤖 AI 브리핑 편집기 (5:5 분할 — 좌: 우선순위·일정, 우: 편집기) ────
    elif _spa_screen == "ai_brief":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "🤖 AI 브리핑 편집기 — 우선순위 · GCS 편집 저장 · 상담 시뮬레이터</div>",
            unsafe_allow_html=True,
        )
        today_str_b  = datetime.date.today().strftime("%Y년 %m월 %d일")
        st.caption(f"📅 {today_str_b} 기준")
        _brief_custs = _load_customers(_user_id)
        _brief_schs  = _load_schedules_today(_user_id)
        _today_mo    = datetime.date.today().month

        def _prio_score(c: dict) -> int:
            _s = (4 - c.get("management_tier", 3)) * 100
            if c.get("auto_renewal_month") == _today_mo: _s += 50
            if c.get("fire_renewal_month") == _today_mo: _s += 40
            return _s

        _p3 = sorted(_brief_custs, key=_prio_score, reverse=True)[:3]
        _ab_left, _ab_right = st.columns([5, 5])

        # ── LEFT (5): 오늘의 우선순위 TOP3 + 일정 ────────────────────────────
        with _ab_left:
            st.markdown(
                "<div style='background:#F8FBFA;border:1px solid #EAEAEF;"
                "border-radius:10px;padding:14px;'>",
                unsafe_allow_html=True,
            )
            st.markdown("**🎯 오늘의 우선 고객 TOP 3**")
            for _rk, _c in enumerate(_p3, 1):
                _tm3 = TIER_META.get(_c.get("management_tier", 3), TIER_META[3])
                _rh  = ""
                if _c.get("auto_renewal_month") == _today_mo: _rh += " ⚡ 자동차 만기!"
                if _c.get("fire_renewal_month") == _today_mo: _rh += " ⚡ 화재 만기!"
                _rdl = build_deeplink_to_hq(cid=_c.get("person_id", ""),
                                            agent_id=st.session_state.get("user_id", ""),
                                            sector="t3",
                                            user_id=_user_id)
                st.markdown(
                    f"<div style='background:#ffffff;border:1px dashed #000;border-radius:10px;"
                    f"border-left:4px solid {_tm3['color']};padding:10px 14px;margin-bottom:8px;'>"
                    f"<b>#{_rk} {_c.get('name','')}</b>"
                    f"<span style='font-size:0.7rem;font-weight:900;padding:1px 6px;border-radius:10px;"
                    f"background:{_tm3['bg']};color:{_tm3['color']};margin-left:6px;'>"
                    f"{_tm3['icon']} {_tm3['label']}</span>"
                    f"<div style='font-size:0.78rem;color:#d97706;font-weight:700;'>{_rh}</div>"
                    f"<a href='{_rdl}' target='_blank' style='font-size:0.78rem;color:#1d4ed8;'>"
                    f"🚀 HQ 정밀 분석 →</a></div>",
                    unsafe_allow_html=True,
                )
            if not _p3:
                st.info("등록된 고객이 없습니다.")
            st.markdown(
                "<div style='border-top:1px solid #EAEAEF;padding-top:10px;margin-top:8px;'>"
                "<b style='font-size:0.82rem;'>📅 오늘의 일정</b></div>",
                unsafe_allow_html=True,
            )
            if _brief_schs:
                for _s in _brief_schs:
                    st.markdown(
                        f"<div style='background:#E6E6FA;border:1px solid #c4b5fd;"
                        f"border-radius:8px;padding:8px 12px;margin-bottom:6px;font-size:0.82rem;'>"
                        f"<span style='font-size:0.72rem;font-weight:700;color:#7c3aed;'>"
                        f"🗓️ {_s.get('start_time','')}</span>"
                        f"<b style='color:#3b0764;'> {_s.get('title','')}</b>"
                        f"<div style='font-size:0.75rem;color:#64748b;'>{_s.get('memo','')}</div></div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("오늘 예정된 일정이 없습니다.")
            st.markdown("</div>", unsafe_allow_html=True)

        # ── RIGHT (5): AI 브리핑 편집기 (파스텔 옐로우 #FDFD96 + GCS 저장) ────
        with _ab_right:
            st.markdown(
                "<div style='background:#FDFD96;border:1px dashed #d97706;"
                "border-radius:10px;padding:14px;margin-bottom:12px;'>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:0.82rem;font-weight:900;color:#78350f;"
                "border-bottom:2px solid #f59e0b;padding-bottom:4px;margin-bottom:10px;'>"
                "✏️ AI 브리핑 편집기 — 수치·문구 직접 수정 후 GCS DB 즉시 저장</div>",
                unsafe_allow_html=True,
            )
            _edit_key_b = f"crm_brief_edit_{_user_id}"
            _brief_saved = _du_ai_brief(_user_id, limit=1)  # [db_utils §12]
            _brief_default = (_brief_saved[0].get("brief_text", "") if _brief_saved else
                              st.session_state.get(_edit_key_b, ""))
            _brief_text = st.text_area(
                "브리핑 내용 (수정 후 저장 → GCS DB 즉시 반영)",
                value=_brief_default,
                height=200,
                key=_edit_key_b,
                help="수치·문구를 직접 수정할 수 있습니다. 저장 즉시 마스터 DB에 업데이트됩니다.",
            )
            _bsv1, _bsv2 = st.columns([3, 1])
            with _bsv1:
                if st.button("💾 브리핑 저장 (GCS DB)", key="crm_brief_save",
                             use_container_width=True, type="primary"):
                    if _du_save_ai_brief(_user_id, _brief_text):  # [db_utils §12]
                        st.success("✅ GCS 마스터 DB에 저장되었습니다.")
                    else:
                        st.caption("저장 실패 (네트워크 오류)")
            with _bsv2:
                if st.button("↩️ 초기화", key="crm_brief_reset"):
                    st.session_state.pop(_edit_key_b, None)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("🎮 AI 상담 시나리오 시뮬레이터", expanded=False):
                st.caption("고객 상황 입력 → AI 최적 상담 전략 제시")
                try:
                    from sim_trainer import render_simulation_dashboard as _crm_render_sim
                    _crm_render_sim(compact=True)
                except Exception:
                    _sim_input = st.text_area(
                        "상담 상황 입력",
                        placeholder="예: 35세 남성, 현재 암보험 없음, 월 보험료 30만원 예산...",
                        height=80, key="crm_sim_input",
                    )
                    if st.button("🤖 AI 전략 생성", key="crm_sim_run",
                                 use_container_width=True, type="primary"):
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
                                        f"<div style='background:#F8FBFA;border:1px dashed #000;"
                                        f"border-radius:10px;padding:14px;font-size:0.85rem;line-height:1.8;'>"
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
            "💬 카카오 알림톡 발송 — 단건 발송 · 일괄 발송 관리</div>",
            unsafe_allow_html=True,
        )

        # API 키 공통 로드
        try:
            from shared_components import get_env_secret as _genv_kk
            _kk_api_url = _genv_kk("KAKAO_API_URL", "")
            _kk_api_key = _genv_kk("KAKAO_API_KEY", "")
        except Exception:
            _kk_api_url = _kk_api_key = ""
        _is_dry_run = not (_kk_api_url and _kk_api_key)

        _TMPL_MAP = {
            "GP_AI_REPORT_01": "🤖 AI 분석 리포트",
            "GP_RENEWAL_01":   "🚗 만기 도래 알림",
            "GP_CONSULT_01":   "📞 상담 안내",
            "GP_CUSTOM_01":    "✍️ 맞춤형 메시지",
        }

        # ── 발송 모드 선택 ──────────────────────────────────────────────────
        _kk_mode = st.radio(
            "발송 모드",
            ["📤 단건 발송", "📦 일괄 발송 관리"],
            horizontal=True,
            key="kakao_mode_sel",
            label_visibility="collapsed",
        )

        if _kk_mode == "📤 단건 발송":
            if not _sel_cust:
                st.info("고객을 먼저 선택해 주세요.")
            else:
                _kk_name  = _sel_cust.get("name", "")
                _kk_phone = decrypt_pii(_sel_cust.get("contact", ""))
                _kk_pid   = _sel_cust.get("person_id", "")

                st.markdown(
                    "<div style='background:#f0fdf4;border:1px dashed #16a34a;"
                    "border-radius:10px;padding:8px 14px;font-size:0.78rem;margin-bottom:10px;'>"
                    "<b style='color:#15803d;'>① AI 브리핑 로드</b> → "
                    "<b style='color:#15803d;'>② 템플릿 매핑</b> → "
                    "<b style='color:#15803d;'>③ API 호출</b> → "
                    "<b style='color:#15803d;'>④ 상담일지 자동 기록</b></div>",
                    unsafe_allow_html=True,
                )

                _kk1, _kk2 = st.columns([5, 5])
                with _kk1:
                    st.markdown(
                        "<div style='background:#F8FBFA;border:1px dashed #000;"
                        "border-radius:10px;padding:14px;'>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("**📤 알림톡 발송 설정**")
                    _brief_from_session = st.session_state.get(f"crm_brief_edit_{_user_id}", "")
                    _brief_preview = (
                        _brief_from_session[:80] + "…"
                        if len(_brief_from_session) > 80 else _brief_from_session
                    )
                    _tmpl_id = st.selectbox(
                        "알림톡 템플릿",
                        list(_TMPL_MAP.keys()),
                        format_func=lambda x: _TMPL_MAP.get(x, x),
                        key="kakao_tmpl_sel",
                    )
                    _kk_summary = st.text_area(
                        "발송 내용",
                        value=_brief_preview or f"{_kk_name} 고객님 AI 분석 리포트 — 골드키 AI",
                        height=90, key="kakao_summary_inp",
                        help="AI 브리핑 탭에서 저장한 내용이 자동 로드됩니다.",
                    )
                    if _is_dry_run:
                        st.caption("⚠️ API 키 미설정 → 미리보기 모드")
                    _send_ready = bool(_kk_name and _kk_summary.strip())
                    if st.button("💬 카카오톡 발송", key="kakao_send_btn",
                                 use_container_width=True, type="primary",
                                 disabled=not _send_ready):
                        with st.spinner("발송 처리 중…"):
                            try:
                                from db_utils import send_kakao_report as _dku_kakao
                                _kk_result = _dku_kakao(
                                    customer_name=_kk_name, phone_number=_kk_phone,
                                    report_summary=_kk_summary, agent_id=_user_id,
                                    person_id=_kk_pid, template_id=_tmpl_id,
                                    api_url=_kk_api_url, api_key=_kk_api_key,
                                )
                            except Exception as _ke:
                                _kk_result = {"ok": False, "message": str(_ke)}
                        if _kk_result.get("ok"):
                            _dry_lbl = " (미리보기)" if _kk_result.get("dry_run") else ""
                            st.success(f"✅ {_kk_name} 발송 완료{_dry_lbl}!")
                            if _kk_result.get("dry_run") and _kk_result.get("payload"):
                                with st.expander("📄 페이로드 미리보기"):
                                    import json as _jkk
                                    st.code(_jkk.dumps(_kk_result["payload"],
                                                       ensure_ascii=False, indent=2))
                        else:
                            st.error(f"❌ {_kk_result.get('message','')}")
                    st.markdown("</div>", unsafe_allow_html=True)

                with _kk2:
                    st.markdown(
                        "<div style='background:#F8FBFA;border:1px dashed #000;"
                        "border-radius:10px;padding:14px;'>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("**📋 최근 발송 기록**")
                    try:
                        _kk_logs = _du_consult_logs(_user_id, _kk_pid,
                                                    log_type="kakao_sent", limit=8)  # [db_utils §9]
                        if _kk_logs:
                            for _lg in _kk_logs:
                                st.markdown(
                                    f"<div style='font-size:0.77rem;padding:4px 8px;"
                                    f"border-left:3px solid #fbbf24;margin-bottom:4px;'>"
                                    f"<span style='color:#92400e;'>"
                                    f"{str(_lg.get('created_at',''))[:10]}</span> "
                                    f"{str(_lg.get('content',''))[:55]}</div>",
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.caption("발송 기록 없음")
                    except Exception:
                        st.caption("기록 조회 불가")
                    st.markdown("</div>", unsafe_allow_html=True)

        else:  # ── 일괄 발송 관리 ─────────────────────────────────────────
            st.markdown(
                "<div style='background:#F8FBFA;border:1px dashed #000;"
                "border-radius:10px;padding:14px;margin-bottom:10px;'>",
                unsafe_allow_html=True,
            )
            st.markdown("**📦 일괄 발송 — 대상 고객 선택 & 템플릿 설정**")

            _bulk_tmpl = st.selectbox(
                "공통 템플릿",
                list(_TMPL_MAP.keys()),
                format_func=lambda x: _TMPL_MAP.get(x, x),
                key="kakao_bulk_tmpl",
            )
            _bulk_msg_tpl = st.text_area(
                "공통 발송 내용 ({name} 자리에 고객명 자동 치환)",
                value="{name} 고객님, 안녕하세요. 골드키 AI 설계사입니다. "
                      "보장 분석 리포트를 보내드립니다.",
                height=70,
                key="kakao_bulk_msg",
            )

            # 필터 조건
            _bk_f1, _bk_f2, _bk_f3 = st.columns(3)
            with _bk_f1:
                _bk_tier = st.selectbox("등급 필터", ["전체", "VVIP(1)", "핵심(2)", "일반(3)"],
                                        key="kakao_bk_tier")
            with _bk_f2:
                _bk_mo = st.number_input("만기월 (0=전체)", 0, 12, 0, key="kakao_bk_mo")
            with _bk_f3:
                _bk_stat = st.selectbox("상태 필터", ["전체", "가망", "진행중", "계약"],
                                        key="kakao_bk_stat")

            _bk_custs = _load_customers(_user_id, "")
            _bk_tmap = {"VVIP(1)": 1, "핵심(2)": 2, "일반(3)": 3}
            _bk_smap = {"가망": "potential", "진행중": "active", "계약": "contracted"}
            if _bk_tier != "전체":
                _bk_custs = [c for c in _bk_custs if c.get("management_tier") == _bk_tmap.get(_bk_tier)]
            if _bk_mo:
                _bk_custs = [c for c in _bk_custs
                             if c.get("auto_renewal_month") == _bk_mo
                             or c.get("fire_renewal_month") == _bk_mo]
            if _bk_stat != "전체":
                _bk_custs = [c for c in _bk_custs if c.get("status") == _bk_smap.get(_bk_stat, "")]

            st.caption(f"필터 대상: **{len(_bk_custs)}명**")

            # data_editor로 체크박스 선택
            import pandas as _pd_bulk
            _bk_rows = [{"선택": False, "이름": c.get("name",""),
                         "등급": c.get("management_tier", 3),
                         "상태": c.get("status",""),
                         "_pid": c.get("person_id",""),
                         "_contact": c.get("contact","")}
                        for c in _bk_custs]
            if _bk_rows:
                _bk_df_edit = st.data_editor(
                    _pd_bulk.DataFrame(_bk_rows)[["선택", "이름", "등급", "상태"]],
                    use_container_width=True,
                    key="kakao_bulk_editor",
                    height=min(320, 56 + len(_bk_rows) * 35),
                    disabled=["이름", "등급", "상태"],
                )
                _bk_selected_idx = [
                    i for i, r in _bk_df_edit.iterrows() if r.get("선택", False)
                ]
                _bk_sel_count = len(_bk_selected_idx)
                st.caption(f"✔ 선택된 고객: **{_bk_sel_count}명**")

                if _is_dry_run:
                    st.caption("⚠️ API 키 미설정 → 미리보기(dry-run) 모드")

                if st.button(
                    f"💬 선택 {_bk_sel_count}명에게 일괄 발송",
                    key="kakao_bulk_send_btn",
                    use_container_width=True,
                    type="primary",
                    disabled=(_bk_sel_count == 0),
                ):
                    _bulk_ok = _bulk_fail = 0
                    _bulk_prog = st.progress(0)
                    with st.spinner("일괄 발송 처리 중…"):
                        for _bi, _bix in enumerate(_bk_selected_idx):
                            _bc = _bk_custs[_bix]
                            _b_name  = _bc.get("name", "")
                            _b_phone = decrypt_pii(_bc.get("contact", ""))
                            _b_pid   = _bc.get("person_id", "")
                            _b_msg   = _bulk_msg_tpl.replace("{name}", _b_name)
                            try:
                                from db_utils import send_kakao_report as _dku_kk2
                                _br = _dku_kk2(
                                    customer_name=_b_name, phone_number=_b_phone,
                                    report_summary=_b_msg, agent_id=_user_id,
                                    person_id=_b_pid, template_id=_bulk_tmpl,
                                    api_url=_kk_api_url, api_key=_kk_api_key,
                                )
                                if _br.get("ok"):
                                    _bulk_ok += 1
                                else:
                                    _bulk_fail += 1
                            except Exception:
                                _bulk_fail += 1
                            _bulk_prog.progress((_bi + 1) / _bk_sel_count)
                    _bulk_prog.empty()
                    if _bulk_ok:
                        _dry_sfx = " (미리보기)" if _is_dry_run else ""
                        st.success(f"✅ {_bulk_ok}명 발송 완료{_dry_sfx}!"
                                   + (f"  ❌ {_bulk_fail}명 실패" if _bulk_fail else ""))
                    else:
                        st.error(f"❌ 전체 발송 실패 ({_bulk_fail}명)")
            else:
                st.info("필터 조건에 해당하는 고객이 없습니다.")

            st.markdown("</div>", unsafe_allow_html=True)

    # ── SCREEN 7: 👥 고객 DB 관리 ────────────────────────────────────────────
    elif _spa_screen == "db_manage":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "👥 고객 DB 관리 — Fortress 검색 · 상세 수정 · HQ 딥링크</div>",
            unsafe_allow_html=True,
        )
        _db_l, _db_r = st.columns([3, 7])

        # ── LEFT: Fortress 검색 리스트 ────────────────────────────────────
        with _db_l:
            st.markdown(
                "<div style='background:#f8fafc;border:1px dashed #000;"
                "border-radius:10px;padding:10px;'>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:0.8rem;font-weight:900;color:#1e3a8a;"
                "border-bottom:2px solid #bfdbfe;padding-bottom:4px;margin-bottom:8px;'>"
                "🔍 고객 검색</div>",
                unsafe_allow_html=True,
            )
            _db_q = st.text_input("이름/연락처 검색", key="db_manage_q",
                                   placeholder="검색어 입력…", label_visibility="collapsed")
            _db_all = _load_customers(_user_id, _db_q)
            _db_sel_pid = st.session_state.get("db_manage_sel_pid", "")
            for _dbc in _db_all[:30]:
                _dn  = _dbc.get("name", "")
                _dpi = _dbc.get("person_id", "")
                _dt  = TIER_META.get(_dbc.get("management_tier", 3), {})
                _is_sel = (_dpi == _db_sel_pid)
                _bg = "#eff6ff" if _is_sel else "#fff"
                if st.button(
                    f"{_dt.get('icon','📋')} {_dn}",
                    key=f"db_sel_{_dpi}",
                    use_container_width=True,
                ):
                    st.session_state["db_manage_sel_pid"] = _dpi
                    st.rerun()
            if not _db_all:
                st.caption("검색 결과 없음")
            st.markdown("</div>", unsafe_allow_html=True)

        # ── RIGHT: 상세 수정 폼 + HQ 딥링크 ─────────────────────────────
        with _db_r:
            _db_cust = next(
                (c for c in _load_customers(_user_id, "") if c.get("person_id") == _db_sel_pid),
                None,
            )
            if not _db_cust:
                st.info("← 좌측에서 고객을 선택하세요.")
            else:
                _dn2 = _db_cust.get("name", "")
                _dp2 = _db_cust.get("person_id", "")
                st.markdown(
                    "<div style='background:#fff;border:1px dashed #000;"
                    "border-radius:10px;padding:14px;'>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;"
                    f"border-bottom:2px solid #bfdbfe;padding-bottom:4px;margin-bottom:12px;'>"
                    f"✏️ {_dn2} — 고객 정보 수정</div>",
                    unsafe_allow_html=True,
                )
                if _OUTLOOK_OK:
                    _db_upd = 손보사_standard_form(_db_cust, key_prefix=f"dbm_{_dp2}")
                else:
                    _dbn_e = st.text_input("이름", value=_db_cust.get("name",""), key=f"dbm_n_{_dp2}")
                    _dbj_e = st.text_input("직업", value=_db_cust.get("job",""), key=f"dbm_j_{_dp2}")
                    _dba_e = st.text_input("주소", value=_db_cust.get("address",""), key=f"dbm_a_{_dp2}")
                    _dbm_e = st.text_area("메모", value=_db_cust.get("memo",""), height=60, key=f"dbm_m_{_dp2}")
                    _db_upd = {**_db_cust, "name": _dbn_e, "job": _dbj_e,
                               "address": _dba_e, "memo": _dbm_e}
                _dbb1, _dbb2, _dbb3 = st.columns(3)
                with _dbb1:
                    if st.button("💾 저장", key=f"dbm_save_{_dp2}",
                                 type="primary", use_container_width=True):
                        try:
                            customer_input_form(_db_upd, _user_id, _sb)
                            st.success("✅ 저장 완료!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as _dbe:
                            st.error(f"저장 오류: {_dbe}")
                with _dbb2:
                    if st.button("↩️ 새로고침", key=f"dbm_reload_{_dp2}",
                                 use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()
                with _dbb3:
                    _hq_url = build_deeplink_to_hq(_dp2, _user_id)
                    st.markdown(
                        f"<a href='{_hq_url}' target='_blank'>"
                        f"<button style='width:100%;padding:6px;background:#1e3a8a;color:#fff;"
                        f"border:none;border-radius:6px;font-size:0.78rem;font-weight:700;"
                        f"cursor:pointer;'>🔗 HQ 정밀분석</button></a>",
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)

    # ── SCREEN 8: ⚙️ 연동/설정 ───────────────────────────────────────────────
    elif _spa_screen == "settings":
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "⚙️ 연동/설정 — 외부 캘린더 OAuth 2.0 · Admin-Blind RLS · 계정 관리</div>",
            unsafe_allow_html=True,
        )
        _set_tab_cal, _set_tab_sec, _set_tab_acct = st.tabs(
            ["📅 캘린더 연동", "🔒 보안 현황 (RLS)", "👤 계정 관리"]
        )

        with _set_tab_cal:
            st.markdown(
                "<div style='background:#fffbeb;border:1px solid #fbbf24;"
                "border-radius:10px;padding:12px 14px;margin-bottom:12px;'>"
                "<div style='font-size:0.82rem;font-weight:900;color:#92400e;"
                "border-bottom:2px solid #fbbf24;padding-bottom:4px;margin-bottom:8px;'>"
                "📅 외부 캘린더 연동 (OAuth 2.0) — 합법적 표준 방식</div>"
                "<div style='font-size:0.76rem;color:#78350f;line-height:1.7;'>"
                "✅ <b>자동 동기화 금지</b> — 사용자가 직접 '동기화' 버튼을 클릭할 때만 실행<br>"
                "✅ <b>OAuth 2.0 표준</b> — 기기 내부 DB 직접 접근(Scraping) 절대 금지<br>"
                "✅ <b>언제든 해제</b> — '연동 해제' 버튼으로 즉시 권한 철회 가능"
                "</div></div>",
                unsafe_allow_html=True,
            )
            _cal_cs = st.session_state.get("cal_sync_consent_agreed", False)
            if not _cal_cs:
                st.error("🔐 로그인 시 [📅 외부 캘린더 연동 동의] 항목에 동의 후 이용해 주세요.")
            else:
                st.success("✅ 캘린더 연동 동의 완료 — 아래에서 계정을 연동하세요.")

            st.markdown("<br>", unsafe_allow_html=True)
            _gcal_ok = st.session_state.get("gcal_oauth_connected", False)
            _gc1, _gc2 = st.columns([4, 2])
            with _gc1:
                st.markdown(
                    "<div style='background:#f8fafc;border:1px solid #e2e8f0;"
                    "border-radius:8px;padding:10px 14px;'>"
                    "<b>📅 Google 캘린더</b>"
                    "<br><span style='font-size:0.73rem;color:#64748b;'>"
                    "OAuth 2.0 · 읽기 전용 권한 · 언제든 Google 계정 설정에서 철회 가능</span>"
                    f"<br><span style='font-size:0.72rem;font-weight:700;"
                    f"color:{'#15803d' if _gcal_ok else '#dc2626'};'>"
                    f"{'🟢 연동됨' if _gcal_ok else '⭕ 미연동'}</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            with _gc2:
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                if not _gcal_ok:
                    _gcb = st.checkbox("[필수] 외부 캘린더 접근 동의",
                                       key="gcal_cb", disabled=(not _cal_cs))
                    if st.button("📅 Google 연동", key="gcal_connect_btn",
                                 type="primary", use_container_width=True,
                                 disabled=(not _gcb or not _cal_cs)):
                        st.info("🔧 [Placeholder] 실 구현 시 Google OAuth 2.0 URL로 리디렉션됩니다.")
                else:
                    if st.button("🔌 Google 해제", key="gcal_disc_btn",
                                 use_container_width=True):
                        st.session_state.pop("gcal_oauth_connected", None)
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            _acal_ok = st.session_state.get("acal_oauth_connected", False)
            _ac1, _ac2 = st.columns([4, 2])
            with _ac1:
                st.markdown(
                    "<div style='background:#f8fafc;border:1px solid #e2e8f0;"
                    "border-radius:8px;padding:10px 14px;'>"
                    "<b>🍎 Apple 캘린더 (CalDAV)</b>"
                    "<br><span style='font-size:0.73rem;color:#64748b;'>"
                    "CalDAV 표준 · 앱별 비밀번호 · Apple ID 직접 접근 없음</span>"
                    f"<br><span style='font-size:0.72rem;font-weight:700;"
                    f"color:{'#15803d' if _acal_ok else '#dc2626'};'>"
                    f"{'🟢 연동됨' if _acal_ok else '⭕ 미연동'}</span>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            with _ac2:
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                if not _acal_ok:
                    _acb = st.checkbox("[필수] Apple 캘린더 접근 동의",
                                       key="acal_cb", disabled=(not _cal_cs))
                    if st.button("🍎 Apple 연동", key="acal_connect_btn",
                                 use_container_width=True,
                                 disabled=(not _acb or not _cal_cs)):
                        st.info("🔧 [Placeholder] CalDAV 앱별 비밀번호 방식으로 연결합니다.")
                else:
                    if st.button("🔌 Apple 해제", key="acal_disc_btn",
                                 use_container_width=True):
                        st.session_state.pop("acal_oauth_connected", None)
                        st.rerun()

        with _set_tab_sec:
            st.markdown(
                "<div style='background:linear-gradient(135deg,#1e3a8a,#1d4ed8);"
                "border-radius:12px;padding:14px 18px;'>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:0.85rem;font-weight:900;color:#fff;"
                "border-bottom:1px solid rgba(255,255,255,0.3);"
                "padding-bottom:6px;margin-bottom:10px;'>"
                "🔒 Admin-Blind RLS (Zero-Knowledge) 보안 현황</div>",
                unsafe_allow_html=True,
            )
            for _rk, _rv, _rc in [
                ("Supabase RLS",          "auth.uid()::text = agent_id",         "#bfdbfe"),
                ("고객 DB (gk_people)",   "설계사 본인만 CRUD · 관리자 열람 불가", "#a5f3fc"),
                ("스케줄 (gk_schedules)", "설계사 본인만 CRUD · 교차 열람 차단",  "#a5f3fc"),
                ("PII 암호화",            "Fernet AES-128 · SHA-256",            "#fde68a"),
                ("전송 구간",             "TLS 1.3 (HTTPS) 강제",               "#fde68a"),
                ("관리자 접근",           "IAM 403 차단",                        "#fca5a5"),
            ]:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.1);"
                    f"font-size:0.76rem;'>"
                    f"<span style='color:{_rc};font-weight:700;'>{_rk}</span>"
                    f"<span style='color:#fff;font-size:0.72rem;'>{_rv}</span></div>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
            with st.expander("🗄️ Supabase RLS SQL 가이드", expanded=False):
                st.code(
                    """-- [GP-SEC §3] Admin-Blind RLS
ALTER TABLE gk_people ENABLE ROW LEVEL SECURITY;
CREATE POLICY "agent_iso_people" ON gk_people FOR ALL
    USING (auth.uid()::text = agent_id);

ALTER TABLE gk_schedules ENABLE ROW LEVEL SECURITY;
CREATE POLICY "agent_iso_schedules" ON gk_schedules FOR ALL
    USING (auth.uid()::text = agent_id);

ALTER TABLE gk_consulting_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "agent_iso_logs" ON gk_consulting_logs FOR ALL
    USING (auth.uid()::text = agent_id);

SELECT tablename, rowsecurity FROM pg_tables
WHERE tablename IN ('gk_people','gk_schedules','gk_consulting_logs');""",
                    language="sql",
                )

        with _set_tab_acct:
            st.markdown(
                "<div style='background:#f8fafc;border:1px solid #e2e8f0;"
                "border-radius:10px;padding:12px 14px;'>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;"
                "border-bottom:1px solid #bfdbfe;padding-bottom:4px;margin-bottom:10px;'>"
                "👤 내 계정 정보</div>",
                unsafe_allow_html=True,
            )
            for _albl, _aval in [
                ("사용자 ID",        _user_id[:16] + "…" if len(_user_id) > 16 else _user_id),
                ("이름",             _user_name),
                ("캘린더 동의",      "✅ 동의" if st.session_state.get("cal_sync_consent_agreed") else "⬜ 미동의"),
                ("nibo 동의",        "✅ 동의" if st.session_state.get("nibo_consent_agreed")     else "⬜ 미동의"),
                ("AI 음성 동의",     "✅ 동의" if st.session_state.get("voice_consent_agreed")    else "⬜ 미동의"),
                ("Microsoft Outlook","🟢 연동됨" if st.session_state.get("outlook_oauth_connected") else "⭕ 미연동"),
                ("Google 연동",      "🟢 연동됨" if st.session_state.get("gcal_oauth_connected") else "⭕ 미연동"),
                ("Apple 연동",       "🟢 연동됨" if st.session_state.get("acal_oauth_connected") else "⭕ 미연동"),
            ]:
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:4px 0;border-bottom:1px solid #e2e8f0;font-size:0.8rem;'>"
                    f"<span style='color:#64748b;font-weight:700;'>{_albl}</span>"
                    f"<span style='color:#1e293b;'>{_aval}</span></div>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            # ── [V4] Microsoft Outlook 개별 동의 ─────────────────────────────
            with st.expander("🟦 Microsoft Outlook 연결 (일방향 Read-Only)", expanded=False):
                st.markdown(
                    "<div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;"
                    "padding:10px 14px;font-size:0.78rem;color:#1e3a8a;line-height:1.9;'>"
                    "<b>🔒 Microsoft Outlook 연동 동의 안내</b><br>"
                    "• <b>수집 목적:</b> Outlook 연락처 일방향 가져오기(Read-Only)<br>"
                    "• <b>양방향 동기화(Write) 물리적 차단</b> — 외부 앱 쓰기 절대 불가<br>"
                    "• <b>수집 정보:</b> 이름·연락처 (Microsoft Graph API 미들 처리)<br>"
                    "• <b>저장:</b> PII 암호화(Fernet AES-128) 후 Supabase 보관<br>"
                    "• <b>중복 제거:</b> 전화번호 숫자(normalize_phone) PK 기준 자동 병합<br>"
                    "• <b>개인정보 보호법 제15조:</b> 이용자 권리 보장, 수집일부터 5년 후 파기"
                    "</div>",
                    unsafe_allow_html=True,
                )
                _ol_agreed = st.checkbox(
                    "위 안내를 확인하였으며 Outlook 연락처 가져오기에 동의합니다",
                    key="outlook_consent_cb",
                )
                _ol_c1, _ol_c2 = st.columns(2)
                with _ol_c1:
                    if st.button(
                        "🟦 Outlook 연결",
                        key="outlook_connect_btn",
                        type="primary",
                        disabled=not _ol_agreed,
                    ):
                        st.session_state["outlook_oauth_pending"] = True
                        st.info(
                            "⚠️ Microsoft Graph API OAuth2 연동 모듈 배포 준비 중입니다.\n"
                            "동의 설정은 저장되었습니다. 연동 모듈 배포 시 자동 활성화됩니다.",
                            icon="ℹ️",
                        )
                with _ol_c2:
                    if st.session_state.get("outlook_oauth_connected"):
                        if st.button("🔌 연결 해제", key="outlook_disconnect_btn"):
                            st.session_state.pop("outlook_oauth_connected", None)
                            st.success("✅ Outlook 연결이 해제되었습니다.")
                            st.rerun()

            # ── [V4] 마이크 수집 법률 고지문 ─────────────────────────────────
            with st.expander("🎤 AI 음성 비서 (마이크 수집 법률 고지)", expanded=False):
                st.markdown(
                    "<div style='background:#f0fdf4;border:1px solid #86efac;border-radius:8px;"
                    "padding:10px 14px;font-size:0.78rem;color:#166534;line-height:1.9;'>"
                    "<b>🔒 음성 데이터 수집 동의 및 법률 고지</b><br>"
                    "• <b>수집 목적:</b> AI 음성 고객 검색·브리핑 서비스 제공<br>"
                    "• <b>수집 항목:</b> 마이크 실시간 음성 (인식 완료 즉시 로컬 파기, 서버 저장 불가)<br>"
                    "• <b>처리 방식:</b> 브라우저 Web Speech API 로컬 전용 처리<br>"
                    "• <b>마이크 활성화 시</b> 브라우저 권한 표시줄에 🔴 아이콘 표시됨<br>"
                    "• <b>정보통신망법 제22조·제49조:</b> 위치·음성정보 수집 동의 보장<br>"
                    "• <b>동의 철회:</b> 아래 '동의 항목 재설정' 버튼 → 브라우저 마이크 차단"
                    "</div>",
                    unsafe_allow_html=True,
                )
                if not st.session_state.get("voice_consent_agreed"):
                    _vc_agree = st.checkbox(
                        "마이크 수집 고지 내용을 확인하였으며 AI 음성 비서 사용에 동의합니다",
                        key="voice_consent_cb_settings",
                    )
                    if _vc_agree and st.button(
                        "🎤 AI 음성 활성화", key="voice_consent_save_btn", type="primary"
                    ):
                        st.session_state["voice_consent_agreed"] = True
                        st.success("✅ AI 음성 비서가 활성화되었습니다.")
                        st.rerun()
                else:
                    st.success("✅ AI 음성 비서 활성화됨 (마이크 동의 완료)")

            # ── [V4] 가비지 블랙리스트 관리 ──────────────────────────────────
            with st.expander("🗑️ 가비지 블랙리스트 (차단 번호 관리)", expanded=False):
                _gb_c1, _gb_c2 = st.columns([3, 1])
                with _gb_c1:
                    _gb_new_phone = st.text_input(
                        "차단할 번호", placeholder="010-xxxx-xxxx",
                        key="gc_new_phone", label_visibility="collapsed",
                    )
                with _gb_c2:
                    _gb_reason = st.selectbox(
                        "사유", ["설계사 거부", "스팸/불유 요청", "전화 사기 의심", "기타"],
                        key="gc_reason_sel", label_visibility="collapsed",
                    )
                _gba1, _gba2 = st.columns(2)
                with _gba1:
                    if st.button("🚫 차단 등록", key="gc_add_btn", type="primary",
                                 disabled=not (_gb_new_phone or "").strip()):
                        if _ff_add_garbage and _sb:
                            _ff_add_garbage(_sb, _gb_new_phone.strip(), _user_id, _gb_reason)
                            st.success(f"✅ {_gb_new_phone} 차단 등록 완료")
                        else:
                            st.warning("crm_fortress 모듈 필요")
                with _gba2:
                    if st.button("🗑 목록 새로고침", key="gc_list_btn"):
                        st.session_state["show_garbage_list"] = not st.session_state.get("show_garbage_list", False)
                if st.session_state.get("show_garbage_list"):
                    _gb_list = (_ff_list_garbage(_sb, _user_id) if _ff_list_garbage and _sb else [])
                    if _gb_list:
                        for _gbr in _gb_list[:20]:
                            _gbc1, _gbc2 = st.columns([5, 1])
                            with _gbc1:
                                st.caption(f"🚫 {_gbr.get('phone_normalized','')} — {_gbr.get('reason','')}")
                            with _gbc2:
                                if st.button("🔓", key=f"gc_rst_{_gbr.get('phone_normalized','')}",
                                             help="차단 해제"):
                                    if _ff_restore_garbage and _sb:
                                        _ff_restore_garbage(_sb, _gbr.get("phone_normalized", ""), _user_id)
                                        st.session_state["show_garbage_list"] = False
                                        st.rerun()
                    else:
                        st.caption("차단된 번호가 없습니다.")

            # ── [V4] AI 상담 타임라인 (최신순) ───────────────────────────────
            with st.expander("🕐 AI 상담 타임라인 (최신순)", expanded=False):
                if _ff_timeline and _sb:
                    _tl_items = _ff_timeline(_sb, _user_id, limit=20)
                    if _tl_items:
                        for _tl in _tl_items:
                            _dt_str = (_tl.get("dt", "") or "")[:16].replace("T", " ")
                            _tl_color = "#1e5ba4" if _tl.get("type") == "consult" else "#64748b"
                            st.markdown(
                                f"<div style='display:flex;gap:8px;padding:5px 0;"
                                f"border-bottom:1px solid #e2e8f0;font-size:0.78rem;"
                                f"word-break:keep-all;overflow-wrap:break-word;'>"
                                f"<span style='color:#94a3b8;white-space:nowrap;min-width:100px;'>{_dt_str}</span>"
                                f"<span style='font-weight:700;color:{_tl_color};'>{_tl.get('title','')}</span>"
                                f"<span style='color:#64748b;margin-left:auto;white-space:nowrap;'>"
                                f"{(_tl.get('detail','') or '')[:25]}</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.caption("아직 기록된 타임라인이 없습니다.")
                else:
                    st.caption("타임라인 기능을 사용하려면 crm_fortress 모듈이 필요합니다.")

            if st.button("🔄 동의 항목 재설정", key="settings_reset_consent_btn"):
                for _ck in ["cal_sync_consent_agreed", "nibo_consent_agreed",
                            "voice_consent_agreed", "gcal_oauth_connected", "acal_oauth_connected",
                            "outlook_oauth_connected", "outlook_oauth_pending"]:
                    st.session_state.pop(_ck, None)
                st.info("동의 항목이 초기화되었습니다. 로그아웃 후 재로그인하여 재동의해 주세요.")

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
            from db_utils import get_all_members as _du_all_members  # [db_utils §8]
            _cadm_list = _du_all_members()
            st.caption(f"전체 등록 회원: {len(_cadm_list)}명")
            if _cadm_list:
                import pandas as _pd_adm
                _cadm_df = _pd_adm.DataFrame([{
                    "이름":  m.get("name", ""),
                    "ID":    str(m.get("user_id", ""))[:10] + "…",
                    "가입일": str(m.get("join_date", ""))[:10],
                } for m in _cadm_list[:30]])
                st.dataframe(_cadm_df, use_container_width=True, hide_index=True)
            if not _du_get_sb():
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

# ── [GP-SEC] 로그아웃 버튼 — 페이지 최하단 고정 ──────────────────────────────
st.markdown("<hr style='border-top:1px solid #e5e7eb;margin:24px 0 8px;'>",
            unsafe_allow_html=True)
_lo_c1, _lo_c2, _lo_c3 = st.columns([3, 4, 3])
with _lo_c2:
    if st.button("🔒 로그아웃", key="crm_logout_btn_bottom", use_container_width=True):
        try:
            _sb_lo2 = _du_get_sb()  # [GP-DB] 중앙 엔진 싱글턴
            if _sb_lo2:
                _sb_lo2.auth.sign_out()
        except Exception:
            pass
        st.session_state.clear()
        st.session_state["_crm_logout_success"] = True
        st.rerun()
st.markdown(
    f"<div style='text-align:center;font-size:0.72rem;color:#9ca3af;padding:4px 0 12px;'>"
    f"🔒 {_user_name} 로그인 중 &nbsp;·&nbsp; "
    f"nibo 동의: {'✅' if st.session_state.get('nibo_consent_agreed') else '⬜'}"
    f"</div>",
    unsafe_allow_html=True,
)

