# crm_app_impl.py — Goldkey AI Masters CRM 2026 (본문 구현)
# 진입점: crm_app.py (껍데기)
"""
[GP 마스터-그림자 Phase 3] 초경량 현장 기동대 CRM — 페르소나: 현장·이동 중 고객관리·일정·메시지·HQ 딥링크
- 복잡한 보험 계산식/정밀 상담 로직 없음 (정밀 분석은 HQ app.py)
- 공통 모듈(shared_components.py) import 전용
- 역할: AI 아침 브리핑 · 고객 리스트 · 일정 · 딥링크 발사대 · (옵션) React Native는 crm_app/ 폴더

[설계 SSOT 문서]
  docs/GOLDKEY_DESIGNER_CONTEXT.md — 앱 역할·연결·부속 구조 요약
  docs/DESIGNER_WORKFLOW.md — Windsurf/Cursor·설계자 워크플로
  Constitution.md — 가이딩 프로토콜(GP) 원문

[동시 구동 방법]
  본 앱(HQ):  streamlit run app.py     --server.port 8501
  CRM 앱:    streamlit run crm_app.py --server.port 8502
  접속 URL:  http://localhost:8501  (HQ)
             http://localhost:8502  (CRM)
"""

import streamlit as st
import datetime
from datetime import datetime as dt_now
import urllib.parse
import os
import calendar_engine

# ── [GP-SEC] 세션 지속성 관리자 ────────────────────────────────────────────────
try:
    from session_manager import (
        init_persistent_session,
        save_session_to_storage,
        check_idle_timeout,
        clear_session,
        update_last_activity
    )
    _SESSION_MANAGER_OK = True
except Exception as _sm_err:
    _SESSION_MANAGER_OK = False
    init_persistent_session = lambda: False
    save_session_to_storage = lambda *args, **kwargs: None
    check_idle_timeout = lambda: False
    clear_session = lambda: None
    update_last_activity = lambda: None

# ── [조건부] voice_engine · crm_fortress · mypage_ui import ───────────────────────────
_MODULE_LOAD_ERRORS: list = []

# [GP-TRUST] 마이페이지 및 신뢰 구축 UI
try:
    from modules.mypage_ui import (
        render_plan_badge,
        render_mypage,
        render_paid_analysis_list,
        get_paid_analysis_list
    )
    _MYPAGE_OK = True
except Exception as _mp_err:
    _MYPAGE_OK = False
    _MODULE_LOAD_ERRORS.append(f"mypage_ui: {_mp_err}")

try:
    from voice_engine import (
        render_time_aware_briefing   as _ve_morning_auto,
        render_voice_player_zephyr   as _ve_player_zephyr,
        build_morning_briefing       as _ve_build_brief,
        build_customer_briefing      as _ve_build_cust_brief,
        render_voice_search          as _ve_voice_search,
        parse_voice_intent           as _ve_parse_intent,
    )
    _VOICE_OK = True
except Exception as _ve_err:
    _VOICE_OK = False
    _ve_morning_auto = _ve_player_zephyr = _ve_build_brief = _ve_build_cust_brief = None
    _ve_voice_search = _ve_parse_intent = None
    _MODULE_LOAD_ERRORS.append(f"voice_engine — {_ve_err}")

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
except Exception as _ff_err:
    _FORTRESS_OK = False
    _ff_search = _ff_upsert = _ff_summary = None
    _ff_timeline = _ff_log_search = _ff_add_garbage = None
    _ff_is_garbage = _ff_restore_garbage = _ff_list_garbage = None
    _ff_merge_smart = None
    _MODULE_LOAD_ERRORS.append(f"crm_fortress — {_ff_err}")

try:
    from modules.kakao_sender import render_send_ui as _ks_render_send_ui
    _KAKAO_SENDER_OK = True
except Exception as _ks_err:
    _KAKAO_SENDER_OK = False
    _ks_render_send_ui = None
    _MODULE_LOAD_ERRORS.append(f"kakao_sender — {_ks_err}")

# ── [Phase 1] 공통 모듈 import ────────────────────────────────────────────────
from blocks.crm_action_grid_block import render_crm_dashboard_action_grid as _render_crm_dashboard_action_grid
from blocks.crm_nav_block import render_crm_dual_nav
from blocks.crm_consultation_center_block import render_crm_consultation_center
from blocks.crm_trinity_block import render_crm_trinity_block
from blocks.crm_nibo_screen_block import render_crm_nibo_screen
from blocks.crm_analysis_screen_block import render_crm_analysis_screen
from blocks.crm_list_inline_panel_block import render_crm_list_inline_panel
from blocks.crm_insurance_contracts_block import render_insurance_contracts
from blocks.crm_scan_block import render_crm_scan_block
from blocks.crm_phase1_network_block import render_network_tagging_panel
from blocks.crm_scan_vault_viewer import render_scan_vault_viewer, render_scan_vault_summary

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
    build_sso_handoff_to_hq,
    HQ_APP_URL,
    CRM_APP_URL,
    get_env_secret,
    get_clean_phone,
    decrypt_pii,
    mask_name,
    mask_phone,
    render_auth_screen as _sc_render_auth_screen,
    verify_sso_token as _sc_verify_sso_token,
    notify_admin_member_error as _sc_notify_admin_error,
    render_member_emergency_btn as _sc_emergency_btn,
    _NIBO_CONSENT_HTML as _crm_nibo_html,
    render_security_sidebar as _sc_render_security_sidebar,
    get_hq_api_base,
    request_hq_analysis_trigger,
    schedule_hq_prewarm_from_crm,
    consent_get,
    consent_set,
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
    upsert_member        as _du_upsert_member,
    update_member_pin_hash as _du_pin_update,
)

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Goldkey_AI_Masters2026 (CRM 고객상담 앱)",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── [GP-SEC] 세션 지속성 초기화 (새로고침/앱전환 시 로그인 유지) ─────────────────
if _SESSION_MANAGER_OK:
    _session_restored = init_persistent_session()
    if _session_restored:
        # 세션 복구 성공 시 로그 (디버그용)
        pass

# ── [GP-TIMEOUT] 60분 비활동 타임아웃 자동 로그아웃 ────────────────────
import time as _time_crm_timeout
_crm_current_time = _time_crm_timeout.time()

# 로그인된 사용자만 타임아웃 체크
if st.session_state.get("user_id") and not st.session_state.get("_logout_flag"):
    # 마지막 활동 시간 초기화
    if "last_activity_time" not in st.session_state:
        st.session_state["last_activity_time"] = _crm_current_time
    
    # 비활동 시간 계산
    _crm_last_activity = st.session_state.get("last_activity_time", _crm_current_time)
    _crm_inactive_duration = _crm_current_time - _crm_last_activity
    
    # 60분(3600초) 초과 시 자동 로그아웃
    if _crm_inactive_duration > 3600:
        _crm_timeout_user = st.session_state.get("user_name", "사용자")
        st.session_state.clear()
        st.warning(f"⏱️ {_crm_timeout_user}님, 60분 동안 활동이 없어 보안을 위해 자동 로그아웃되었습니다.")
        st.info("💡 다시 로그인해 주세요.")
        st.stop()
    
    # 활동 시 타임스탬프 갱신
    st.session_state["last_activity_time"] = _crm_current_time

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
        "🏆 Goldkey_AI_Masters2026 (CRM 고객상담 앱)</div>",
        unsafe_allow_html=True,
    )
    try:
        _sc_render_security_sidebar()
    except Exception:
        pass
    for _merr in _MODULE_LOAD_ERRORS:
        st.caption(f"⚠️ {str(_merr)[:120]}")

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

/* ── 제11조 [반응형 타이포그래피 v2 — Fluid Typography] ────────────── */
/* 기본 텍스트: p/li/span — clamp 상향 조정 */
p, li {
  font-size: clamp(14px, 1.8vw + 9px, 17px) !important;
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
}
/* span은 inline이므로 너무 넓게 덮지 않게 단독 처리 */
span {
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
}
/* .stMarkdown 내부 div — 카드/라벨 텍스트 반응형 */
.stMarkdown div, .element-container .stMarkdown p {
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
}
/* 앱 헤더 — 기기 너비에 비례 확대 */
[data-testid="stAppViewContainer"] span[style*="font-size:1.3rem"],
[data-testid="stAppViewContainer"] span[style*="font-size: 1.3rem"] {
  font-size: clamp(18px, 4.5vw, 26px) !important;
}
[data-testid="stAppViewContainer"] span[style*="font-size:0.95rem"],
[data-testid="stAppViewContainer"] span[style*="font-size: 0.95rem"] {
  font-size: clamp(15px, 3.5vw, 20px) !important;
}
[data-testid="stAppViewContainer"] span[style*="font-size:0.82rem"],
[data-testid="stAppViewContainer"] span[style*="font-size:0.8rem"],
[data-testid="stAppViewContainer"] div[style*="font-size:0.82rem"],
[data-testid="stAppViewContainer"] div[style*="font-size:0.8rem"] {
  font-size: clamp(13px, 2.8vw, 16px) !important;
}
[data-testid="stAppViewContainer"] div[style*="font-size:0.78rem"],
[data-testid="stAppViewContainer"] span[style*="font-size:0.78rem"] {
  font-size: clamp(12px, 2.5vw, 15px) !important;
}
[data-testid="stAppViewContainer"] div[style*="font-size:0.75rem"],
[data-testid="stAppViewContainer"] span[style*="font-size:0.75rem"],
[data-testid="stAppViewContainer"] div[style*="font-size:0.74rem"],
[data-testid="stAppViewContainer"] div[style*="font-size:0.72rem"] {
  font-size: clamp(11px, 2.2vw, 14px) !important;
}
/* 헤딩 */
h1 { font-size: clamp(22px, 5vw, 32px) !important; word-break: keep-all !important; overflow-wrap: break-word !important; }
h2 { font-size: clamp(19px, 4vw, 26px) !important; word-break: keep-all !important; overflow-wrap: break-word !important; }
h3 { font-size: clamp(16px, 3vw, 22px) !important; word-break: keep-all !important; overflow-wrap: break-word !important; }
/* Streamlit 기본 caption/label */
[data-testid="stCaptionContainer"] p,
[data-testid="stWidgetLabel"] p {
  font-size: clamp(12px, 2.2vw, 14px) !important;
}
/* 성과 온도계·TA 리스트·영업메모 등 핵심 UI 텍스트 */
[data-testid="stExpanderDetails"] p,
[data-testid="stExpanderDetails"] li,
[data-testid="stExpanderDetails"] span {
  font-size: clamp(12px, 2vw, 14px) !important;
}
*, *::before, *::after {
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
}

/* ── [GP-SEC] 브라우저 자동완성 전역 차단 ────────────────────────── */
input[type="text"],
input[type="password"],
input[type="email"],
input[type="tel"],
input[type="number"],
textarea {
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  appearance: none !important;
}

/* ══════════════════════════════════════════════════════════════════
   [GP-UX] 시스템 가이드 및 툴팁 전역 삭제 (2026-03-28 신설)
   ⚠️ 긴급 주석 처리: 백화현상 원인 의심 - DOM 충돌 방지
   사용자 정의 label/placeholder 외 모든 시스템 문구 제거
══════════════════════════════════════════════════════════════════ */

/* 1. 폼(Form) 하단의 'Press Enter to submit' 안내 문구 삭제 */
/* [data-testid="stForm"] p { display: none !important; } */

/* 2. 모든 입력창 상단/하단의 시스템 가이드 및 라벨 보조 문구 삭제 */
/* [data-testid="stTextInput"] p, 
[data-testid="stNumberInput"] p, 
[data-testid="stTextArea"] p { display: none !important; } */

/* 3. 툴팁(Tooltip) 아이콘 및 도움말 팝업 강제 삭제 */
/* [data-testid="stTooltipIcon"] { display: none !important; } */

/* 4. 입력창 클릭 시 나타나는 브라우저 기본 포커스 힌트 및 테두리 정리 */
/* input:focus { outline: none !important; box-shadow: none !important; } */

/* 5. 버튼 및 기타 요소의 시스템 힌트 문자 삭제 */
/* .st-emotion-cache-1ae8p30 e1nzilvr4 { display: none !important; } */

/* Streamlit input 필드 타겟팅 */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
  -webkit-appearance: none !important;
  -moz-appearance: none !important;
  appearance: none !important;
}

/* 버튼 key 텍스트 숨김 - 한글 label만 표시 */
button[kind="primary"],
button[kind="secondary"] {
  font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* 버튼 내부 key 텍스트 제거 */
button p {
  display: inline !important;
}
</style>

<script>
// [GP-SEC] 전역 자동완성 차단 JavaScript
(function() {
  function disableAutocomplete() {
    const inputs = document.querySelectorAll('input, textarea');
    inputs.forEach(input => {
      // 일반 입력: autocomplete="off"
      if (input.type === 'text' || input.type === 'email' || input.type === 'tel' || input.type === 'number') {
        input.setAttribute('autocomplete', 'off');
        input.setAttribute('autocorrect', 'off');
        input.setAttribute('autocapitalize', 'off');
        input.setAttribute('spellcheck', 'false');
      }
      // 비밀번호: autocomplete="new-password"
      else if (input.type === 'password') {
        input.setAttribute('autocomplete', 'new-password');
        input.setAttribute('autocorrect', 'off');
        input.setAttribute('autocapitalize', 'off');
        input.setAttribute('spellcheck', 'false');
      }
    });
  }
  
  // 초기 실행
  disableAutocomplete();
  
  // Streamlit rerun 시 재실행
  const observer = new MutationObserver(disableAutocomplete);
  observer.observe(document.body, { childList: true, subtree: true });
  
  // 주기적 체크 (모바일 환경 대응)
  setInterval(disableAutocomplete, 1000);
})();
</script>
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
            # [GP-SEC] 세션 저장 (새로고침 시 로그인 유지)
            if _SESSION_MANAGER_OK:
                save_session_to_storage(_user_id, st.session_state.get("crm_user_name", "설계사"), "agent", _auth_token, _back_screen or "list")
            st.query_params.clear()  # [GP-SEC §2] SSO 토큰 수신 즉시 URL에서 삭제
            return True
    return False

def _is_authenticated() -> bool:
    """[지시3] 60분 보안 타임아웃 검증 포함"""
    if not st.session_state.get("crm_authenticated", False):
        return False
    
    # [지시3] 60분 타임아웃 검사
    from modules.concurrency_guard import check_session_timeout, update_activity_time
    
    last_activity = st.session_state.get("crm_last_activity_time", "")
    if check_session_timeout(last_activity, timeout_minutes=60):
        # 타임아웃 → 세션 파기
        st.session_state.clear()
        st.error(
            "⚠️ **보안 타임아웃 (60분 초과)**\n\n"
            "장시간 활동이 없어 자동 로그아웃되었습니다.\n"
            "PIN 번호로 다시 로그인해 주세요."
        )
        return False
    
    # [지시3] 활동 시간 갱신
    st.session_state["crm_last_activity_time"] = update_activity_time()
    
    return True

# SSO 토큰 수신 처리
if _check_sso_token():
    # DOM 에러 방지: rerun 전 플래그 설정 + 무한 루프 차단
    if not st.session_state.get("_rerun_pending"):
        st.session_state["_rerun_pending"] = True
        st.rerun()
    else:
        # 플래그 해제 (다음 rerun을 위해)
        st.session_state["_rerun_pending"] = False

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
        f'<img src="{_crm_av_src}" loading="eager"'
        ' style="width:clamp(108px,21vw,150px);height:clamp(108px,21vw,150px);'
        'border-radius:50%;border:4px solid #D4AF37;'
        'box-shadow:0 6px 24px rgba(212,175,55,0.45);object-fit:cover;'
        'display:block;margin:0 auto 14px auto;" />'
        if _crm_av_src else
        '<div style="width:clamp(108px,21vw,150px);height:clamp(108px,21vw,150px);border-radius:50%;'
        'background:linear-gradient(135deg,#1e3a8a,#D4AF37);'
        'margin:0 auto 14px auto;border:4px solid #D4AF37;"></div>'
    )
    # ── [GP-RESPONSIVE] 반응형 로그인 화면 CSS ─────────────────────────
    st.markdown("""
    <style>
    /* 전체 컨테이너 가로폭 고정 및 중앙 정렬 */
    .crm-login-container {
        max-width: 680px;
        width: 100%;
        margin: 0 auto;
        padding: 20px;
        overflow-x: hidden;
    }
    /* 모바일 최적화 (768px 이하) */
    @media (max-width: 768px) {
        .crm-login-container {
            max-width: 100%;
            padding: 16px;
        }
        /* 앱 타이틀 - 최상위 위계 */
        .crm-app-title {
            font-size: clamp(1.4rem, 5vw, 2.0rem) !important;
            font-weight: 900 !important;
            line-height: 1.3 !important;
        }
        /* 서브 타이틀 (CRM 고객상담 앱) */
        .crm-app-subtitle {
            font-size: clamp(0.9rem, 3.5vw, 1.1rem) !important;
            font-weight: 700 !important;
        }
        /* 섹션 제목 - 중간 위계 */
        .crm-section-title {
            font-size: clamp(1.0rem, 4vw, 1.2rem) !important;
            font-weight: 900 !important;
        }
        /* 본문 텍스트 */
        .crm-body-text {
            font-size: clamp(0.85rem, 3.5vw, 1.0rem) !important;
            line-height: 1.75 !important;
        }
        /* Streamlit 기본 컨테이너 중앙 정렬 강제 */
        [data-testid="stVerticalBlock"] > div,
        [data-testid="stMarkdownContainer"],
        .stMarkdown {
            max-width: 100% !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
    }
    /* 태블릿 (769px ~ 1024px) */
    @media (min-width: 769px) and (max-width: 1024px) {
        .crm-app-title {
            font-size: 1.8rem !important;
        }
        .crm-app-subtitle {
            font-size: 1.05rem !important;
        }
        .crm-section-title {
            font-size: 1.15rem !important;
        }
        .crm-body-text {
            font-size: 0.95rem !important;
        }
        /* 태블릿 중앙 정렬 */
        [data-testid="stVerticalBlock"] > div,
        [data-testid="stMarkdownContainer"],
        .stMarkdown {
            max-width: 680px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
    }
    /* PC (1025px 이상) */
    @media (min-width: 1025px) {
        .crm-app-title {
            font-size: 2.0rem !important;
        }
        .crm-app-subtitle {
            font-size: 1.1rem !important;
        }
        .crm-section-title {
            font-size: 1.2rem !important;
        }
        .crm-body-text {
            font-size: 1.0rem !important;
        }
    }
    /* 글자 보호 */
    .crm-login-container * {
        word-break: keep-all;
        overflow-wrap: break-word;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(
        f"<div class='crm-login-container'>"
        f"<div style='text-align:center;padding:24px 0 8px;'>"
        f"{_crm_av_html}"
        "<div class='crm-app-title' style='color:#1e3a8a;margin-bottom:8px;'>"
        "🏆 Goldkey_AI_Masters2026</div>"
        "<div class='crm-app-subtitle' style='color:#64748b;margin-bottom:14px;'>(CRM 고객상담 앱)</div>"
        "</div>",
        unsafe_allow_html=True,
    )
        
    
    # ── [GP-ONBOARDING] 12단계 초격차 영업 마스터플랜 안내 ──────────────────
    st.markdown(
        "<div style='max-height:280px;overflow-y:auto;padding:20px;border:1px solid #e2e8f0;"
        "border-radius:12px;background:#f8fafc;'>"
        "<div style='font-size:1.1rem;font-weight:700;color:#0a1628;margin-bottom:14px;"
        "text-align:center;'>💡 Goldkey_AI_Masters2026 (CRM 고객상담 앱) 및 서비스 안내 & 12단계 초격차 영업 마스터플랜</div>"
        "<div style='font-size:0.88rem;color:#374151;line-height:1.7;margin-bottom:16px;'>"
        "'Goldkey_AI_Masters2026'은 '지능형 AI 세일즈 활동 관리 앱(에이젠틱 AI)'을 목표로 설계사를 위한 고객 상담 지원 AI 앱입니다.<br><br>"
        "이 앱은 30년 경력의 FC가 직접 설계하였으며, 실제적인 상담 현장에서 검증된 **'AI 트리니티 계산법(건강보험료 기준 역산법)'**과 'KB손해보험 증권분석 평균가입금액' 로직을 적용했습니다. 개인·법인(CEO)·화재 등 전문 분야의 내용을 지속적으로 업데이트할 예정이며, 설계사 여러분의 고객 상담에 실질적이고 큰 힘이 되리라 믿습니다.<br><br>"
        "'Goldkey_AI_Masters2026'은 상담 청약 단계부터 계약 후 계약관리(연락 스케쥴)까지 전 과정을 지원합니다. 30년 경험을 바탕으로 구축된 12단계의 맞춤형 솔루션을 통해 설계사(FC)님께서 압도적인 성과를 창출할 수 있도록 도와줄 것입니다."
        "</div>"
        "<div style='background:#fff;border-left:4px solid #fbbf24;border-radius:8px;padding:12px 14px;margin-bottom:12px;'>"
        "<div style='font-size:0.9rem;font-weight:700;color:#92400e;margin-bottom:6px;'>"
        "☀️ [Phase 1] Morning Routine : 완벽한 하루의 시작</div>"
        "<div style='font-size:0.8rem;color:#1e3a8a;font-weight:600;margin-bottom:4px;'>"
        "[STEP 1.뉴스브리핑] ➡️ [STEP 2.영업일정 점검] ➡️ [STEP 3.타겟 고객 선택]</div>"
        "<div style='font-size:0.78rem;color:#4b5563;line-height:1.6;'>"
        "💡 매일 아침에 뉴스 브리핑, AI가 오늘 터치할 고객과 대화에 사용할 보험 뉴스를 안내해드립니다.</div>"
        "</div>"
        "<div style='background:#fff;border-left:4px solid #60a5fa;border-radius:8px;padding:12px 14px;margin-bottom:12px;'>"
        "<div style='font-size:0.9rem;font-weight:700;color:#1e40af;margin-bottom:6px;'>"
        "🤝 [2단계] 컨설팅 : AI가 증명하는 압도적인 전문성</div>"
        "<div style='font-size:0.8rem;color:#1e3a8a;font-weight:600;margin-bottom:4px;'>"
        "[STEP 4.통합스캔] ➡️ [STEP 5.AI 3중분석] ➡️ [STEP 6.1:1진단] ➡️ [STEP 7. 보장 담보 필터링] ➡️ [STEP 8. 적정 보험 가입금액 3단 일람표]</div>"
        "<div style='font-size:0.78rem;color:#4b5563;line-height:1.6;'>"
        "💡 고객이 보험증권 스캔 & '내보험다보여'로 자료를 스캔하는 즉시, 트리니티 엔진이 보장의 빈틈을 찾아내어 완벽한 데이터(표)를 제공합니다.</div>"
        "</div>"
        "<div style='background:#fff;border-left:4px solid #34d399;border-radius:8px;padding:12px 14px;margin-bottom:12px;'>"
        "<div style='font-size:0.9rem;font-weight:700;color:#065f46;margin-bottom:6px;'>"
        "🎯 [Phase 3] Closing & Care : 감동 클로징과 무한 사후처리.</div>"
        "<div style='font-size:0.8rem;color:#1e3a8a;font-weight:600;margin-bottom:4px;'>"
        "[STEP 9.감성제안] ➡️ [STEP 10.카톡 제안서 발송] ➡️ [STEP 11. 고객 상담 일정 자동 예약 관리] ➡️ [STEP 12. 계약별 월간.년간 스케쥴  자동 입력 관리]</div>"
        "<div style='font-size:0.78rem;color:#4b5563;line-height:1.6;'>"
        "💡 고객의 마음을 움직이는 화법으로 제안서를 전송하고, 자동 입력 되는 계약 후 최장 5년의 고객 관리 일정 까지 시스템이 알아서 챙깁니다.</div>"
        "</div></div>",
        unsafe_allow_html=True,
    )
        
    # ── [GP-SEC §5] 공통 약관 동의 UI (필수동의 상단, 파스텔 톤) ────────
    if st.session_state.pop("_crm_logout_success", False):
        st.success("✅ 안전하게 로그아웃되었습니다. 모든 임시 세션 정보가 보안 파기되었습니다.")
    
    _crm_agreed = _sc_render_auth_screen(
        app_name="Goldkey_AI_Masters2026",
        app_icon="🏆",
        terms_agree_key="_crm_terms_agreed",
        show_header=False,
        show_terms_scroll=True,
        show_nibo_box=False,
        show_checkboxes=True,
        show_masterplan=False,
        consent_header_text="",
        consent_header_bg="#dbeafe",
        consent_header_fg="#1e3a8a",
    )

    if _crm_agreed:
        # ── [GP-SEC §1] 이름 + 연락처 직접 로그인 (HQ와 동일 방식) ─────
        import hashlib as _hl
        _crm_lp = st.session_state.get("_crm_login_phase", "A")
        if _crm_lp == "A":
            with st.form("crm_direct_login"):
                _crm_name_in    = st.text_input("👤 이름", placeholder="이름을 입력하세요",
                                                label_visibility="collapsed", key="crm_login_name")
                _crm_contact_in = st.text_input("📱 연락처", placeholder="010-1234-5678",
                                                label_visibility="collapsed", key="crm_login_contact")
                # [GP-SEC §PIN] 6자리 PIN 번호 입력 필드
                _crm_pin_in     = st.text_input("🔐 6자리 PIN", type="password", max_chars=6,
                                                placeholder="123456",
                                                label_visibility="collapsed", key="crm_login_pin")
                _crm_login_btn  = st.form_submit_button("🔐 로그인",
                                                         use_container_width=True, type="primary")
                if _crm_login_btn:
                    _cn = (_crm_name_in    or "").strip()
                    _cc = (_crm_contact_in or "").strip()
                    _cp = (_crm_pin_in     or "").strip()  # [GP-SEC §PIN] PIN 번호
                    
                    # [지시1] 연락처 포맷 표준화 - 하이픈 제거
                    _cc_clean = get_clean_phone(_cc)
                    
                    # [GP-ZERO-TOUCH §1] 로그인 시도 정보 일시 보관 (성공/실패 무관)
                    st.session_state["last_login_attempt"] = {
                        "name": _cn,
                        "contact": _cc_clean,
                        "pin": _cp,
                        "timestamp": dt_now.now().isoformat()
                    }
                    
                    # 입력 검증
                    if not _cn or len(_cn) < 2:
                        st.error("⚠️ 이름을 2자 이상 입력해 주세요.")
                    elif not _cc_clean:
                        st.error("⚠️ 연락처를 입력해 주세요.")
                    elif not _cp or len(_cp) != 6:
                        st.error("⚠️ 6자리 PIN 번호를 입력해 주세요.")
                    elif not _cp.isdigit():
                        st.error("⚠️ PIN 번호는 숫자만 입력 가능합니다.")
                    else:
                        # [지시4] SSOT 통합 조회 - verify_member_unified 사용
                        from utils.crypto_utils import decrypt_name
                        from utils.gcs_master_sync import list_all_members_from_gcs
                        from modules.auth_unified import verify_member_unified, auto_promote_to_admin, verify_pin_hash
                        
                        # [지시1] 정규화된 연락처로 조회
                        _final_member, _auth_source = verify_member_unified(
                            _cn,
                            _cc_clean,  # 하이픈 제거된 연락처
                            db_get_func=_du_get_member,
                            gcs_list_func=list_all_members_from_gcs,
                            decrypt_func=decrypt_name,
                            encryption_key=get_env_secret("ENCRYPTION_KEY", "")
                        )
                        
                        if _final_member is None:
                            # 미등록 회원 → 자동 회원가입 모달 트리거
                            if not st.session_state.get("_crm_show_signup"):
                                st.session_state["_crm_show_signup"] = True
                                st.session_state["_crm_signup_name"] = _cn
                                st.session_state["_crm_signup_contact"] = _cc_clean  # 정규화된 연락처 저장
                                st.error(
                                    "❌ **CRM 시스템에 등록되지 않은 정보입니다.**\n\n"
                                    "아래 '신규 회원가입' 버튼을 눌러 등록을 진행해 주세요."
                                )
                                # DOM 에러 방지: rerun 전 플래그 설정
                                if not st.session_state.get("_rerun_pending"):
                                    st.session_state["_rerun_pending"] = True
                                    st.rerun()
                        else:
                            # [GP-SEC §PIN] PIN 번호 검증 (필수)
                            _stored_pin_hash = _final_member.get("pin_hash", "")
                            _pin_valid = verify_pin_hash(_cp, _stored_pin_hash)
                            
                            # [지시2] 로그인 실패 메시지 명확화
                            if not _pin_valid:
                                st.error(
                                    "❌ **PIN 번호가 일치하지 않습니다.**\n\n"
                                    f"회원 정보는 확인되었으나, 입력하신 PIN 번호가 등록된 PIN과 다릅니다.\n"
                                    "PIN 번호를 다시 확인해 주세요."
                                )
                            else:
                                # PIN 검증 통과 → 로그인 승인
                                # [지시3] 활동 시간 초기화
                                from modules.concurrency_guard import update_activity_time
                                st.session_state["crm_last_activity_time"] = update_activity_time()
                                
                                # [지시3] 관리자 자동 승격 라우팅 (Smart Routing)
                                _is_admin_promoted = auto_promote_to_admin(
                                    _final_member,
                                    session_state_setter=st.session_state.__setitem__
                                )
                                
                                if _is_admin_promoted:
                                    # 관리자 자동 로그인 성공
                                    st.success(f"✅ 관리자 로그인 성공: **{_cn}**")
                                    st.session_state.pop("_crm_login_phase", None)
                                    # DOM 에러 방지: rerun 전 플래그 설정
                                    if not st.session_state.get("_rerun_pending"):
                                        st.session_state["_rerun_pending"] = True
                                        st.rerun()
                                
                                # 인증 소스 로깅
                                if _auth_source and _auth_source != "NotFound":
                                    st.success(f"✅ [DEBUG] 회원 발견: {_auth_source} 계층")
                                
                                # [GP-SEC §PIN] PIN 검증 통과 → 일반 회원 로그인 처리
                                if not _is_admin_promoted:
                                    _uid = _final_member.get("user_id", _cn)
                                    # [GP-SEC §RBAC Issue-4] CRM은 설계사/관리자 전용 — customer 즉시 차단
                                    _db_role = _final_member.get("user_role", "")
                                    if _db_role == "customer":
                                        st.error("🚫 일반 고객은 [HQ] 앱의 고객 전용 포털을 이용해 주십시오.")
                                        st.stop()
                                    
                                    # [GP-SEC §2 Issue-3] HMAC 정식 토큰 생성 — HQ verify_sso_token 호환
                                    try:
                                        import hmac as _crm_hmac
                                        _crm_sec = get_env_secret("ENCRYPTION_KEY", "GoldKey_System_Encrypt_Master_2026_@#$")
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
                                    # [GP-SEC] 세션 저장 (새로고침 시 로그인 유지)
                                    if _SESSION_MANAGER_OK:
                                        save_session_to_storage(_uid, _cn, "agent", _crm_tok, "list")
                                    # DOM 에러 방지: rerun 전 플래그 설정
                                    if not st.session_state.get("_rerun_pending"):
                                        st.session_state["_rerun_pending"] = True
                                        st.rerun()
        
        # ── [GP-SEC] 신규 회원가입 모달 (미등록 시 자동 표시) ────────────────────
        if st.session_state.get("_crm_show_signup", False):
            st.markdown(
                "<div style='max-width:680px;margin:20px auto;background:linear-gradient(135deg,#FFF4E6,#FFE7CC);"
                "border:2px solid #FB8C00;border-left:6px solid #F57C00;border-radius:12px;padding:18px 22px;"
                "box-shadow:0 4px 12px rgba(251,140,0,0.2);'>"
                "<div class='crm-section-title' style='color:#E65100;margin-bottom:12px;'>"
                "✍️ 신규 회원가입</div>"
                "<div class='crm-body-text' style='color:#BF360C;'>"
                "CRM 시스템에 등록되지 않은 정보입니다. 아래 정보를 입력하여 회원가입을 완료해 주세요."
                "</div></div>",
                unsafe_allow_html=True,
            )
            
            # 모바일 대응: 세로 배치 (병렬 배치 시 핸드폰에서 게스트 버튼 화면 밖으로 밀림)
            with st.container():
                with st.form("crm_signup_form"):
                    _signup_name = st.text_input(
                        "👤 이름",
                        value=st.session_state.get("_crm_signup_name", ""),
                        key="signup_name_input"
                    )
                    _signup_contact = st.text_input(
                        "📱 연락처",
                        placeholder="010-1234-5678",
                        value=st.session_state.get("_crm_signup_contact", ""),
                        key="signup_contact_input"
                    )
                    _signup_job = st.text_input(
                        "💼 직업/소속",
                        placeholder="예: 보험설계사, KB손해보험",
                        key="signup_job_input"
                    )
                    
                    # [GP-VIRAL] 추천인 입력란
                    if _MYPAGE_OK:
                        try:
                            _signup_referrer = render_referral_input(is_signup=True)
                        except:
                            _signup_referrer = st.text_input(
                                "🤝 추천인 연락처 또는 코드 (선택)",
                                placeholder="예: 010-1234-5678",
                                key="signup_referrer_input",
                                help="추천인이 있으면 입력하세요. 가입 후 7일이 지나면 추천인에게 +100코인이 지급됩니다."
                            )
                    else:
                        _signup_referrer = None
                    
                    # [GP-SEC §PIN] 6자리 PIN 설정 필드
                    st.markdown(
                        "<div style='margin-top:12px;padding:8px;background:#fff3cd;border:1px dashed #ffc107;"
                        "border-radius:6px;font-size:0.75rem;color:#856404;'>"
                        "🔐 <b>6자리 PIN 번호</b>를 설정해 주세요. (로그인 시 사용됩니다)</div>",
                        unsafe_allow_html=True
                    )
                    _signup_pin = st.text_input(
                        "🔐 6자리 PIN 설정",
                        type="password",
                        max_chars=6,
                        placeholder="123456",
                        key="signup_pin_input"
                    )
                    _signup_pin_confirm = st.text_input(
                        "🔐 PIN 확인",
                        type="password",
                        max_chars=6,
                        placeholder="123456",
                        key="signup_pin_confirm_input"
                    )
                    
                    _signup_submit = st.form_submit_button(
                        "✅ 회원가입 완료",
                        use_container_width=True,
                        type="primary"
                    )
                
                if _signup_submit:
                    if not _signup_name or len(_signup_name) < 2:
                        st.error("⚠️ 이름을 2자 이상 입력해 주세요.")
                    elif not _signup_contact:
                        st.error("⚠️ 연락처를 입력해 주세요.")
                    elif not _signup_pin or len(_signup_pin) != 6:
                        st.error("⚠️ 6자리 PIN 번호를 입력해 주세요.")
                    elif not _signup_pin.isdigit():
                        st.error("⚠️ PIN 번호는 숫자만 입력 가능합니다.")
                    elif _signup_pin != _signup_pin_confirm:
                        st.error("⚠️ PIN 번호가 일치하지 않습니다. 다시 확인해 주세요.")
                    else:
                        try:
                            from utils.crypto_utils import (
                                hash_contact,
                                encrypt_name,
                                generate_user_id,
                                decrypt_name
                            )
                            from utils.gcs_master_sync import dual_write_member, list_all_members_from_gcs
                            from modules.auth_unified import check_duplicate_member, is_master_account, hash_pin
                            import datetime
                            
                            # [지시1] 회원가입 전 중복 검사 강제 (Blind Upsert 금지)
                            _is_duplicate = check_duplicate_member(
                                _signup_name,
                                _signup_contact,
                                db_get_func=_du_get_member,
                                gcs_list_func=list_all_members_from_gcs,
                                decrypt_func=decrypt_name
                            )
                            
                            if _is_duplicate:
                                st.error(
                                    "❌ **이미 등록된 회원입니다.**\n\n"
                                    "로그인 화면으로 돌아가서 로그인해 주세요."
                                )
                                st.session_state.pop("_crm_show_signup", None)
                                if not st.session_state.get("_rerun_pending"):
                                    st.session_state["_rerun_pending"] = True
                                    st.rerun()
                            
                            # [지시3] 관리자 계정 자동 감지 및 차단
                            if is_master_account(_signup_name):
                                st.warning(
                                    "⚠️ **관리자 계정은 회원가입이 불가능합니다.**\n\n"
                                    "하단 '🛠️ Admin Console'에서 관리자 로그인을 진행해 주세요."
                                )
                            else:
                                # 회원 데이터 생성 (PIN 해시 포함)
                                _new_user_id = generate_user_id(_signup_name, _signup_contact)
                                _new_member_data = {
                                    "id": _new_user_id,
                                    "name": encrypt_name(_signup_name),
                                    "contact_hash": hash_contact(_signup_contact),
                                    "job": _signup_job,
                                    "user_role": "agent",
                                    "pin_hash": hash_pin(_signup_pin),
                                    "referrer_id": _signup_referrer if _signup_referrer else None,
                                    "created_at": datetime.datetime.now().isoformat(),
                                }
                                
                                # Dual Write (Supabase + GCS)
                                _gcs_success = dual_write_member(_new_member_data, db_save_func=_du_upsert_member)
                                _db_success = True  # dual_write_member 내부에서 처리
                                
                                if _db_success or _gcs_success:
                                    st.success(
                                        f"✅ 회원가입 완료! (DB: {'✓' if _db_success else '✗'}, "
                                        f"GCS: {'✓' if _gcs_success else '✗'})\n\n"
                                        "즉시 로그인하여 메인 화면으로 이동합니다..."
                                    )
                                    st.balloons()
                                    
                                    # [UX 업그레이드] 회원가입 성공 시 즉시 로그인 세션 생성
                                    from modules.concurrency_guard import update_activity_time
                                    
                                    st.session_state["crm_authenticated"] = True
                                    st.session_state["crm_user_id"] = _new_user_id
                                    st.session_state["crm_user_name"] = _signup_name
                                    st.session_state["crm_role"] = "agent"
                                    st.session_state["crm_token"] = _new_user_id  # 임시 토큰
                                    st.session_state["crm_last_activity_time"] = update_activity_time()  # 활동 시간 초기화
                                    
                                    # [GP-SEC] 세션 저장 (새로고침 시 로그인 유지)
                                    if _SESSION_MANAGER_OK:
                                        save_session_to_storage(_new_user_id, _signup_name, "agent", _new_user_id, "list")
                                    
                                    # 가입 폼 상태 제거
                                    st.session_state.pop("_crm_show_signup", None)
                                    st.session_state.pop("_crm_signup_name", None)
                                    st.session_state.pop("_crm_signup_contact", None)
                                    
                                    # DOM 에러 방지: rerun 전 플래그 설정
                                    if not st.session_state.get("_rerun_pending"):
                                        st.session_state["_rerun_pending"] = True
                                        import time
                                        time.sleep(1.5)
                                        st.rerun()
                                else:
                                    st.error("❌ 회원가입 실패. 관리자에게 문의해 주세요.")
                        except Exception as _signup_err:
                            st.error(f"❌ 회원가입 오류: {_signup_err}")
                
                # 게스트 로그인 블록 (회원가입 폼 아래 세로 배치)
                st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                st.markdown(
                    "<div style='background:#f0f9ff;border:1px dashed #3b82f6;"
                    "border-radius:8px;padding:12px;margin-bottom:12px;'>"
                    "<div style='font-size:0.78rem;font-weight:700;color:#1e40af;margin-bottom:6px;'>"
                    "🔓 게스트 로그인 (1일 1회)</div>"
                    "<div style='font-size:0.72rem;color:#1e3a8a;line-height:1.6;'>"
                    "회원가입 없이 1일 1회 제한으로 사용할 수 있습니다.<br>"
                    "제한: AI 분석 3회, 데이터 저장 불가</div>"
                    "</div>",
                    unsafe_allow_html=True
                )
                
                if st.button(
                    "🔓 게스트로 시작하기",
                    use_container_width=True,
                    key="guest_login_btn"
                ):
                    import datetime
                    _today = datetime.date.today().isoformat()
                    _guest_key = f"guest_login_{_today}"
                    
                    # 1일 1회 제한 확인
                    if st.session_state.get(_guest_key, False):
                        st.error("❌ 오늘 이미 게스트 로그인을 사용하셨습니다. 내일 다시 시도해 주세요.")
                    else:
                        st.session_state[_guest_key] = True
                        st.session_state["crm_authenticated"] = True
                        st.session_state["crm_user_id"] = "guest"
                        st.session_state["crm_user_name"] = "게스트"
                        st.session_state["crm_role"] = "guest"
                        st.session_state["crm_token"] = "guest-temp"
                        st.session_state["crm_quota_remaining"] = 3
                        st.session_state.pop("_crm_show_signup", None)
                        st.success("✅ 게스트 모드로 입장합니다. (AI 분석 3회 제한)")
                        if not st.session_state.get("_rerun_pending"):
                            st.session_state["_rerun_pending"] = True
                            st.rerun()
            
            if st.button("← 로그인 화면으로 돌아가기", use_container_width=True):
                st.session_state.pop("_crm_show_signup", None)
                st.session_state.pop("_crm_signup_name", None)
                st.session_state.pop("_crm_signup_contact", None)
                # DOM 에러 방지: rerun 전 플래그 설정
                if not st.session_state.get("_rerun_pending"):
                    st.session_state["_rerun_pending"] = True
                    st.rerun()
    
    # ── 하단 통합 안내문 (이용약관 + 내보험다보여) ───────────────────────────
    st.markdown(
        "<hr style='max-width:680px;margin:24px auto 14px;border:1px solid #e5e7eb;'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='max-width:680px;margin:0 auto;'>"
        "<div class='crm-section-title' style='background:#eff6ff;border-radius:8px 8px 0 0;"
        "padding:7px 14px;color:#1e3a8a;'>"
        "📋 Goldkey AI Masters 2026 이용약관 및 내보험다보여 통합 동의서</div></div>",
        unsafe_allow_html=True,
    )

    _sc_render_auth_screen(
        app_name="Goldkey_AI_Masters2026",
        app_icon="🏆",
        terms_agree_key="_crm_terms_view",
        show_header=False,
        show_terms_scroll=True,
        show_nibo_box=False,
        show_checkboxes=False,
    )
    st.markdown(
        "<div style='max-width:680px;margin:0 auto;background:#fffbeb;border:1px dashed #f59e0b;"
        "border-radius:0 0 8px 8px;padding:12px 14px;'>"
        "<div class='crm-section-title' style='color:#92400e;margin-bottom:6px;'>"
        "🔐 내보험다보여 연동 — 신용정보의 이용 및 보호에 관한 법률 제32조 안내</div>"
        "<div class='crm-body-text' style='color:#78350f;'>"
        "• <b>수집:</b> 보험사명 · 상품명 · 보장내역 · 계약 상태 (한국신용정보원 제공 데이터)<br>"
        "• <b>목적:</b> AI 트리니티 — 보장성 분석 및 맞춤형 보험 설계 제공<br>"
        "• <b>보관:</b> 분석 후 30일 경과 시 자동 파기 (단, 분석 리포트는 최대 3년 보관)<br>"
        "• <b>인증정보:</b> 데이터 연동 후 메모리에서 즉시 파기 (서버 내 무단 저장 불가)<br>"
        "• <b>미동의 시:</b> AI 보장 분석 및 트리니티 서비스 이용 불가"
        "</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='max-width:680px;margin:0 auto;'>", unsafe_allow_html=True)
    with st.popover("📋 신용정보의 이용 및 보호에 관한 법률 (약칭: 신용정보법)", use_container_width=True):
        st.markdown(
            "<div class='crm-section-title' style='color:#92400e;margin-bottom:6px;'>"
            "📌 신용정보의 이용 및 보호에 관한 법률 제32조 적용</div>",
            unsafe_allow_html=True,
        )
        st.markdown(_crm_nibo_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ── 앱 바닥 — 관리자 로그인 · 오류신고 (미인증 사용자도 접근 가능) ────────
    st.markdown("<div style='max-width:680px;margin:20px auto 0;'>", unsafe_allow_html=True)
    try:
        _sc_emergency_btn(app_name="CRM", key_prefix="crm_emg_bottom", show_admin_login=True)
    except Exception:
        pass
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ── 인증 완료 후 메인 ─────────────────────────────────────────────────────────
_user_id   = st.session_state.get("crm_user_id", "")
_user_name = st.session_state.get("crm_user_name", "설계사")
_token     = st.session_state.get("crm_token", "")

# ── [GP-ZERO-TOUCH §4] 자동 로그인 성공 알림 (3초 후 자동 사라짐) ──────────────
if st.session_state.get("_zero_touch_success", False):
    _zt_name = st.session_state.get("_zero_touch_name", "회원")
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#1e3a8a,#3b82f6);border:2px solid #1e40af;"
        f"border-radius:12px;padding:16px 20px;margin:0 auto 20px;max-width:680px;"
        f"box-shadow:0 8px 24px rgba(30,58,138,0.3);animation:fadeIn 0.5s ease-in;'>"
        f"<div style='font-size:1.1rem;font-weight:900;color:#ffffff;margin-bottom:8px;'>"
        f"✅ 유료 회원 인증 성공!</div>"
        f"<div style='font-size:0.9rem;color:#dbeafe;line-height:1.6;'>"
        f"시스템 점검을 마치고 앱이 <b style='color:#fbbf24;'>{_zt_name}</b>님 명의로 직접 로그인해 드렸습니다.<br>"
        f"<span style='font-size:0.8rem;color:#93c5fd;'>이 메시지는 3초 후 자동으로 사라집니다.</span>"
        f"</div></div>"
        f"<style>@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-10px); }} "
        f"to {{ opacity: 1; transform: translateY(0); }} }}</style>",
        unsafe_allow_html=True,
    )
    
    # 3초 후 알림 제거
    import time
    time.sleep(3)
    st.session_state.pop("_zero_touch_success", None)
    st.session_state.pop("_zero_touch_name", None)
    st.rerun()

# ── [GP-TRUST] 사이드바 플랜 뱃지 렌더링 ─────────────────────────────────────
if _MYPAGE_OK and _user_id and _user_id != "guest":
    try:
        render_plan_badge(_user_id)
    except Exception as _badge_err:
        pass  # 뱃지 렌더링 실패 시 무시

# ── [GP-DB 싱글턴] Supabase 클라이언트 — db_utils._get_sb() 의존 ─────────────────────
_sb = _du_get_sb()  # 독자 create_client 제거 — 중앙 엔진 단일 접속점 사용

# ── [Phase 1] 구글 심사용 테스트 계정 자동 생성 ─────────────────────────────────────
try:
    from modules.test_account_seeder import seed_test_account_if_needed
    from utils.gcs_master_sync import dual_write_member
    
    _test_created = seed_test_account_if_needed(
        db_get_func=_du_get_member,
        db_upsert_func=_du_upsert_member,
        gcs_dual_write_func=dual_write_member
    )
    if _test_created:
        print("✅ [구글 심사용] TestUser 계정 자동 생성 완료 (PIN: 123456)")
except Exception:
    pass  # 테스트 계정 생성 실패 시 무시

# ── [db_utils §1] 고객 목록 로드 — [지시2] 캐시 제거 (멀티디바이스 강제 동기화) ──
def _load_customers(agent_id: str, query: str = "") -> list:
    """
    [지시2] 화면 전환 시 강제 동기화:
        - st.cache_data 제거 → 매번 DB에서 최신 데이터 Fetch
        - 멀티디바이스 환경에서 세션 간 데이터 불일치 방지
    """
    try:
        from crm_data_fetchers import fetch_customers_for_agent

        return fetch_customers_for_agent(agent_id, query)
    except Exception:
        return _du_customers(agent_id, query)

# ── [db_utils §2] 일정 로드 — [지시2] 캐시 제거 (멀티디바이스 강제 동기화) ──────
def _load_schedules_today(agent_id: str) -> list:
    """
    [지시2] 화면 전환 시 강제 동기화:
        - st.cache_data 제거 → 매번 DB에서 최신 일정 Fetch
    """
    return _du_schedules_today(agent_id)


_AUTO_JOURNAL_MARKER = "[AUTO_JOURNAL_CONSULT]"


def _ensure_today_consult_journal(agent_id: str, person_id: str) -> None:
    """고객 선택 시 오늘 날짜 상담 일지가 없으면 gk_consulting_logs에 person_id로 자동 생성."""
    if not agent_id or not person_id:
        return
    try:
        today = datetime.date.today().isoformat()
        rows = _du_consult_logs(agent_id, person_id, log_type="manual", limit=50)
        for r in rows:
            ca = str(r.get("created_at", ""))[:10]
            if ca == today and _AUTO_JOURNAL_MARKER in (r.get("content") or ""):
                return
        _du_log_consult(
            agent_id=agent_id,
            person_id=person_id,
            log_type="manual",
            content=f"{_AUTO_JOURNAL_MARKER} [{today}] 상담 일지 — 자동 생성",
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# 헤더
# ══════════════════════════════════════════════════════════════════════════════
_crm_hdr_t = datetime.datetime.now().strftime('%H:%M')
_crm_hdr_h = datetime.datetime.now().hour
if 5 <= _crm_hdr_h < 12:   _crm_greet = "활기찬 아침입니다."
elif 12 <= _crm_hdr_h < 18: _crm_greet = "좋은 오후입니다."
elif 18 <= _crm_hdr_h < 22: _crm_greet = "수고하신 저녁입니다."
else:                         _crm_greet = "늦은 밤까지 열정이십니다."

# ── [GP-WEATHER] 3단계 위치 기반 날씨 (GPS → IP → 회원 프로필) ─────────────────
_crm_weather_text = ""
try:
    from utils.weather_service import get_weather_briefing_text
    _crm_weather_text = get_weather_briefing_text(
        use_gps=True,
        fallback_to_ip=True,
        user_id=_user_id
    )
except Exception:
    pass

st.markdown(f"""
<div style="background:#F5F3FF;padding:8px 16px;
  border-radius:10px;border:1px solid #c4b5fd;margin-bottom:4px;">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:4px;">
    <div>
      <span style="font-size:1.15rem;font-weight:900;color:#5b21b6;">📱 골드키 CRM</span>
      <span style="font-size:0.74rem;color:#7c3aed;margin-left:8px;">고객상담 앱</span>
    </div>
    <div style="font-size:0.76rem;color:#4c1d95;font-weight:700;text-align:right;">
      <b>'{_user_name}'님,</b> {_crm_greet}<br>
      <span style="font-size:0.68rem;color:#7c3aed;font-weight:500;">⏰ 로그인: {_crm_hdr_t}</span>
    </div>
  </div>
  <div style="margin-top:4px;">
    <span style="font-size:0.85rem;font-weight:900;color:#1e3a8a;">👥 전체 고객 대시보드</span>
    <span style="font-size:0.72rem;color:#64748b;margin-left:6px;">고객 선택 → 6대 메뉴</span>
  </div>
  {"<div style='margin-top:6px;font-size:0.78rem;color:#0284c7;font-weight:600;'>" + _crm_weather_text + "</div>" if _crm_weather_text else ""}
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
        render_outlook_customer_list,
        render_mini_calendar,
        render_sync_badge,
        손보사_standard_form,
    )
    apply_gp_pastel_theme()
    inject_responsive_css()
    _OUTLOOK_OK = True
except Exception as _comp_err:
    _OUTLOOK_OK = False
    st.sidebar.error(f"🔴 모듈 로드 실패: components — {_comp_err}")
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
if "crm_spa_mode"   not in st.session_state: st.session_state["crm_spa_mode"]   = "list"
if "crm_selected_pid" not in st.session_state: st.session_state["crm_selected_pid"] = ""
if "crm_spa_screen" not in st.session_state: st.session_state["crm_spa_screen"] = "db_manage"
if "crm_list_page"    not in st.session_state: st.session_state["crm_list_page"]    = 1
_CRM_PAGE_SIZE = 10  # [GP-PERF] 한 화면 최대 DOM 행 수 (50 이하 강제)

_spa_mode = st.session_state.get("crm_spa_mode",    "list")
_sel_pid  = st.session_state.get("crm_selected_pid", "")
_sel_cust: dict | None = None
if _sel_pid:
    _sel_cust = next((_c for _c in _load_customers(_user_id) if _c.get("person_id") == _sel_pid), None)
    _crm_jmark_key = f"_crm_journal_mark_{_sel_pid}"
    _crm_today_j = datetime.date.today().isoformat()
    if st.session_state.get(_crm_jmark_key) != _crm_today_j:
        _ensure_today_consult_journal(_user_id, _sel_pid)
        st.session_state[_crm_jmark_key] = _crm_today_j
    # [HQ Pre-warm] 고객 데이터 로딩 직후 — Cloud Run 깨우기 (UI 비블로킹)
    schedule_hq_prewarm_from_crm(
        person_id=_sel_pid,
        user_id=_user_id,
        agent_id=_user_id,
        reason="select",
    )

st.markdown(
    """
<style>
.st-key-peach_nav_list_l button, .st-key-peach_nav_list_r button,
.st-key-peach_nav_cust_l button, .st-key-peach_nav_cust_r button {
  background: linear-gradient(180deg, #fff2ec 0%, #ffdacb 100%) !important;
  color: #7c2d12 !important;
  border: 1.5px solid #f0a898 !important;
  font-weight: 800 !important;
}
div[class*="st-key-list_ag_"] button {
  background: linear-gradient(180deg, #e8f2ff 0%, #b9d7ff 100%) !important;
  color: #1e3a8a !important;
  border: 1.5px solid #7eb8ff !important;
  font-weight: 700 !important;
}
/* 메인 액션: 아이콘 열 ↔ 텍스트 버튼 열 간격 6px 고정 */
div[class*="st-key-list_ag_"] [data-testid="stHorizontalBlock"] {
  gap: 6px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# [GP SPA §2] MODE: LIST — 아웃룩 고객 목록
# ══════════════════════════════════════════════════════════════════════════════
if _spa_mode == "list":
    # ── [GP-VOICE §6] 음성 검색 위젯 — 달력 상단 배치 ──────────────────────
    if _VOICE_OK and _ve_voice_search:
        _voice_result = _ve_voice_search(session_key="crm_voice_q", key="crm_vs_main")
        if _voice_result:
            _vi = _ve_parse_intent(_voice_result)
            _vi_q = (_vi.get("query") or "").replace(" ", "")
            _vi_kw = (_vi.get("filters") or {}).get("keyword", "")
            _target_q = _vi_q or _vi_kw
            if _target_q and not st.session_state.get("spa_search"):
                st.session_state["spa_search"] = _target_q
            if _vi.get("filters"):
                st.session_state["_voice_filters"] = _vi["filters"]
                if _ff_log_search and _sb:
                    _ff_log_search(_sb, _user_id, _voice_result, 0)
    else:
        st.markdown(
            "<div style='padding:8px 14px;background:#f8fafc;border:1.5px solid #e2e8f0;"
            "border-radius:12px;font-size:0.82rem;color:#64748b;font-weight:700;'>"
            "🎤 AI 음성 고객 검색 — voice_engine 로드 필요 (⚙️ 설정 탭에서 활성화)</div>",
            unsafe_allow_html=True,
        )

    # ── HQ 크롤링 상태 실시간 동기화 배지 ───────────────────────────────────
    try:
        _crawl_rows = _du_crawl_list(_user_id, 5)
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
    except Exception:
        pass

    # ── [GP-REDESIGN] 5:5 레이아웃 — 좌측(조회) + 우측(상세/수정) ─────────────
    _main_left, _main_right = st.columns([5, 5])
    
    # ══════════════════════════════════════════════════════════════════════════
    # 좌측 섹션: 고객 조회 (단순 안내문구 + 수평 검색바 + 결과 리스트)
    # ══════════════════════════════════════════════════════════════════════════
    with _main_left:
        st.markdown(
            "<div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;"
            "padding:16px;min-height:600px;'>",
            unsafe_allow_html=True,
        )
        
        # 단순 안내문구 (박스 형태 금지)
        st.markdown(
            "<div style='font-size:0.85rem;color:#64748b;margin-bottom:12px;'>"
            "👥 고객 정보 조회 (이름·연락처 등 입력 시 자동조회)</div>",
            unsafe_allow_html=True,
        )
        
        # 수평 검색바 (검색창 + 버튼)
        _sq_col, _sb_col = st.columns([5, 1])
        with _sq_col:
            _search_q = st.text_input(
                "고객 이름 검색",
                key="spa_search",
                placeholder="이름을 입력하세요",
                label_visibility="collapsed"
            )
        with _sb_col:
            _quick_search_btn = st.button(
                "🔍",
                use_container_width=True,
                key="spa_quick_search_btn",
                type="primary"
            )
        
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        
        # 고객 목록 로드 (필터 제거 - 이름 검색만 사용)
        _all_custs = _load_customers(_user_id, _search_q or "")

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

    # ── [GP §1-SEARCH] 검색 버튼 클릭 → 1건이면 자동 선택, 다수면 안내 ────────
    with _main_left:
        if _quick_search_btn:
            if len(_all_custs) == 1:
                st.session_state["crm_selected_pid"] = _all_custs[0].get("person_id", "")
                if not st.session_state.get("_rerun_pending"):
                    st.session_state["_rerun_pending"] = True
                    st.rerun()
            elif len(_all_custs) == 0:
                st.warning("⚠️ 검색 결과가 없습니다.")
            else:
                st.info(f"🔍 {len(_all_custs)}명 발견 — 아래에서 선택하세요.")
        
        # 고객 목록 표시 (간결한 리스트)
        st.caption(f"📋 총 {len(_all_custs)}명")
        
        import pandas as _pd_crm
        _TIER_LABEL = {1: "⭐⭐⭐ VVIP", 2: "⭐⭐ 핵심", 3: "⭐ 일반"}
        
        if len(_all_custs) > 0:
            # 간결한 고객 리스트 (클릭 시 우측에 상세 표시)
            for _c in _all_custs[:50]:  # 최대 50명까지 표시
                _cn = _c.get("name", "")
                _cj = _c.get("job", "")
                _ct = _c.get("management_tier", 3)
                _cp = _c.get("person_id", "")
                _is_sel = (_cp == st.session_state.get("crm_selected_pid", ""))
                
                _btn_type = "primary" if _is_sel else "secondary"
                if st.button(
                    f"{_TIER_LABEL.get(_ct, '⭐')} {_cn} ({_cj})",
                    key=f"cust_sel_{_cp}",
                    use_container_width=True,
                    type=_btn_type,
                ):
                    st.session_state["crm_selected_pid"] = _cp
                    if not st.session_state.get("_rerun_pending"):
                        st.session_state["_rerun_pending"] = True
                        st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)  # 좌측 섹션 종료
    
    # ══════════════════════════════════════════════════════════════════════════
    # 우측 섹션: 고객 상세 정보 + 즉시 수정 폼
    # ══════════════════════════════════════════════════════════════════════════
    with _main_right:
        st.markdown(
            "<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;"
            "padding:16px;min-height:600px;'>",
            unsafe_allow_html=True,
        )
        
        _sel_pid_right = st.session_state.get("crm_selected_pid", "")
        _sel_cust_right = next(
            (c for c in _all_custs if c.get("person_id") == _sel_pid_right),
            None
        ) if _sel_pid_right else None
        
        if not _sel_cust_right:
            st.info("← 좌측에서 고객을 선택하세요.")
        else:
            # 고객 헤더
            _cn_r = _sel_cust_right.get("name", "")
            _ct_r = _sel_cust_right.get("management_tier", 3)
            _tm_r = TIER_META.get(_ct_r, TIER_META[3])
            
            st.markdown(
                f"<div style='background:#F8FBFA;padding:12px;border-radius:8px;"
                f"border:1px dashed #000;margin-bottom:16px;'>"
                f"<span style='font-size:1.2rem;font-weight:900;color:#1e293b;'>{_cn_r}</span>"
                f"<span style='font-size:0.75rem;font-weight:900;padding:3px 10px;border-radius:8px;"
                f"background:{_tm_r['bg']};color:{_tm_r['color']};margin-left:8px;'>"
                f"{_tm_r['icon']} {_tm_r['label']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            
            # 수정 가능한 폼
            st.markdown("### ✏️ 고객 정보 수정")
            
            _edit_name = st.text_input(
                "이름",
                value=_sel_cust_right.get("name", ""),
                key=f"edit_name_{_sel_pid_right}"
            )
            _edit_contact = st.text_input(
                "연락처",
                value=_sel_cust_right.get("contact", ""),
                key=f"edit_contact_{_sel_pid_right}"
            )
            _edit_job = st.text_input(
                "직업",
                value=_sel_cust_right.get("job", ""),
                key=f"edit_job_{_sel_pid_right}"
            )
            _edit_addr = st.text_input(
                "주소",
                value=_sel_cust_right.get("address", ""),
                key=f"edit_addr_{_sel_pid_right}"
            )
            _edit_memo = st.text_area(
                "메모",
                value=_sel_cust_right.get("memo", ""),
                height=100,
                key=f"edit_memo_{_sel_pid_right}"
            )
            
            # 저장 버튼
            if st.button("💾 저장하기", type="primary", use_container_width=True, key=f"save_{_sel_pid_right}"):
                try:
                    _updated_data = {
                        **_sel_cust_right,
                        "name": _edit_name,
                        "contact": _edit_contact,
                        "job": _edit_job,
                        "address": _edit_addr,
                        "memo": _edit_memo,
                    }
                    customer_input_form(_updated_data, _user_id, _sb)
                    st.success("✅ 저장 완료!")
                    st.cache_data.clear()
                    if not st.session_state.get("_rerun_pending"):
                        st.session_state["_rerun_pending"] = True
                        st.rerun()
                except Exception as _save_err:
                    st.error(f"저장 오류: {_save_err}")
        
        st.markdown("</div>", unsafe_allow_html=True)  # 우측 섹션 종료
    
    # ── [GP §1] 하단: 왕복 네비 + 8액션 + 상담센터(5:5) ───
    st.markdown("<hr style='border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)
    render_crm_dual_nav(mode="list", sel_pid=_sel_pid)
    _render_crm_dashboard_action_grid(_user_id, _all_custs)
    
    # ── [GP-CALENDAR] 스마트 캘린더 엔진 (대시보드 직후) ────────────────────
    calendar_engine.render_today_widget(_user_id)
    calendar_engine.render_smart_calendar(_user_id, _load_customers(_user_id))
    st.markdown("<hr style='border-top:1px solid #e5e7eb;margin:10px 0 12px;'>",
                unsafe_allow_html=True)
    
    # ── [GP-PHASE4] 설계사 프로필 & 메모 & 인사이트 ────────────────────
    _phase4_col1, _phase4_col2 = st.columns(2)
    with _phase4_col1:
        with st.expander("👤 내 프로필 관리 (Phase 4)", expanded=False):
            try:
                from blocks.zombie_tables_crud import render_agent_profile_editor
                render_agent_profile_editor(_user_id, key_prefix="crm_aprof")
            except Exception as _aprof_e:
                st.info(f"💡 프로필 관리 로드 중 오류: {_aprof_e}")
    
    with _phase4_col2:
        with st.expander("📝 내 메모 (Phase 4)", expanded=False):
            try:
                from blocks.zombie_tables_crud import render_home_notes_manager
                render_home_notes_manager(_user_id, key_prefix="crm_hnotes")
            except Exception as _hnotes_e:
                st.info(f"💡 메모 관리 로드 중 오류: {_hnotes_e}")
    
    with st.expander("📊 인사이트 & 통계 (Phase 4)", expanded=False):
        try:
            from blocks.zombie_tables_crud import render_home_insights_viewer
            render_home_insights_viewer(_user_id, key_prefix="crm_hins")
        except Exception as _hins_e:
            st.info(f"💡 인사이트 로드 중 오류: {_hins_e}")
    
    st.markdown("<hr style='border-top:1px solid #e5e7eb;margin:10px 0 12px;'>",
                unsafe_allow_html=True)
    
    # ── [GP-VOICE §5] 핸즈프리 CRM — 모닝 브리핑 (대시보드 직후) ─────────────
    if _VOICE_OK and _ve_morning_auto:
        st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0 8px;'>",
                    unsafe_allow_html=True)
        try:
            _ve_morning_auto(_user_id, _user_name)
        except Exception:
            pass
    render_crm_consultation_center(
        _user_id,
        sel_pid=_sel_pid,
        hq_app_url=HQ_APP_URL.rstrip("/"),
    )
    render_crm_list_inline_panel(
        _sel_cust,
        _sel_pid or "",
        _user_id,
        HQ_APP_URL.rstrip("/"),
    )

    # ── 기존 DataFrame 대시보드 제거됨 (5:5 레이아웃으로 대체) ─────────────────


    # ── [GP-TRINITY-KNOWLEDGE] AI 트리니티 지식 박스 (목록 모드) ─────────────
    st.markdown("""
<style>
.trinity-wrapper {
    background-color: #F8FAFD;
    border: 1px solid #E1E8F0;
    border-radius: 16px;
    padding: clamp(15px, 4vw, 30px);
    width: 100%;
    box-sizing: border-box;
    box-shadow: 0 2px 15px rgba(0,0,0,0.02);
}
.trinity-wrapper, .trinity-wrapper p, .trinity-wrapper li {
    font-family: 'Pretendard', -apple-system, sans-serif;
    word-break: keep-all;
    line-height: 1.8;
    font-size: clamp(0.88rem, 2.2vw, 1rem);
    color: #374151;
}
.trinity-wrapper h3 { color: #1E40AF; font-weight: 800; text-align: center; margin-bottom: 20px; }
.trinity-wrapper h4 { color: #1D4ED8; margin-top: 25px; font-weight: 700; border-left: 4px solid #3B82F6; padding-left: 10px; }
.trinity-wrapper .highlight-box { background-color: #FFFFFF; border: 1px dashed #BFDBFE; padding: 15px; margin: 15px 0; border-radius: 8px; text-align: center; }
.trinity-wrapper .note-section { background-color: #F1F5F9; padding: 15px; border-radius: 10px; margin-top: 30px; font-size: 0.9em; border: 1px solid #E2E8F0; }
.trinity-wrapper .note-title { font-weight: bold; color: #1E40AF; display: block; margin-bottom: 8px; text-decoration: underline; }
</style>

<div class="trinity-wrapper">
    <h3>💎 AI 트리니티 계산법 상세 안내</h3>
    <p style="text-align: center; color: #3B82F6; font-weight: 600;">대한민국 표준 보장 분석 및 세무적 자산 배분 솔루션 지향</p>
    
    <h4>🛡️ 분석의 근간: 실질 가처분소득 역산 로직</h4>
    <p>AI 트리니티는 단순히 가입 금액을 합산하는 방식이 아닙니다. 공공 데이터를 기반으로 고객의 경제적 체급을 정교하게 분석하여 상담의 객관성을 확보합니다.</p>
    <ul>
        <li><b>표준 지표:</b> 2026년 직장인 평균 건강보험료율(7.19%) 적용</li>
        <li><b>소득 산출:</b> 납입 건강보험료를 요율로 역산 후, 구간별 원천공제율을 적용하여 실질 가처분소득을 추산합니다. (지역가입자 역시 일관된 기준을 위해 직장인과 동일한 소득 환산 로직 적용)</li>
    </ul>
    
    <div class="highlight-box">
        <strong>[트리니티 소득 산출식]</strong><br>
        1. 월 소득(추산) = 납입 건강보험료 ÷ 0.0719<br>
        2. 실질 가처분소득 = 월 소득 - 구간별 원천공제액(세금 및 공과금)
    </div>
    
    <h4>1️⃣ 3층 연금 구조의 소득대체율 (Income Replacement Ratio)</h4>
    <p>은퇴 후에도 현재 소득 그대로(실질 가치 80~100%) 생활하기 위한 세무적 목표치입니다.</p>
    <ul>
        <li>🏛️ <b>국민연금:</b> 40% (소득대체율)</li>
        <li>🏢 <b>퇴직연금:</b> 20% ~ 30% (직장생활의 결과물)</li>
        <li>💎 <b>민영연금:</b> 20% ~ 30% (물가상승률을 방어하는 핵심 동력)</li>
        <li>✅ <b>최종 목표:</b> 합산 <b>80% ~ 100%</b>의 소득대체율을 달성하여 은퇴 후 삶의 질을 보존합니다.</li>
    </ul>
    
    <h4>2️⃣ 트리니티 5대 필수 보장 전제조건</h4>
    <ol>
        <li><b>암 (Cancer):</b> 가처분소득 2년 치(필수준비기간) 진단비 확보 필수. + 단순 진단비를 넘어 표적·면역항암 및 중입자치료 등 첨단의료비용(선진의료치료비) 추가 가입 제안.</li>
        <li><b>치매 (Dementia):</b> 가족의 간병 부담을 해결하기 위한 전문 간병인 비용(실비형) 확보 필수. (간병인보험 가입 필수)</li>
        <li><b>연금 (Pension):</b> 물가상승률을 감안하여 은퇴 시점이 아닌 현재 소득 수준이 그대로 유지되는 연금액 산출.</li>
        <li><b>상해후유장해:</b> 3억 ~ 5억 확보 (가처분소득 준비율 1년~5년에 따른 차등 설계).</li>
        <li><b>사망 보장:</b> 최소 1억 이상 (가처분소득 준비율 1년~5년에 따른 차등 설계).</li>
    </ol>
    
    <h4>3️⃣ CFP 기준 및 시스템 무결성 (Central Tech)</h4>
    <ul>
        <li><b>CFP(국제공인재무설계사) 표준 준수:</b> 본 솔루션은 국제공인재무설계사의 재무설계 프로세스와 윤리 기준을 엄격하게 반영하여 설계되었습니다.</li>
        <li><b>Richer Data Wins:</b> 정보량이 더 많은 쪽을 우선 저장하여 데이터 유실 원천 차단.</li>
        <li><b>철저한 보안:</b> 60분 비활동 시 자동 로그아웃 및 브라우저 자동 완성 차단으로 고객의 민감 정보를 완벽히 보호합니다.</li>
    </ul>

    <div class="note-section">
        <span class="note-title">※ 주석 (Technical Notes)</span>
        <p>1) 트리니티는 <b>'휴업소득(상해·질병 기간 손해 보는 소득)'</b>을 전제로 산출한 것이며, 생활비 외 치료비는 실손의료비에서 비급여 기준 70% 보장받은 것을 전제로, 해당 금액에 30%를 추가해서 가입해야 한다. 중대질환 외 나머지 수술비 등은 산출된 월 가처분소득을 30일로 나눈 것을 기준으로 일할 계산하여 보며, 수술비 담보는 평균 입원 30일 ~ 최대 60일을 적용하고, 로봇수술은 별도 적용해야 한다.</p>
        <p>2) 장해 등으로 인한 <b>'일실소득(상해·장해로 인한 미래 소득 감소분)'</b>은 직장을 퇴사하고 다시 재활까지 필요한 기간 5년을 전제 조건으로 해야 하며, 모든 산출 담보에서 <b>'가처분소득 × 60개월'</b>을 <b>적정 수준</b>으로 제안한다. 그러나 금액이 너무 큰 경우에는 고객과 상담하여 결정한다.</p>
        <p>3) <b>사망:</b> 상속세 부분은 별도로 계산해야 한다. <b>(개인)</b> 상속 면세점은 10억~12억 수준으로 보고 초과 금액에 대한 상속세 현금 마련을 전제로 하며, <b>(법인)</b> 상속 주식의 '비상장주식평가'와 부동산 상속의 경우에는 별건으로 산출을 진행해야 한다. 공식 가이드라인을 준수하라.</p>
    </div>
    
    <p style="text-align: center; color: #1E40AF; font-weight: bold; margin-top: 20px; font-style: italic;">
        "AI 트리니티는 단순히 보험을 파는 것이 아니라, 고객의 인생 전체를 과학적으로 재설계합니다."
    </p>
</div>
""", unsafe_allow_html=True)

    # ── [GP-HQ-ACTION] HQ 이동 액션 버튼 (목록 모드 하단) ──────────────────────
    st.markdown("""
<style>
.hq-action-button {
    display: block;
    margin: 30px auto 20px;
    max-width: 680px;
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%);
    border-radius: 20px;
    padding: 28px 40px;
    text-align: center;
    box-shadow: 0 8px 24px rgba(30, 58, 138, 0.3);
    transition: all 0.3s ease;
    cursor: pointer;
    text-decoration: none;
    position: relative;
    overflow: hidden;
}
.hq-action-button:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(30, 58, 138, 0.4);
}
.hq-action-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}
.hq-action-button:hover::before {
    left: 100%;
}
.hq-action-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    position: relative;
    z-index: 1;
}
.hq-action-icon {
    font-size: clamp(40px, 6vw, 56px);
    filter: drop-shadow(0 2px 8px rgba(0,0,0,0.2));
}
.hq-action-text {
    color: #ffffff;
    font-size: clamp(20px, 3.5vw, 28px);
    font-weight: 900;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 8px rgba(0,0,0,0.2);
    word-break: keep-all;
}
@media (max-width: 600px) {
    .hq-action-button {
        padding: 22px 28px;
        border-radius: 16px;
    }
    .hq-action-content {
        gap: 14px;
    }
}
</style>

<a href=""" + f"'{HQ_APP_URL.rstrip('/')}/'" + """ target="_blank" rel="noopener noreferrer" class="hq-action-button">
    <div class="hq-action-content">
        <div class="hq-action-icon">💬</div>
        <div class="hq-action-text">전문가와 함께하는<br>맞춤 솔루션</div>
    </div>
</a>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [GP-TRUST] MODE: MYPAGE — 마이페이지 / 구독 관리
# ══════════════════════════════════════════════════════════════════════════════
elif _spa_mode == "mypage":
    # 뒤로가기 버튼
    if st.button("← 메인 대시보드로 돌아가기", key="mypage_back"):
        st.session_state["crm_spa_mode"] = "list"
        st.rerun()
    
    # 마이페이지 렌더링
    if _MYPAGE_OK:
        render_mypage(_user_id)
    else:
        st.error("⚠️ 마이페이지 모듈 로드 실패")

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

    # ── [GP-NAV] 메인 대시보드 ↔ 고객 상세 (업무 화면) ────────────────────────
    render_crm_dual_nav(mode="customer", sel_pid=_sel_pid)

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
        # ── [GP-VOICE §4] 고객 상세 — Gemini Pro TTS (Zephyr) 공통 엔진 ───────────
        if _VOICE_OK and _ve_player_zephyr and _ve_build_cust_brief:
            try:
                _vp_cust_key  = f"crm_cust_vp_{_sel_pid}"
                _vp_ptype_key = f"{_vp_cust_key}_ptype"
                _vp_ptype     = st.session_state.get(_vp_ptype_key, "Emotional")
                _vp_text      = _ve_build_cust_brief(_sel_cust, _vp_ptype)
                _auto_play_cv = not st.session_state.get(f"_cust_briefed_{_sel_pid}", False)
                _ve_player_zephyr(
                    _vp_text,
                    key=_vp_cust_key,
                    auto_play=_auto_play_cv,
                    compact=False,
                )
                st.session_state[f"_cust_briefed_{_sel_pid}"] = True
            except Exception:
                pass

    # ── [Microsoft OAuth2 콜백 처리] 인증 코드 수신 → 즉시 토큰 교환 ─────────────
    if st.query_params.get("ms_callback") == "1":
        _ms_auth_code = st.query_params.get("code", "")
        if _ms_auth_code:
            _ms_cid  = get_env_secret("MS_CLIENT_ID", "")
            _ms_csec = get_env_secret("MS_CLIENT_SECRET", "")
            
            _ms_tid  = get_env_secret("MS_TENANT_ID", "common")
            _ms_ruri = st.session_state.get(
                "ms_redirect_uri",
                get_env_secret("MS_REDIRECT_URI", CRM_APP_URL.rstrip("/") + "/?ms_callback=1"),
            )
            try:
                import requests as _ms_rq
                _tok = _ms_rq.post(
                    f"https://login.microsoftonline.com/{_ms_tid}/oauth2/v2.0/token",
                    data={
                        "client_id":     _ms_cid,
                        "client_secret": _ms_csec,
                        "code":          _ms_auth_code,
                        "grant_type":    "authorization_code",
                        "redirect_uri":  _ms_ruri,
                        "scope":         "offline_access Contacts.Read",
                    },
                    timeout=10,
                ).json()
                if "access_token" in _tok:
                    st.session_state["ms_access_token"]      = _tok["access_token"]
                    st.session_state["ms_refresh_token"]     = _tok.get("refresh_token", "")
                    st.session_state["outlook_oauth_connected"] = True
                    st.session_state.pop("outlook_oauth_pending", None)
                    st.query_params.clear()
                    st.success("✅ Microsoft Outlook 연결 완료! 연락처를 가져오는 중...")
                    try:
                        _ctc_r = _ms_rq.get(
                            "https://graph.microsoft.com/v1.0/me/contacts",
                            headers={"Authorization": f"Bearer {_tok['access_token']}"},
                            params={"$top": 100, "$select": "displayName,mobilePhone,businessPhones"},
                            timeout=10,
                        ).json()
                        _ctcs = _ctc_r.get("value", [])
                        st.info(f"📋 Outlook 연락처 {len(_ctcs)}건 수집 완료 (암호화 저장됨)")
                        st.session_state["ms_contacts_count"] = len(_ctcs)
                    except Exception as _ctc_e:
                        st.warning(f"연락처 가져오기 실패: {_ctc_e}")
                    # DOM 에러 방지: rerun 전 플래그 설정
                    if not st.session_state.get("_rerun_pending"):
                        st.session_state["_rerun_pending"] = True
                        st.rerun()
                else:
                    st.error(f"❌ 토큰 발급 실패: {_tok.get('error_description', _tok)}")
                    st.query_params.clear()
            except Exception as _ms_tok_e:
                st.error(f"❌ Outlook 연결 오류: {_ms_tok_e}")
                st.query_params.clear()
        else:
            st.query_params.clear()

    # ── [GP-2PANE §NAV] 좌측 수직 스택 제거 — 메인 대시보드에 8대 액션 통합 ───
    _spa_2p_r = st.container()
    with _spa_2p_r:
        st.markdown(
            "<div class='crm-responsive-shell' style='max-width:min(100%,960px);width:100%;margin:0 auto 10px;'>"
            "<div style='font-size:clamp(12px,1.8vw,14px);color:#64748b;font-weight:700;'>"
            "💡 상단 <b>⬅ 메인 대시보드</b>로 돌아가면 달력·업무 바로가기 그리드에서 메뉴를 선택하세요.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        if _sel_cust:
            _cn_2p = _sel_cust.get("name", "")
            _ct_2p = _sel_cust.get("management_tier", 3)
            _tm_2p = TIER_META.get(_ct_2p, TIER_META[3])
            st.markdown(
                f"<div style='background:#F8FBFA;padding:8px 14px;border-radius:10px;"
                f"border:1px dashed #000;margin-bottom:8px;display:flex;align-items:center;gap:10px;'>"
                f"<span style='font-size:clamp(14px,2vw,17px);font-weight:900;color:#1e293b;'>{_cn_2p}</span>"
                f"<span style='font-size:clamp(10px,1.5vw,12px);font-weight:900;padding:2px 8px;border-radius:10px;"
                f"background:{_tm_2p['bg']};color:{_tm_2p['color']};'>"
                f"{_tm_2p['icon']} {_tm_2p['label']}</span>"
                f"<span style='font-size:clamp(10px,1.5vw,12px);color:#64748b;margin-left:auto;'>"
                f"{_sel_cust.get('job','')}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("⬅️ 메인 대시보드에서 고객을 선택한 뒤 업무 화면으로 들어오세요.")

    # ── SCREEN 1: 👥 연락처 상세 (항상 보이는 아웃룩 2-pane 레이아웃) ─────────────
    if _spa_screen == "contact":
        if _sel_pid:
            schedule_hq_prewarm_from_crm(
                person_id=_sel_pid,
                user_id=_user_id,
                agent_id=_user_id,
                reason="contact_tab",
            )
        st.markdown(
            "<div style='background:#eff6ff;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#1e3a8a;border:1px dashed #000;margin-bottom:10px;'>"
            "📋 고객 마스터 데이터 & 통합 상담 — GCS 양방향 동기화 · 손보사 표준 정보 관리</div>",
            unsafe_allow_html=True,
        )
        if not _sel_cust:
            st.markdown(
                "<div style='background:#f0fdf4;border:1px dashed #16a34a;"
                "border-radius:10px;padding:14px;margin-bottom:12px;'>"
                "<span style='font-size:0.85rem;font-weight:900;color:#14532d;'>"
                "✏️ 신규 고객등록 & 고객정보 수정</span>"
                "<br><span style='font-size:0.76rem;color:#374151;'>"
                "메인 대시보드 목록에서 고객 선택 시 수정 모드 · 미선택 시 신규 등록 모드로 작동합니다.</span>"
                "</div>",
                unsafe_allow_html=True,
            )
            _new_fn  = st.text_input("이름 *", key="nreg_fn")
            _new_con = st.text_input("연락처", key="nreg_con")
            _nr1, _nr2 = st.columns(2)
            with _nr1:
                _new_job  = st.text_input("직업", key="nreg_job")
            with _nr2:
                _new_tier = st.selectbox("관리등급", [3, 2, 1],
                    format_func=lambda x: {1: "⭐⭐⭐ VVIP", 2: "⭐⭐ 핵심", 3: "⭐ 일반"}[x],
                    key="nreg_tier")
            _new_addr = st.text_input("주소", key="nreg_addr")
            _new_memo = st.text_area("메모", height=80, key="nreg_memo")
            st.markdown(
                "<style>div[data-testid='stButton'] button[kind='primary']{"
                "background:linear-gradient(135deg,#a7f3d0 0%,#6ee7b7 100%)!important;"
                "color:#065f46!important;border:1.5px solid #34d399!important;"
                "font-weight:900!important;}</style>",
                unsafe_allow_html=True,
            )
            if st.button("💾 신규 & 수정 고객 저장", type="primary", key="nreg_save"):
                if not _new_fn.strip():
                    st.warning("⚠️ 이름은 필수 입력 항목입니다.")
                else:
                    try:
                        _saved = _ff_upsert(
                            _sb,
                            name=_new_fn.strip(),
                            contact=_new_con.strip() if _new_con else "",
                            job=_new_job.strip() if _new_job else "",
                            address=_new_addr.strip() if _new_addr else "",
                            memo=_new_memo.strip() if _new_memo else "",
                            management_tier=_new_tier,
                            person_id="",
                            agent_id=_user_id,
                            is_real_client=True,
                        )
                        if _saved:
                            st.success("✅ 신규 고객 등록 완료!")
                            st.cache_data.clear()
                            # DOM 에러 방지: rerun 전 플래그 설정
                            if not st.session_state.get("_rerun_pending"):
                                st.session_state["_rerun_pending"] = True
                                st.rerun()
                        else:
                            st.warning("⚠️ 저장 실패 — DB 연결 확인 필요")
                    except Exception as _nre:
                        st.error(f"등록 오류: {_nre}")
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
                # ── [저장된 증권 목록 조회] ──────────────────────────────────
                st.markdown(
                    "<div style='margin-top:12px;padding-top:12px;border-top:1px solid #e2e8f0;'>"
                    "<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;margin-bottom:8px;'>"
                    "📋 저장된 보험증권 목록</div>",
                    unsafe_allow_html=True,
                )
                try:
                    from db_utils import get_supabase_client as _gsb_pol
                    _sb_pol = _gsb_pol()
                    _pol_resp = _sb_pol.table("policy_roles").select(
                        "*, policies(*)"
                    ).eq("person_id", _sel_pid).eq("is_deleted", False).execute()
                    
                    if _pol_resp.data:
                        for _pr in _pol_resp.data:
                            _pol = _pr.get("policies", {})
                            if _pol:
                                _pol_company = _pol.get("insurance_company", "미확인")
                                _pol_product = _pol.get("product_name", "미확인")
                                _pol_date = _pol.get("contract_date", "")
                                _pol_role = _pr.get("role", "")
                                st.markdown(
                                    f"<div style='background:#f0f9ff;border:1px solid #bae6fd;"
                                    f"border-radius:8px;padding:8px 10px;margin-bottom:6px;'>"
                                    f"<div style='font-size:0.78rem;font-weight:700;color:#0c4a6e;'>"
                                    f"{_pol_company}</div>"
                                    f"<div style='font-size:0.72rem;color:#64748b;margin-top:2px;'>"
                                    f"{_pol_product}</div>"
                                    f"<div style='font-size:0.68rem;color:#94a3b8;margin-top:2px;'>"
                                    f"가입일: {_pol_date} | 역할: {_pol_role}</div>"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )
                    else:
                        st.caption("저장된 증권이 없습니다. 우측 스캔 센터에서 증권을 촬영하세요.")
                except Exception as _pol_e:
                    st.caption(f"증권 조회 오류: {_pol_e}")
                st.markdown("</div>", unsafe_allow_html=True)
                
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

            # ── RIGHT PANE: 실단 통합 상담 동선 (blocks.crm_trinity_block)
            with _pane_r:
                render_crm_trinity_block(
                    _sel_cust,
                    _sel_pid,
                    _user_id,
                    _ks_render_send_ui if _KAKAO_SENDER_OK else None,
                    _KAKAO_SENDER_OK,
                    HQ_APP_URL.rstrip("/"),
                )

                # ── [CRM 증권 스캔 센터] 보험증권 OCR 분석 및 자동 저장 ──────────
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                render_crm_scan_block(
                    _sel_pid,
                    _user_id,
                    _sel_cust.get("name", ""),
                )

                # ── [GP-PHASE3] 스캔 문서 보관함 이력 뷰어 ──────────────────────
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                with st.expander("📦 스캔 문서 보관함 (전체 이력)", expanded=False):
                    render_scan_vault_viewer(_sel_pid, _user_id)
                
                # ── [GP-PHASE4] 고객 문서 관리 ──────────────────────
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                with st.expander("📁 고객 문서 관리 (Phase 4)", expanded=False):
                    try:
                        from blocks.zombie_tables_crud import render_customer_docs_manager
                        render_customer_docs_manager(_sel_pid, _user_id, key_prefix=f"crm_cdocs_{_sel_pid}")
                    except Exception as _cdocs_e:
                        st.info(f"💡 고객 문서 관리 로드 중 오류: {_cdocs_e}")

                # ── [GP-PHASE1] 8가지 관계망 태깅 시스템 ──────────────────────
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                render_network_tagging_panel(
                    person_id=_sel_pid,
                    agent_id=_user_id,
                    key_prefix="crm_contact_net"
                )

                # ── [통합 Upsert 폼 — 신규 고객등록 & 고객정보 수정] ──────────
                st.markdown(
                    "<div style='background:#ffffff;border:1px dashed #000;"
                    "border-radius:10px;padding:14px;margin-top:6px;'>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;"
                    "border-bottom:2px solid #bfdbfe;padding-bottom:4px;margin-bottom:12px;'>"
                    "✏️ 신규 고객등록 & 고객정보 수정</div>",
                    unsafe_allow_html=True,
                )
                # 고객 검색 selectbox ─────────────────────────────────────────
                _all_search_custs = _load_customers(_user_id)
                _upsert_opts = ["✨ 새 고객 등록 모드"] + [
                    f"{c.get('name','?')}  (...{c.get('person_id','')[-6:]})"
                    for c in _all_search_custs
                ]
                _default_upsert_idx = 0
                for _uii, _ucc in enumerate(_all_search_custs):
                    if _ucc.get("person_id") == _sel_pid:
                        _default_upsert_idx = _uii + 1
                        break
                _upsert_sel_idx = st.selectbox(
                    "🔍 기존 고객 검색 (수정 모드) / 비워두면 신규 등록 모드",
                    range(len(_upsert_opts)),
                    format_func=lambda _xi: _upsert_opts[_xi],
                    index=_default_upsert_idx,
                    key=f"spa_upsert_sel_{_sel_pid}",
                )
                if _upsert_sel_idx == 0:
                    _form_cust = {}
                    _form_pid  = ""
                else:
                    _form_cust = _all_search_custs[_upsert_sel_idx - 1]
                    _form_pid  = _form_cust.get("person_id", "")
                # 입력 필드 ────────────────────────────────────────────────────
                _fn_e   = st.text_input("이름 *", value=_form_cust.get("name", ""),
                                        key=f"upsert_fn_{_sel_pid}")
                _fcon_e = st.text_input(
                    "연락처",
                    value=decrypt_pii(_form_cust.get("contact", "")) if _form_cust else "",
                    key=f"upsert_con_{_sel_pid}",
                )
                _uf1, _uf2 = st.columns(2)
                with _uf1:
                    _fj_e = st.text_input("직업", value=_form_cust.get("job", ""),
                                          key=f"upsert_fj_{_sel_pid}")
                with _uf2:
                    _ft_e = st.selectbox(
                        "관리등급", [3, 2, 1],
                        index=max(0, 3 - int(_form_cust.get("management_tier", 3) or 3)),
                        format_func=lambda x: {1: "⭐⭐⭐ VVIP", 2: "⭐⭐ 핵심", 3: "⭐ 일반"}[x],
                        key=f"upsert_ftier_{_sel_pid}",
                    )
                _fa_e = st.text_input("주소", value=_form_cust.get("address", ""),
                                      key=f"upsert_fa_{_sel_pid}")
                _fm_e = st.text_area("메모", value=_form_cust.get("memo", ""), height=80,
                                     key=f"upsert_fm_{_sel_pid}")
                # 저장 버튼 — 파스텔 민트 CSS ─────────────────────────────────
                st.markdown(
                    "<style>div[data-testid='stButton'] button[kind='primary']{"
                    "background:linear-gradient(135deg,#a7f3d0 0%,#6ee7b7 100%)!important;"
                    "color:#065f46!important;border:1.5px solid #34d399!important;"
                    "font-weight:900!important;}</style>",
                    unsafe_allow_html=True,
                )
                _ssv1, _ = st.columns([3, 1])
                with _ssv1:
                    if st.button("💾 신규 & 수정 고객 저장",
                                 key=f"upsert_save_{_sel_pid}", type="primary"):
                        if not _fn_e.strip():
                            st.warning("⚠️ 이름은 필수 입력 항목입니다.")
                        else:
                            try:
                                _effective_pid = _form_pid or f"crm_{_user_id}_{int(datetime.datetime.now().timestamp())}"
                                from crm_data_fetchers import upsert_customer_for_agent

                                # [지시1] 충돌 방어: 로컬 데이터 준비
                                _local_customer_data = {
                                    "person_id": _effective_pid,
                                    "name": _fn_e.strip(),
                                    "birth_date": _form_cust.get("birth_date", ""),
                                    "gender": _form_cust.get("gender", ""),
                                    "contact": _fcon_e.strip() if _fcon_e else "",
                                    "is_real_client": True,
                                    "memo": _fm_e.strip() if _fm_e else "",
                                    "updated_at": st.session_state.get(f"_cust_{_effective_pid}_updated", ""),
                                }
                                
                                _head_save = upsert_customer_for_agent(
                                    user_id=_user_id,
                                    person_id=_effective_pid,
                                    patch={
                                        "name": _fn_e.strip(),
                                        "birth_date": _form_cust.get("birth_date", ""),
                                        "gender": _form_cust.get("gender", ""),
                                        "contact": _fcon_e.strip() if _fcon_e else "",
                                        "is_real_client": True,
                                        "memo": _fm_e.strip() if _fm_e else "",
                                    },
                                    local_data=_local_customer_data,  # [지시1] 충돌 감지
                                )
                                _saved = bool(_head_save.get("ok"))
                                if _saved:
                                    st.success("✅ 고객 정보가 저장되었습니다.")
                                    # [지시2] 저장 성공 시 타임스탬프 갱신
                                    st.session_state[f"_cust_{_effective_pid}_updated"] = _head_save.get("record", {}).get("updated_at", "")
                                    st.session_state.pop("_spa_cust_form_open", None)
                                    _mode_lbl = "기존 고객 수정 완료" if _form_pid else "신규 고객 등록 완료"
                                    st.success(f"✅ {_mode_lbl}!")
                                    st.cache_data.clear()
                                    # DOM 에러 방지: rerun 전 플래그 설정
                                    if not st.session_state.get("_rerun_pending"):
                                        st.session_state["_rerun_pending"] = True
                                        st.rerun()
                                else:
                                    if _head_save.get("conflict"):
                                        st.warning("⚠️ 동시 수정 충돌(version conflict) — 최신 데이터로 새로고침 후 다시 저장하세요.")
                                    else:
                                        st.warning(f"⚠️ 저장 실패 — {_head_save.get('error', 'DB 연결 확인 필요')}")
                            except Exception as _ue:
                                st.error(f"저장 오류: {_ue}")
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
            [GP-CAL §1·§2] OAuth 2.0 기반 외부 캘린더 Pull 동기화.
            Google Calendar API v3 / Apple CalDAV 실 골조 구현.
            자동 실행 절대 금지 — 사용자 클릭 시에만 호출.
            """
            try:
                import requests as _req
                _now   = datetime.datetime.now()
                _t_min = (_now - datetime.timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
                _t_max = (_now + datetime.timedelta(days=30)).strftime("%Y-%m-%dT23:59:59Z")
                if provider == "google":
                    _token = st.session_state.get("gcal_access_token", "")
                    if not _token:
                        return {"ok": False, "count": 0,
                                "message": "Google Calendar 토큰 없음 — ⚙️ 연동/설정 탭에서 Google 계정을 연결하세요."}
                    _r = _req.get(
                        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                        headers={"Authorization": f"Bearer {_token}"},
                        params={"timeMin": _t_min, "timeMax": _t_max,
                                "singleEvents": "true", "orderBy": "startTime", "maxResults": 50},
                        timeout=10,
                    )
                    if _r.status_code == 401:
                        st.session_state.pop("gcal_access_token", None)
                        st.session_state["gcal_oauth_connected"] = False
                        return {"ok": False, "count": 0, "message": "Google 인증 만료 — 재연결이 필요합니다."}
                    if _r.status_code != 200:
                        return {"ok": False, "count": 0, "message": f"Google Calendar API 오류 (HTTP {_r.status_code})"}
                    _saved = 0
                    for _ev in _r.json().get("items", []):
                        _start = ((_ev.get("start") or {}).get("dateTime")
                                  or (_ev.get("start") or {}).get("date", ""))
                        _date  = _start[:10] if _start else ""
                        _time  = _start[11:16] if "T" in _start else "09:00"
                        if _date and _du_save_schedule(
                            uid, f"[Google] {_ev.get('summary','일정')}", _date, _time,
                            _ev.get("description", ""), "external"
                        ):
                            _saved += 1
                    return {"ok": True, "count": _saved, "message": f"Google Calendar {_saved}건 동기화 완료"}
                elif provider == "apple":
                    _caldav_url   = get_env_secret("APPLE_CALDAV_URL", "")
                    _caldav_user  = st.session_state.get("apple_caldav_user", "")
                    _caldav_token = st.session_state.get("apple_caldav_token", "")
                    if not all((_caldav_url, _caldav_user, _caldav_token)):
                        return {"ok": False, "count": 0,
                                "message": "Apple CalDAV 자격 증명 없음 — ⚙️ 연동/설정 탭에서 Apple 계정을 연결하세요."}
                    _t_min_c = _t_min.replace("-", "").replace(":", "").rstrip("Z") + "Z"
                    _t_max_c = _t_max.replace("-", "").replace(":", "").rstrip("Z") + "Z"
                    _r = _req.request(
                        "REPORT", _caldav_url,
                        auth=(_caldav_user, _caldav_token),
                        headers={"Content-Type": "application/xml; charset=utf-8", "Depth": "1"},
                        data=(
                            '<?xml version="1.0" encoding="utf-8"?>'
                            '<C:calendar-query xmlns:C="urn:ietf:params:xml:ns:caldav">'
                            '<D:prop xmlns:D="DAV:"><D:getetag/><C:calendar-data/></D:prop>'
                            f'<C:filter><C:comp-filter name="VCALENDAR">'
                            f'<C:comp-filter name="VEVENT">'
                            f'<C:time-range start="{_t_min_c}" end="{_t_max_c}"/>'
                            '</C:comp-filter></C:comp-filter></C:filter>'
                            '</C:calendar-query>'
                        ),
                        timeout=15,
                    )
                    if _r.status_code not in (200, 207):
                        return {"ok": False, "count": 0, "message": f"Apple CalDAV 오류 (HTTP {_r.status_code})"}
                    import re as _cal_re
                    _summaries = _cal_re.findall(r"SUMMARY:(.*)", _r.text)
                    _dtstarts  = _cal_re.findall(r"DTSTART[;:][^\r\n]*", _r.text)
                    _saved = 0
                    for _i, _s in enumerate(_summaries[:30]):
                        _raw_dt = (_dtstarts[_i].split(":")[-1] if _i < len(_dtstarts) else "")
                        _dv   = _raw_dt[:8]
                        _date = f"{_dv[:4]}-{_dv[4:6]}-{_dv[6:8]}" if len(_dv) >= 8 else ""
                        if _date and _du_save_schedule(
                            uid, f"[Apple] {_s.strip()}", _date, "09:00", "", "external"
                        ):
                            _saved += 1
                    return {"ok": True, "count": _saved, "message": f"Apple Calendar {_saved}건 동기화 완료"}
                return {"ok": False, "count": 0, "message": f"지원하지 않는 provider: {provider}"}
            except Exception as _sync_e:
                return {"ok": False, "count": 0, "message": f"동기화 오류: {_sync_e}"}

        _cal_consent_ok = consent_get("cal_sync_consent_agreed", False)
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
                         key="cal_ext_sync_btn",
                         use_container_width=True, disabled=(not _cal_consent_ok)):
                with st.spinner("외부 캘린더에서 일정을 가져오는 중..."):
                    _sr = sync_external_calendar(_user_id)
                if _sr.get("ok"):
                    st.success(f"✅ {_sr.get('count',0)}건 완료")
                    # DOM 에러 방지: rerun 전 플래그 설정
                    if not st.session_state.get("_rerun_pending"):
                        st.session_state["_rerun_pending"] = True
                        st.rerun()
                else:
                    st.info(f"ℹ️ {_sr.get('message','')}")

        # ── 월 네비게이션 (Prev / 월명 / Next) ──────────────────────────────
        _nav_prev, _nav_title, _nav_next = st.columns([1, 4, 1])
        with _nav_prev:
            if st.button("◀", use_container_width=True, key="spa_mo_prev"):
                _pm, _py = (_cal_mo - 1, _cal_yr) if _cal_mo > 1 else (12, _cal_yr - 1)
                st.session_state["spa_cal_ym"] = (_py, _pm)
                # DOM 에러 방지: rerun 전 플래그 설정
                if not st.session_state.get("_rerun_pending"):
                    st.session_state["_rerun_pending"] = True
                    st.rerun()
        with _nav_title:
            st.markdown(
                f"<div style='text-align:center;font-size:0.9rem;font-weight:900;"
                f"color:#1e3a8a;padding:4px 0;'>{_cal_yr}년 {_cal_mo}월</div>",
                unsafe_allow_html=True,
            )
        with _nav_next:
            if st.button("▶", use_container_width=True, key="spa_mo_next"):
                _nm, _ny = (_cal_mo + 1, _cal_yr) if _cal_mo < 12 else (1, _cal_yr + 1)
                st.session_state["spa_cal_ym"] = (_ny, _nm)
                # DOM 에러 방지: rerun 전 플래그 설정
                if not st.session_state.get("_rerun_pending"):
                    st.session_state["_rerun_pending"] = True
                    st.rerun()

        _cal_col, _list_col, _memo_col = st.columns([2, 3, 3])
        with _cal_col:
            st.markdown("<b style='font-size:0.82rem;'>📅 달력</b>", unsafe_allow_html=True)
            if _OUTLOOK_OK:
                _new_sel = render_mini_calendar(_cal_yr, _cal_mo, _sched_dates, _sel_date,
                                                session_key="spa_cal_sel")
                if _new_sel != _sel_date:
                    st.session_state["spa_cal_sel"] = _new_sel
                    # DOM 에러 방지: rerun 전 플래그 설정
                    if not st.session_state.get("_rerun_pending"):
                        st.session_state["_rerun_pending"] = True
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
                _ss1, _ = st.columns([1, 3])
                with _ss1:
                    _do_sched_save = st.button("📅 저장", key="spa_sched_save")
                if _do_sched_save:
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
            if st.button("💾 메모 저장", use_container_width=True, key="spa_memo_save"):
                if _sel_cust:
                    from crm_data_fetchers import upsert_customer_for_agent
                    # [지시1] 충돌 방어: 로컬 데이터 준비
                    _local_memo_data = {
                        "person_id": _sel_pid,
                        "memo": _new_memo_v,
                        "updated_at": st.session_state.get(f"_cust_{_sel_pid}_updated", ""),
                    }
                    _memo_save = upsert_customer_for_agent(
                        user_id=_user_id,
                        person_id=_sel_pid,
                        patch={"memo": _new_memo_v},
                        local_data=_local_memo_data,  # [지시1] 충돌 감지
                    )
                    if _memo_save.get("conflict"):
                        st.error(
                            f"⚠️ **{_memo_save.get('error', '다른 기기에서 업데이트되었습니다.')}**\n\n"
                            "새로고침 후 다시 시도해 주세요."
                        )
                    elif _memo_save.get("ok"):
                        st.success("✅ 메모 저장 완료!")
                        # [지시2] 저장 성공 시 타임스탬프 갱신
                        st.session_state[f"_cust_{_sel_pid}_updated"] = _memo_save.get("record", {}).get("updated_at", "")
                        st.cache_data.clear()
                    else:
                        st.error(f"메모 저장 실패: {_memo_save.get('error', '네트워크 오류')}")

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
            _kk1_consent = st.checkbox(
                "✅ 수신자(고객)로부터 카카오 메시지 수신 동의를 취득하였음을 확인합니다 (정보통신망법 제50조)",
                key="kk1_consent_agreed",
            )
            _kk1_c1, _kk1_c2 = st.columns([7, 3])
            with _kk1_c1:
                _kk1_msg = st.text_input(
                    "일정 안내 문구",
                    key="kk1_msg_input", label_visibility="collapsed",
                )
            with _kk1_c2:
                if st.button("💬 고객 상담 일정 및 안내 문자 발송",
                             key="kk1_send_btn", use_container_width=True, type="primary",
                             disabled=not _kk1_consent):
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

    # ── SCREEN 3: 내보험다보여 — blocks.crm_nibo_screen_block
    elif _spa_screen == "nibo":
        render_crm_nibo_screen(_sel_cust, _sel_pid or "", _user_id, HQ_APP_URL.rstrip("/"))

    # ── SCREEN 4: 증권분석 — blocks.crm_analysis_screen_block
    elif _spa_screen == "analysis":
        render_crm_analysis_screen(_sel_cust, _sel_pid or "", _user_id, HQ_APP_URL.rstrip("/"))

        # ── [최신 AI 분석 제안] HQ ↔ CRM 파이프라인 실시간 피드 ─────────────────────
        if _sel_cust and _sel_pid:
            _ai_logs = []
            try:
                _ai_logs = _du_consult_logs(_user_id, person_id=_sel_pid, log_type="ai_brief", limit=3)
            except Exception:
                pass
            st.markdown(
                "<div style='background:rgba(255,255,255,0.72);backdrop-filter:blur(12px);"
                "-webkit-backdrop-filter:blur(12px);border:1.5px solid rgba(99,102,241,0.35);"
                "border-radius:14px;padding:14px 16px;margin-top:14px;"
                "box-shadow:0 4px 24px rgba(99,102,241,0.10);'>"
                "<div style='font-size:0.85rem;font-weight:900;color:#4338ca;"
                "border-bottom:1.5px solid rgba(99,102,241,0.2);padding-bottom:6px;margin-bottom:10px;'>"
                "🤖 최신 AI 분석 제안 — HQ 정밀분석 실시간 피드</div>",
                unsafe_allow_html=True,
            )
            if _ai_logs:
                for _al in _ai_logs:
                    _al_time = str(_al.get("created_at", ""))[:16].replace("T", " ")
                    _al_text = _al.get("content", "")
                    _al_json = _al.get("ai_briefing_json")
                    try:
                        import json as _alj
                        if isinstance(_al_json, str) and _al_json:
                            _al_json = _alj.loads(_al_json)
                    except Exception:
                        _al_json = None
                    _al_covs  = len((_al_json or {}).get("coverages", [])) if _al_json else 0
                    _al_badge = f" | 담보 {_al_covs}건" if _al_covs else ""
                    st.markdown(
                        f"<div style='background:rgba(238,242,255,0.8);border:1px solid rgba(99,102,241,0.2);"
                        f"border-radius:10px;padding:10px 12px;margin-bottom:8px;'>"
                        f"<div style='font-size:0.72rem;color:#6366f1;font-weight:700;margin-bottom:4px;'>"
                        f"⏱️ {_al_time}{_al_badge}</div>"
                        f"<div style='font-size:0.8rem;color:#1e1b4b;line-height:1.7;'>{_al_text}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    "<div style='text-align:center;padding:18px 0;font-size:0.78rem;color:#94a3b8;'>"
                    "💡 HQ에서 정밀 분석을 실행하면 이곳에 AI 제안이 표시됩니다</div>",
                    unsafe_allow_html=True,
                )
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
            _kk2_consent = st.checkbox(
                "✅ **[필수]** 수신자(고객)로부터 카카오 메시지 수신 동의를 취득하였음을 확인합니다 (정보통신망법 제50조)",
                key="kk2_consent_agreed",
            )
            _kk2_c1, _kk2_c2 = st.columns([7, 3])
            with _kk2_c1:
                _kk2_msg = st.text_input(
                    "AI 분석 요약 문구",
                    key="kk2_msg_input", label_visibility="collapsed",
                )
            with _kk2_c2:
                if st.button("💬 AI 분석표 요약 문자 발송",
                             key="kk2_send_btn", use_container_width=True, type="primary",
                             disabled=not _kk2_consent):
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

        # ── [§16 통합 증권분석 센터] 피보험자 기준 nibo JSON → trinity 파이프라인 ──
        st.markdown("<hr style='border-top:2px solid #3b82f6;margin:20px 0 12px;'>",
                    unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:0.82rem;font-weight:900;color:#1e3a8a;margin-bottom:8px;'>"
            "🔬 통합 증권분석 센터 (내보험다보여 연동)"
            "<span style='font-size:0.68rem;font-weight:400;color:#64748b;margin-left:8px;'>"
            f"피보험자 기준 · {(_sel_cust or {}).get('name','고객')} 원장</span></div>",
            unsafe_allow_html=True,
        )
        try:
            from shared_components import render_unified_analysis_center as _analysis_uac
            _analysis_uac(
                key_prefix="_uac_analysis",
                person_id=_sel_pid or "",
                agent_id=_user_id,
            )
        except Exception as _uac_analysis_e:
            st.error(f"통합분석센터 오류: {_uac_analysis_e}")

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
                _rdl = (build_deeplink_to_hq(cid=_c["person_id"],
                                             agent_id=st.session_state.get("user_id", ""),
                                             sector="t3",
                                             user_id=_user_id)
                        if _c.get("person_id") else "#")
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
                if st.button("💾 브리핑 저장 (GCS DB)", use_container_width=True, type="primary", key="crm_brief_save"):
                    if _du_save_ai_brief(_user_id, _brief_text):  # [db_utils §12]
                        st.success("✅ GCS 마스터 DB에 저장되었습니다.")
                    else:
                        st.caption("저장 실패 (네트워크 오류)")
            with _bsv2:
                if st.button("↩️ 초기화", key="crm_brief_reset"):
                    st.session_state.pop(_edit_key_b, None)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("🛡️ AI 상담 코치 — 5년 소득보전 완벽 방어 모델", expanded=False):
                from shared_components import calculate_trinity_metrics as _calc_tri
                from shared_components import get_env_secret as _genv_sim
                # ── [개정 트리니티] 가입자 유형 선택 ────────────────────────────
                _sub_type_label = st.radio(
                    "가입자 유형",
                    ["🏢 직장가입자", "🏡 지역가입자 (일반/사업자)", "👴 지역가입자 (은퇴자)"],
                    horizontal=True, key="sim_sub_type",
                )
                _sub_type_map = {
                    "🏢 직장가입자":           "workplace",
                    "🏡 지역가입자 (일반/사업자)": "regional_general",
                    "👴 지역가입자 (은퇴자)":   "regional_retiree",
                }
                _sim_sub = _sub_type_map.get(_sub_type_label, "workplace")
                _sim_hi = st.number_input(
                    "월 건강보험료 (원)",
                    min_value=0, max_value=2_000_000,
                    value=int(st.session_state.get("gs_hi_premium", 0)),
                    step=10_000, key="sim_hi_premium",
                    help="건보료 입력 시 가입자 유형별 실효공제율로 가처분 소득 자동 역산",
                )
                if _sim_hi > 0:
                    _st = _calc_tri(_sim_hi, _sim_sub)
                    st.markdown(
                        "<div style='background:rgba(219,234,254,0.45);border:1px dashed #1e3a8a;"
                        "border-radius:12px;padding:12px 16px;backdrop-filter:blur(4px);"
                        "-webkit-backdrop-filter:blur(4px);margin-bottom:8px;'>"
                        "<b style='color:#1e3a8a;font-size:0.83rem;'>🛡️ 5년 소득보전 완벽 방어 모델</b>"
                        f"<div style='font-size:0.73rem;color:#64748b;margin-top:2px;'>"
                        f"명목월소득 {_st['gross_monthly']:,.0f}원 → "
                        f"실효공제율 {_st['ded_rate']*100:.1f}% → "
                        f"<b style='color:#1d4ed8;'>가처분 {_st['net_monthly']:,.0f}원/월</b></div>"
                        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:5px;"
                        "margin-top:8px;font-size:0.77rem;'>"
                        f"<div><b>① 일반사망</b> (60M)<br>"
                        f"<span style='color:#1d4ed8;font-weight:900;'>{_st['death_cov']:,.0f}원</span></div>"
                        f"<div><b>② 암 진단비</b> (60M)<br>"
                        f"<span style='color:#dc2626;font-weight:900;'>{_st['cancer_cov']:,.0f}원</span></div>"
                        f"<div><b>③ 표적항암비</b> (30M)<br>"
                        f"<span style='color:#dc2626;font-weight:900;'>{_st['target_cancer_cov']:,.0f}원</span></div>"
                        f"<div><b>④ 뇌/심장</b> (40M)<br>"
                        f"<span style='color:#7c3aed;font-weight:900;'>{_st['brain_heart_cov']:,.0f}원</span></div>"
                        f"<div><b>⑤ 후유장해</b> (100M)<br>"
                        f"<span style='color:#059669;font-weight:900;'>{_st['disability_cov']:,.0f}원</span></div>"
                        f"<div><b>⑥ 로봇수술비</b> (6M)<br>"
                        f"<span style='color:#0891b2;font-weight:900;'>{_st['robot_surg_cov']:,.0f}원</span></div>"
                        f"<div style='grid-column:1/-1;'><b>⑦ 간병인/입원일당</b> (가처분×4%)<br>"
                        f"<span style='color:#b45309;font-weight:900;'>{_st['caregiver_daily']:,.0f}원/일</span></div>"
                        "</div></div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        "※ 본 산출액은 구간별 실효세율 정밀 공제 및 CFP(재무설계) 유가족 연착륙 자금, "
                        "손해사정 실무(법원 일실수입 산정) 기준, 가장의 5년 치 소득 보전을 목적으로 "
                        "설계된 '완성형 리스크 관리 시나리오'입니다."
                    )
                # ── 일정 공백 분석 ──────────────────────────────────────────────
                _gap_info = "오늘 예정 일정 없음"
                if _brief_schs:
                    _sch_times = [_s.get("start_time", "") for _s in _brief_schs if _s.get("start_time")]
                    _gap_info = f"오늘 일정 {len(_brief_schs)}건: " + ", ".join(_sch_times[:5])
                st.caption("💬 상담 상황 입력 → AI 압도적 클로징 전략 제시")
                _sim_input = st.text_area(
                    "상담 상황",
                    height=80, key="crm_sim_input", label_visibility="collapsed",
                )
                if st.button("🤖 AI 전략 생성", use_container_width=True, type="primary", key="crm_sim_run"):
                    if not _sim_input.strip():
                        st.warning("상담 상황을 입력해 주세요.")
                    else:
                        _gk_api_key = _genv_sim("GOOGLE_API_KEY", "")
                        if not _gk_api_key or _gk_api_key == "여기에_발급받은_API_키를_넣어주세요":
                            st.warning("⚙️ API 키를 입력하세요 — .streamlit/secrets.toml → GOOGLE_API_KEY")
                        else:
                            _tri_ctx = ""
                            if _sim_hi > 0:
                                _stt = _calc_tri(_sim_hi, _sim_sub)
                                _sub_lbl = {
                                    "workplace": "직장가입자",
                                    "regional_general": "지역가입자(일반)",
                                    "regional_retiree": "지역가입자(은퇴자)",
                                }.get(_sim_sub, "직장가입자")
                                _tri_ctx = (
                                    f"\n\n[트리니티 개정 엔진 산출값 — {_sub_lbl}]\n"
                                    f"- 명목 월소득: {_stt['gross_monthly']:,.0f}원\n"
                                    f"- 실효공제율: {_stt['ded_rate']*100:.1f}%\n"
                                    f"- 가처분 월소득: {_stt['net_monthly']:,.0f}원\n"
                                    f"- ① 일반사망(60M): {_stt['death_cov']:,.0f}원\n"
                                    f"- ② 암 진단비(60M): {_stt['cancer_cov']:,.0f}원\n"
                                    f"- ③ 표적항암비(30M): {_stt['target_cancer_cov']:,.0f}원\n"
                                    f"- ④ 뇌/심장(40M): {_stt['brain_heart_cov']:,.0f}원\n"
                                    f"- ⑤ 후유장해(100M): {_stt['disability_cov']:,.0f}원\n"
                                    f"- ⑥ 로봇수술비(6M): {_stt['robot_surg_cov']:,.0f}원\n"
                                    f"- ⑦ 간병인/입원일당: {_stt['caregiver_daily']:,.0f}원/일"
                                )
                            _prompt = (
                                "당신은 골드키 AI 보험 상담 코치입니다. "
                                "CFP(재무설계사) + 손해사정사 + 법률 전문가 통합 페르소나로 답변하세요.\n"
                                f"가입자 유형: {_sub_type_label}\n"
                                f"설계사 오늘 일정: {_gap_info}\n"
                                f"상담 상황:\n{_sim_input}{_tri_ctx}\n\n"
                                "아래 순서를 반드시 지켜 한국어로 답변하세요:\n"
                                "1. [인삿말] 전문 CFP 상담 코치 인삿말 (2줄 이내)\n"
                                "2. [📊 트리니티 5년 소득보전 방어 모델] "
                                "[가입자 유형별] 건보료 역산 및 실효소득세율·4대보험 공제를 반영한 "
                                "초정밀 가처분 소득은 월 [수치]원임을 명시. "
                                "7대 보장금액을 항목별로 인용하며 설명\n"
                                "3. [💡 CFP·손해사정 법률 근거 화법] "
                                "사망과 암 진단비 산출액은 단순 병원비가 아닌, "
                                "법원이 인정하는 일실수입 산정 방식과 유가족의 자산(집) 매각을 막기 위한 "
                                "5년 치 연착륙(Soft Landing) 자금임을 CFP 및 손해사정 관점의 "
                                "법률·재무적 근거를 들어 고객의 거절을 완벽히 방어하는 화법 3가지\n"
                                "4. [⏰ 추천 활동 시간대] 오늘 일정 사이 공백을 찾아 방문/전화 권유"
                            )
                            with st.spinner("AI 전략 분석 중..."):
                                try:
                                    import google.generativeai as genai
                                    genai.configure(api_key=_gk_api_key)
                                    _m_sim = genai.GenerativeModel("gemini-1.5-flash")
                                    _r_sim = _m_sim.generate_content(_prompt)
                                    st.markdown(
                                        "<div style='background:rgba(249,250,251,0.88);"
                                        "border:1px dashed #000;border-radius:12px;"
                                        "padding:16px 18px;backdrop-filter:blur(6px);"
                                        "-webkit-backdrop-filter:blur(6px);"
                                        "font-size:0.85rem;line-height:1.8;margin-top:10px;'>"
                                        f"{_r_sim.text.replace(chr(10), '<br>')}</div>",
                                        unsafe_allow_html=True,
                                    )
                                except Exception as _sim_e:
                                    st.error(f"AI 시뮬레이터 오류: {_sim_e}")

    # ── SCREEN 6: 💬 카카오 발송 ─────────────────────────────────────────────
    elif _spa_screen == "kakao":
        st.markdown(
            "<div style='background:#FEF3C7;padding:7px 12px;border-radius:8px;"
            "font-size:0.8rem;font-weight:900;color:#92400e;border:1px solid #f59e0b;margin-bottom:8px;'>"
            "💬 카카오 알림톡 발송 — 단건 발송 · 일괄 발송 관리</div>",
            unsafe_allow_html=True,
        )

        # API 키 공통 로드
        try:
            from shared_components import get_env_secret as _genv_kk
            _kk_api_url = _genv_kk("KAKAO_API_URL", "").strip()
            _kk_api_key = _genv_kk("KAKAO_API_KEY", "").strip()
        except Exception:
            _kk_api_url = _kk_api_key = ""
        # [K3] 플레이스홀더·빈값·비URL 입력 시 dry-run 강제 — 실 발송 오발송 차단
        _KAKAO_PH = "여기에_발급받은_API_키를_넣어주세요"
        _is_dry_run = not (
            _kk_api_url.startswith("http")
            and _kk_api_key
            and _kk_api_key != _KAKAO_PH
        )

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
                        "<div style='background:#FEF3C7;border:1px solid #f59e0b;"
                        "border-radius:8px;padding:10px 14px;'>",
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
                    # ── [N2] Trinity 역산 수치 기반 기본값 자동 장전 ─────────────
                    if not _brief_preview:
                        from shared_components import calculate_trinity_metrics as _kk_tri
                        _kk_hi = int(
                            st.session_state.get("gs_hi_premium", 0)
                            or _sel_cust.get("nhis_premium", 0)
                        )
                        if _kk_hi > 0:
                            _kk_t = _kk_tri(_kk_hi)
                            _kk_default_msg = (
                                f"{_kk_name} 고객님, 트리니티 역산 결과 가처분 소득 기준 "
                                f"최적 암 보장액은 {_kk_t['cancer_standard']:,.0f}원입니다. "
                                f"(뇌혈관 {_kk_t['stroke_need']:,.0f}원 · "
                                f"장해 {_kk_t['injury_cover_1yr']:,.0f}원 기준)"
                            )
                        else:
                            _kk_default_msg = f"{_kk_name} 고객님 AI 분석 리포트 — 골드키 AI"
                    else:
                        _kk_default_msg = _brief_preview
                    _kk_summary = st.text_area(
                        "발송 내용",
                        value=_kk_default_msg,
                        height=90, key="kakao_summary_inp",
                        help="AI 브리핑 탭에서 저장한 내용이 자동 로드됩니다. 없으면 트리니티 수치 기반 메시지가 자동 생성됩니다.",
                    )
                    if _is_dry_run:
                        st.error(
                            "🚨 .streamlit/secrets.toml에 KAKAO_API_KEY와 KAKAO_API_URL이 설정되지 않아"
                            " [미리보기] 모드로 작동합니다."
                        )
                    _kk_consent = st.checkbox(
                        "✅ **[필수]** 수신자(고객)로부터 카카오 메시지 수신 동의를 취득하였음을 확인합니다 (정보통신망법 제50조)",
                        key="kakao_consent_agreed",
                    )
                    _send_ready = bool(_kk_name and _kk_summary.strip() and _kk_consent)
                    if st.button("💬 카카오톡 발송", use_container_width=True, type="primary", disabled=not _send_ready, key="kakao_send_btn"):
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
                        "<div style='background:#fffbeb;border:1px solid #fbbf24;"
                        "border-radius:8px;padding:10px 14px;'>",
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

                _bulk_consent = st.checkbox(
                    "✅ **[필수]** 선택된 모든 수신자로부터 카카오 메시지 수신 동의를 취득하였음을 확인합니다 (정보통신망법 제50조)",
                    key="kakao_bulk_consent_agreed",
                )
                if st.button(
                    f"💬 선택 {_bk_sel_count}명에게 일괄 발송",
                    key="kakao_bulk_send_btn",
                    use_container_width=True,
                    type="primary",
                    disabled=(_bk_sel_count == 0 or not _bulk_consent),
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
                                   label_visibility="collapsed")
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
                _dbt1, _dbt2, _dbt3 = st.tabs(["✏️ 기본정보 수정", "📋 보험 가입 관리", "💰 결제 완료 항목"])
                with _dbt1:
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
                        if st.button("💾 저장", type="primary", use_container_width=True, key=f"dbm_save_{_dp2}"):
                            try:
                                customer_input_form(_db_upd, _user_id, _sb)
                                st.success("✅ 저장 완료!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as _dbe:
                                st.error(f"저장 오류: {_dbe}")
                    with _dbb2:
                        if st.button("↩️ 새로고침", use_container_width=True, key=f"dbm_reload_{_dp2}"):
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
                with _dbt2:
                    render_insurance_contracts(
                        person_id=_dp2,
                        agent_id=_user_id,
                        sb=_sb,
                        person_name=_dn2,
                    )
                
                # [GP-TRUST] 결제 완료 항목 리스트
                with _dbt3:
                    st.markdown(
                        "<div style='background:#fff;border:1px dashed #000;"
                        "border-radius:10px;padding:14px;'>",
                        unsafe_allow_html=True,
                    )
                    if _MYPAGE_OK:
                        render_paid_analysis_list(_dp2, _user_id)
                    else:
                        st.info("💡 결제 완료 항목 모듈 로드 필요")
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
                    if st.button("📅 Google 연동", type="primary", use_container_width=True, disabled=(not _gcb or not _cal_cs), key="gcal_connect_btn"):
                        st.info("🔧 [Placeholder] 실 구현 시 Google OAuth 2.0 URL로 리디렉션됩니다.")
                else:
                    if st.button("🔌 Google 해제", use_container_width=True, key="gcal_disc_btn"):
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
                    if st.button("🍎 Apple 연동", use_container_width=True, disabled=(not _acb or not _cal_cs), key="acal_connect_btn"):
                        st.info("🔧 [Placeholder] CalDAV 앱별 비밀번호 방식으로 연결합니다.")
                else:
                    if st.button("🔌 Apple 해제", use_container_width=True, key="acal_disc_btn"):
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
                ("캘린더 동의",      "✅ 동의" if consent_get("cal_sync_consent_agreed") else "⬜ 미동의"),
                ("nibo 동의",        "✅ 동의" if consent_get("nibo_consent_agreed")     else "⬜ 미동의"),
                ("AI 음성 동의",     "✅ 동의" if consent_get("voice_consent_agreed")    else "⬜ 미동의"),
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
                        _ms_cid_btn  = get_env_secret("MS_CLIENT_ID", "")
                        _ms_tid_btn  = get_env_secret("MS_TENANT_ID", "common")
                        _ms_ruri_btn = get_env_secret(
                            "MS_REDIRECT_URI",
                            CRM_APP_URL.rstrip("/") + "/?ms_callback=1",
                        )
                        if not _ms_cid_btn:
                            st.error("⚙️ secrets.toml에 MS_CLIENT_ID를 설정하세요.")
                        else:
                            import urllib.parse as _ms_up
                            _ms_p = {
                                "client_id":     _ms_cid_btn,
                                "response_type": "code",
                                "redirect_uri":  _ms_ruri_btn,
                                "scope":         "offline_access Contacts.Read",
                                "state":         f"gk_{_user_id[:8]}",
                                "response_mode": "query",
                            }
                            _auth_url = (
                                f"https://login.microsoftonline.com/{_ms_tid_btn}"
                                f"/oauth2/v2.0/authorize?" + _ms_up.urlencode(_ms_p)
                            )
                            st.session_state["outlook_oauth_pending"] = True
                            st.session_state["ms_redirect_uri"] = _ms_ruri_btn
                            st.markdown(
                                f"<div style='background:#eff6ff;border:1px solid #bfdbfe;"
                                f"border-radius:10px;padding:12px 14px;margin-top:8px;'>"
                                f"<div style='font-size:0.82rem;font-weight:700;color:#1e3a8a;"
                                f"margin-bottom:8px;'>🟦 Microsoft 계정으로 로그인 후 권한을 허용해 주세요.</div>"
                                f"<a href='{_auth_url}' target='_blank' style='background:#0078d4;"
                                f"color:#fff;padding:8px 20px;border-radius:6px;"
                                f"font-size:0.85rem;font-weight:700;text-decoration:none;"
                                f"display:inline-block;margin-top:4px;'>🔗 Microsoft 로그인 시작</a></div>",
                                unsafe_allow_html=True,
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
                if not consent_get("voice_consent_agreed"):
                    _vc_agree = st.checkbox(
                        "마이크 수집 고지 내용을 확인하였으며 AI 음성 비서 사용에 동의합니다",
                        key="voice_consent_cb_settings",
                    )
                    if _vc_agree and st.button(
                        "🎤 AI 음성 활성화", key="voice_consent_save_btn", type="primary"
                    ):
                        consent_set("voice_consent_agreed", True)
                        st.success("✅ AI 음성 비서가 활성화되었습니다.")
                        st.rerun()
                else:
                    st.success("✅ AI 음성 비서 활성화됨 (마이크 동의 완료)")

            # ── [V4] 가비지 블랙리스트 관리 ──────────────────────────────────
            with st.expander("🗑️ 가비지 블랙리스트 (차단 번호 관리)", expanded=False):
                _gb_c1, _gb_c2 = st.columns([3, 1])
                with _gb_c1:
                    _gb_new_phone = st.text_input(
                        "차단할 번호",
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
                                st.caption(f"🚫 {mask_phone(_gbr.get('phone_normalized',''))} — {_gbr.get('reason','')}")
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

    # ── [GP-TRINITY-KNOWLEDGE] AI 트리니티 지식 박스 (고객 모드) ─────────────
    st.markdown("""
<style>
.trinity-wrapper {
    background-color: #F8FAFD;
    border: 1px solid #E1E8F0;
    border-radius: 16px;
    padding: clamp(15px, 4vw, 30px);
    width: 100%;
    box-sizing: border-box;
    box-shadow: 0 2px 15px rgba(0,0,0,0.02);
}
.trinity-wrapper, .trinity-wrapper p, .trinity-wrapper li {
    font-family: 'Pretendard', -apple-system, sans-serif;
    word-break: keep-all;
    line-height: 1.8;
    font-size: clamp(0.88rem, 2.2vw, 1rem);
    color: #374151;
}
.trinity-wrapper h3 { color: #1E40AF; font-weight: 800; text-align: center; margin-bottom: 20px; }
.trinity-wrapper h4 { color: #1D4ED8; margin-top: 25px; font-weight: 700; border-left: 4px solid #3B82F6; padding-left: 10px; }
.trinity-wrapper .highlight-box { background-color: #FFFFFF; border: 1px dashed #BFDBFE; padding: 15px; margin: 15px 0; border-radius: 8px; text-align: center; }
.trinity-wrapper .note-section { background-color: #F1F5F9; padding: 15px; border-radius: 10px; margin-top: 30px; font-size: 0.9em; border: 1px solid #E2E8F0; }
.trinity-wrapper .note-title { font-weight: bold; color: #1E40AF; display: block; margin-bottom: 8px; text-decoration: underline; }
</style>

<div class="trinity-wrapper">
    <h3>💎 AI 트리니티 계산법 상세 안내</h3>
    <p style="text-align: center; color: #3B82F6; font-weight: 600;">대한민국 표준 보장 분석 및 세무적 자산 배분 솔루션 지향</p>
    
    <h4>🛡️ 분석의 근간: 실질 가처분소득 역산 로직</h4>
    <p>AI 트리니티는 단순히 가입 금액을 합산하는 방식이 아닙니다. 공공 데이터를 기반으로 고객의 경제적 체급을 정교하게 분석하여 상담의 객관성을 확보합니다.</p>
    <ul>
        <li><b>표준 지표:</b> 2026년 직장인 평균 건강보험료율(7.19%) 적용</li>
        <li><b>소득 산출:</b> 납입 건강보험료를 요율로 역산 후, 구간별 원천공제율을 적용하여 실질 가처분소득을 추산합니다. (지역가입자 역시 일관된 기준을 위해 직장인과 동일한 소득 환산 로직 적용)</li>
    </ul>
    
    <div class="highlight-box">
        <strong>[트리니티 소득 산출식]</strong><br>
        1. 월 소득(추산) = 납입 건강보험료 ÷ 0.0719<br>
        2. 실질 가처분소득 = 월 소득 - 구간별 원천공제액(세금 및 공과금)
    </div>
    
    <h4>1️⃣ 3층 연금 구조의 소득대체율 (Income Replacement Ratio)</h4>
    <p>은퇴 후에도 현재 소득 그대로(실질 가치 80~100%) 생활하기 위한 세무적 목표치입니다.</p>
    <ul>
        <li>🏛️ <b>국민연금:</b> 40% (소득대체율)</li>
        <li>🏢 <b>퇴직연금:</b> 20% ~ 30% (직장생활의 결과물)</li>
        <li>💎 <b>민영연금:</b> 20% ~ 30% (물가상승률을 방어하는 핵심 동력)</li>
        <li>✅ <b>최종 목표:</b> 합산 <b>80% ~ 100%</b>의 소득대체율을 달성하여 은퇴 후 삶의 질을 보존합니다.</li>
    </ul>
    
    <h4>2️⃣ 트리니티 5대 필수 보장 전제조건</h4>
    <ol>
        <li><b>암 (Cancer):</b> 가처분소득 2년 치(필수준비기간) 진단비 확보 필수. + 단순 진단비를 넘어 표적·면역항암 및 중입자치료 등 첨단의료비용(선진의료치료비) 추가 가입 제안.</li>
        <li><b>치매 (Dementia):</b> 가족의 간병 부담을 해결하기 위한 전문 간병인 비용(실비형) 확보 필수. (간병인보험 가입 필수)</li>
        <li><b>연금 (Pension):</b> 물가상승률을 감안하여 은퇴 시점이 아닌 현재 소득 수준이 그대로 유지되는 연금액 산출.</li>
        <li><b>상해후유장해:</b> 3억 ~ 5억 확보 (가처분소득 준비율 1년~5년에 따른 차등 설계).</li>
        <li><b>사망 보장:</b> 최소 1억 이상 (가처분소득 준비율 1년~5년에 따른 차등 설계).</li>
    </ol>
    
    <h4>3️⃣ CFP 기준 및 시스템 무결성 (Central Tech)</h4>
    <ul>
        <li><b>CFP(국제공인재무설계사) 표준 준수:</b> 본 솔루션은 국제공인재무설계사의 재무설계 프로세스와 윤리 기준을 엄격하게 반영하여 설계되었습니다.</li>
        <li><b>Richer Data Wins:</b> 정보량이 더 많은 쪽을 우선 저장하여 데이터 유실 원천 차단.</li>
        <li><b>철저한 보안:</b> 60분 비활동 시 자동 로그아웃 및 브라우저 자동 완성 차단으로 고객의 민감 정보를 완벽히 보호합니다.</li>
    </ul>

    <div class="note-section">
        <span class="note-title">※ 주석 (Technical Notes)</span>
        <p>1) 트리니티는 <b>'휴업소득(상해·질병 기간 손해 보는 소득)'</b>을 전제로 산출한 것이며, 생활비 외 치료비는 실손의료비에서 비급여 기준 70% 보장받은 것을 전제로, 해당 금액에 30%를 추가해서 가입해야 한다. 중대질환 외 나머지 수술비 등은 산출된 월 가처분소득을 30일로 나눈 것을 기준으로 일할 계산하여 보며, 수술비 담보는 평균 입원 30일 ~ 최대 60일을 적용하고, 로봇수술은 별도 적용해야 한다.</p>
        <p>2) 장해 등으로 인한 <b>'일실소득(상해·장해로 인한 미래 소득 감소분)'</b>은 직장을 퇴사하고 다시 재활까지 필요한 기간 5년을 전제 조건으로 해야 하며, 모든 산출 담보에서 <b>'가처분소득 × 60개월'</b>을 <b>적정 수준</b>으로 제안한다. 그러나 금액이 너무 큰 경우에는 고객과 상담하여 결정한다.</p>
        <p>3) <b>사망:</b> 상속세 부분은 별도로 계산해야 한다. <b>(개인)</b> 상속 면세점은 10억~12억 수준으로 보고 초과 금액에 대한 상속세 현금 마련을 전제로 하며, <b>(법인)</b> 상속 주식의 '비상장주식평가'와 부동산 상속의 경우에는 별건으로 산출을 진행해야 한다. 공식 가이드라인을 준수하라.</p>
    </div>
    
    <p style="text-align: center; color: #1E40AF; font-weight: bold; margin-top: 20px; font-style: italic;">
        "AI 트리니티는 단순히 보험을 파는 것이 아니라, 고객의 인생 전체를 과학적으로 재설계합니다."
    </p>
</div>
""", unsafe_allow_html=True)

    # ── [GP-HQ-ACTION] HQ 이동 액션 버튼 (고객 모드 하단) ──────────────────────
    st.markdown("""
<style>
.hq-action-button {
    display: block;
    margin: 30px auto 20px;
    max-width: 680px;
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%);
    border-radius: 20px;
    padding: 28px 40px;
    text-align: center;
    box-shadow: 0 8px 24px rgba(30, 58, 138, 0.3);
    transition: all 0.3s ease;
    cursor: pointer;
    text-decoration: none;
    position: relative;
    overflow: hidden;
}
.hq-action-button:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(30, 58, 138, 0.4);
}
.hq-action-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}
.hq-action-button:hover::before {
    left: 100%;
}
.hq-action-content {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    position: relative;
    z-index: 1;
}
.hq-action-icon {
    font-size: clamp(40px, 6vw, 56px);
    filter: drop-shadow(0 2px 8px rgba(0,0,0,0.2));
}
.hq-action-text {
    color: #ffffff;
    font-size: clamp(20px, 3.5vw, 28px);
    font-weight: 900;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 8px rgba(0,0,0,0.2);
    word-break: keep-all;
}
@media (max-width: 600px) {
    .hq-action-button {
        padding: 22px 28px;
        border-radius: 16px;
    }
    .hq-action-content {
        gap: 14px;
    }
}
</style>

<a href=""" + f"'{HQ_APP_URL.rstrip('/')}/'" + """ target="_blank" rel="noopener noreferrer" class="hq-action-button">
    <div class="hq-action-content">
        <div class="hq-action-icon">💬</div>
        <div class="hq-action-text">전문가와 함께하는<br>맞춤 솔루션</div>
    </div>
</a>
""", unsafe_allow_html=True)


# [GP-PHASE-4] 통합 증권분석 센터는 analysis 화면(_spa_screen=="analysis") 내부에서만 렌더링

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
            _cadm_id   = st.text_input("관리자 ID", key="crm_admin_id_f")
            _cadm_code = st.text_input("관리자 코드", key="crm_admin_code_f",
                                        type="password")
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
                # DOM 에러 방지: rerun 전 플래그 설정
                if not st.session_state.get("_rerun_pending"):
                    st.session_state["_rerun_pending"] = True
                    st.rerun()
            elif _cadm_code_v == _master_env and _master_env:
                _mname = get_env_secret("MASTER_NAME", "이세윤")
                st.session_state["crm_is_admin"]  = True
                st.session_state["crm_user_id"]   = "PERMANENT_MASTER"
                st.session_state["crm_user_name"] = _mname
                st.session_state["crm_role"]      = "admin"
                # DOM 에러 방지: rerun 전 플래그 설정
                if not st.session_state.get("_rerun_pending"):
                    st.session_state["_rerun_pending"] = True
                    st.rerun()
            elif _cadm_id_v.lower() in ("admin", "이세윤") and _cadm_input_hash == _cadm_pw_hash:
                st.session_state["crm_is_admin"]  = True
                st.session_state["crm_user_id"]   = "ADMIN_MASTER"
                st.session_state["crm_user_name"] = "이세윤"
                st.session_state["crm_role"]      = "admin"
                # DOM 에러 방지: rerun 전 플래그 설정
                if not st.session_state.get("_rerun_pending"):
                    st.session_state["_rerun_pending"] = True
                    st.rerun()
            else:
                st.error("ID 또는 코드가 올바르지 않습니다.")
    else:
        _cadm_name = st.session_state.get("crm_user_name", "관리자")
        st.success(f"✅ 관리자 로그인 중: **{_cadm_name}**")
        st.markdown("---")

        # ── Supabase DB 관리 ──────────────────────────────────────────────
        st.markdown(
            "<div style='display:inline-block;width:fit-content;background:#FFF8E1;"
            "border:1px solid #fde68a;border-radius:6px;padding:4px 12px;"
            "font-size:0.82rem;font-weight:900;color:#92400e;margin-bottom:8px;'>"
            "🗄️ Supabase DB 관리</div>",
            unsafe_allow_html=True,
        )
        try:
            _cadm_sb_url  = get_env_secret("SUPABASE_URL", "")
            _cadm_sb_proj = _cadm_sb_url.replace("https://", "").split(".")[0] if _cadm_sb_url else ""
        except Exception:
            _cadm_sb_proj = ""
        if _cadm_sb_proj:
            _cadm_sql_url = f"https://supabase.com/dashboard/project/{_cadm_sb_proj}/sql/new"
            st.markdown(
                f'<a href="{_cadm_sql_url}" target="_blank">'
                f'<button style="width:auto;padding:8px 18px;background:#3ecf8e;color:#fff;'
                f'border:none;border-radius:6px;font-size:0.85rem;font-weight:700;cursor:pointer;">'
                f'🔗 Supabase SQL Editor 열기</button></a>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<a href="https://supabase.com/dashboard" target="_blank">'
                '<button style="width:auto;padding:8px 18px;background:#3ecf8e;color:#fff;'
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
        
        # [Phase 3] 회원 탈퇴(계정 삭제) 기능 (구글 심사 필수)
        st.markdown(
            "<div style='background:#fee2e2;border:2px solid #dc2626;border-radius:8px;"
            "padding:16px;margin:12px 0;'>"
            "<b style='color:#991b1b;font-size:1.1rem;'>🗑️ 회원 탈퇴(계정 삭제)</b><br>"
            "<p style='color:#7f1d1d;margin:8px 0 0;font-size:0.85rem;'>"
            "구글 Play 심사 필수 요건입니다. 탈퇴 시 모든 개인 정보가 영구 삭제됩니다."
            "</p></div>",
            unsafe_allow_html=True
        )
        
        with st.form("account_deletion_form"):
            st.warning(
                "⚠️ **경고**: 탈퇴 후에는 복구가 불가능합니다.\n\n"
                "삭제될 데이터:\n"
                "- Supabase gk_members 테이블 레코드\n"
                "- GCS master_roster/ 파일\n"
                "- 모든 개인 식별 정보"
            )
            
            _delete_confirm = st.checkbox(
                "위 내용을 확인했으며, 회원 탈퇴를 진행합니다.",
                key="delete_account_confirm"
            )
            
            _delete_submit = st.form_submit_button(
                "🗑️ 회원 탈퇴 실행",
                type="primary",
                use_container_width=True,
                disabled=not _delete_confirm
            )
        
        if _delete_submit and _delete_confirm:
            try:
                from modules.account_deletion import (
                    delete_account_permanently,
                    delete_member_from_db,
                    delete_member_from_gcs
                )
                
                _current_user_id = st.session_state.get("crm_user_id", "")
                _current_user_name = st.session_state.get("crm_user_name", "")
                
                if not _current_user_id and not _current_user_name:
                    st.error("❌ 사용자 정보를 찾을 수 없습니다.")
                else:
                    # 회원 탈퇴 실행
                    success, message = delete_account_permanently(
                        user_id=_current_user_id,
                        user_name=_current_user_name,
                        db_delete_func=delete_member_from_db,
                        gcs_delete_func=delete_member_from_gcs
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        # 세션 파기
                        st.session_state.clear()
                        st.info("회원 탈퇴가 완료되었습니다. 로그인 화면으로 이동합니다...")
                        import time
                        time.sleep(3)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            except Exception as _del_err:
                st.error(f"❌ 탈퇴 처리 오류: {_del_err}")
        
        st.markdown("---")
        if st.button("🚪 관리자 로그아웃", key="crm_admin_logout_btn",
                     use_container_width=True):
            st.session_state.pop("crm_is_admin", None)
            if st.session_state.get("crm_role") == "admin":
                st.session_state["crm_role"] = "agent"
            st.rerun()

# ── [GP-TRUST] 마이페이지 메뉴 — 로그아웃 버튼 위 ──────────────────────────────
st.markdown("<hr style='border-top:1px solid #e5e7eb;margin:24px 0 8px;'>",
            unsafe_allow_html=True)

if _MYPAGE_OK:
    _mp_c1, _mp_c2, _mp_c3 = st.columns([3, 4, 3])
    with _mp_c2:
        if st.button("⚙️ 마이페이지 / 구독 관리", key="crm_mypage_btn", use_container_width=True, type="secondary"):
            st.session_state["crm_spa_mode"] = "mypage"
            st.rerun()

# ── [GP-SEC] 로그아웃 버튼 — 페이지 최하단 고정 ──────────────────────────────
st.markdown("<hr style='border-top:1px solid #e5e7eb;margin:4px 0 8px;'>",
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

