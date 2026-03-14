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
)

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="골드키 CRM — 현장 기동대",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 전역 CSS (1px dashed #000 기본값) ─────────────────────────────────────────
st.markdown("""
<style>
body, .stApp { background: #f0f4ff !important; }
.gk-card {
  background: #fff; border: 1px dashed #000;
  border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;
}
.gk-section-title {
  font-size: 1.05rem; font-weight: 900; color: #1e3a8a;
  border-bottom: 2px solid #1e3a8a; padding-bottom: 4px; margin-bottom: 12px;
}
.gk-badge {
  display: inline-block; font-size: 0.72rem; font-weight: 700;
  padding: 2px 8px; border-radius: 5px; border: 1px dashed currentColor;
}
.gk-deeplink-btn {
  display: inline-block; background: #1e3a8a; color: #fff !important;
  border: 1px dashed #93c5fd; border-radius: 8px;
  padding: 6px 14px; font-size: 0.82rem; font-weight: 900;
  text-decoration: none; margin-top: 8px;
}
.gk-deeplink-btn:hover { background: #1d4ed8; }
div[data-testid="stMainBlockContainer"] { padding-top: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# [Phase 2] SSO 인증 처리
# 세션 없으면 모 앱으로 자동 리다이렉트 (?return_to=crm_url)
# ══════════════════════════════════════════════════════════════════════════════
# ── 환경 감지: 로컬 개발 vs 프로덕션 ──────────────────────────────────────────
_IS_LOCAL = (
    os.environ.get("STREAMLIT_ENV", "") == "local"
    or st.secrets.get("ENV", "") == "local"
    or os.environ.get("GAE_ENV", "") == ""
    and not os.environ.get("K_SERVICE", "")  # Cloud Run 환경변수 없으면 로컬
)
CRM_URL = st.secrets.get("CRM_URL", "http://localhost:8502")

def _check_sso_token() -> bool:
    """URL에서 SSO 토큰 수신 → 세션 설정 → 인증 완료."""
    _token   = st.query_params.get("token",   "")
    _user_id = st.query_params.get("user_id", "")
    _name    = st.query_params.get("name",    "")
    _role    = st.query_params.get("role",    "agent")
    if _token and _user_id:
        st.session_state["crm_authenticated"] = True
        st.session_state["crm_user_id"]       = _user_id
        st.session_state["crm_user_name"]     = _name
        st.session_state["crm_role"]          = _role
        st.session_state["crm_token"]         = _token
        st.query_params.clear()
        return True
    return False

def _is_authenticated() -> bool:
    return st.session_state.get("crm_authenticated", False)

# SSO 토큰 수신 처리
if _check_sso_token():
    st.rerun()

# ── 미인증 처리 ───────────────────────────────────────────────────────────────
if not _is_authenticated():
    if _IS_LOCAL:
        # ── [로컬 개발 모드] Supabase 직접 로그인 폼 ──────────────────────────
        st.markdown("""
<div style="max-width:420px;margin:60px auto;background:#fff;
  border:1px dashed #000;border-radius:20px;padding:28px;text-align:center;">
  <div style="font-size:2.4rem;margin-bottom:6px;">📱</div>
  <div style="font-size:1.2rem;font-weight:900;color:#1e3a8a;margin-bottom:2px;">골드키 CRM</div>
  <div style="font-size:0.78rem;color:#6b7280;margin-bottom:18px;">
    로컬 개발 모드 — 직접 로그인
  </div>
</div>""", unsafe_allow_html=True)
        with st.form("crm_local_login"):
            _lid  = st.text_input("사용자 ID (user_id)", placeholder="예: agent_001")
            _lnm  = st.text_input("이름", placeholder="예: 홍길동")
            _submitted = st.form_submit_button("🔑 개발 모드 로그인", use_container_width=True, type="primary")
        if _submitted and _lid:
            st.session_state["crm_authenticated"] = True
            st.session_state["crm_user_id"]       = _lid
            st.session_state["crm_user_name"]     = _lnm or "설계사"
            st.session_state["crm_role"]          = "agent"
            st.session_state["crm_token"]         = "dev-token"
            st.rerun()
        st.caption("💡 로컬 테스트용. 프로덕션에서는 SSO 인증이 적용됩니다.")
        st.stop()
    else:
        # ── [프로덕션] 모 앱 SSO 리다이렉트 ──────────────────────────────────
        sso_url = build_sso_redirect(CRM_URL)
        st.markdown(f"""
<div style="max-width:420px;margin:80px auto;background:#fff;
  border:1px dashed #000;border-radius:20px;padding:32px;text-align:center;">
  <div style="font-size:3rem;margin-bottom:8px;">🔑</div>
  <div style="font-size:1.2rem;font-weight:900;color:#1e3a8a;margin-bottom:4px;">골드키 CRM</div>
  <div style="font-size:0.85rem;color:#6b7280;margin-bottom:20px;">SSO 통합 인증이 필요합니다</div>
  <div style="background:#eff6ff;border:1px dashed #000;border-radius:10px;
    padding:14px;font-size:0.82rem;color:#374151;text-align:left;margin-bottom:20px;">
    <b>📋 로그인 방법</b><br>
    1. 아래 버튼 → Goldkey AI 로그인<br>
    2. 로그인 완료 후 자동으로 CRM으로 복귀
  </div>
  <a href="{sso_url}" target="_self" style="display:block;background:#1d4ed8;
    color:#fff;border-radius:12px;padding:12px;font-weight:900;
    font-size:1rem;text-decoration:none;border:1px dashed #93c5fd;">
    🚀 Goldkey AI로 로그인
  </a>
  <div style="font-size:0.70rem;color:#9ca3af;margin-top:14px;">
    Powered by Goldkey AI SSO · GP-SSO §1
  </div>
</div>""", unsafe_allow_html=True)
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
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY",
                              st.secrets.get("SUPABASE_KEY", ""))
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
    <span style="font-size:0.78rem;color:#93c5fd;margin-left:10px;">현장 기동대 · Shadow App</span>
  </div>
  <div style="font-size:0.82rem;color:#e2e8f0;">{_user_name} 설계사</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 탭 네비게이션
# ══════════════════════════════════════════════════════════════════════════════
TAB_BRIEFING  = "🌅 AI 브리핑"
TAB_CUSTOMERS = "👥 고객 목록"
TAB_SCHEDULE  = "📅 일정"
TAB_DEEPLINK  = "🚀 HQ 연결"
TAB_HQ_GUIDE  = "🏢 HQ 앱 안내"

_active_tab = st.session_state.get("crm_tab", TAB_BRIEFING)
tab1, tab2, tab3, tab4, tab5 = st.tabs([TAB_BRIEFING, TAB_CUSTOMERS, TAB_SCHEDULE, TAB_DEEPLINK, TAB_HQ_GUIDE])

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
    {c.get('job', '')} · {c.get('contact', '')}
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
# TAB 4: HQ 딥링크 발사대 + Fallback
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="gk-section-title">🚀 HQ 모 앱 연결 — 정밀 분석 발사대</div>',
                unsafe_allow_html=True)
    st.caption("복잡한 보험 분석은 모 앱(Goldkey AI HQ)에 위임합니다.")

    # 고객 선택 후 섹터 지정 → 딥링크 생성
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

        # Fallback: 링크 실패 시 안내
        with st.expander("❓ 모 앱이 열리지 않는다면?", expanded=False):
            st.markdown(f"""
<div style="background:#eff6ff;border:1px dashed #000;border-radius:10px;padding:14px;font-size:0.85rem;">
  <b>📌 안내 데스크 (Fallback 가이드)</b><br><br>
  1️⃣ <b>웹 브라우저</b>로 직접 접속:<br>
  &nbsp;&nbsp;<a href="{HQ_APP_URL}" target="_blank">{HQ_APP_URL}</a><br><br>
  2️⃣ 로그인 후 상단 주소창에 아래 파라미터를 추가하세요:<br>
  &nbsp;&nbsp;<code>?gk_cid={_sel_cust.get('person_id','')}&gk_sector={_sel_sector}</code><br><br>
  3️⃣ 모바일에서 앱이 미설치 시: 위 링크를 북마크에 추가하세요.
</div>""", unsafe_allow_html=True)
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

# ── 푸터 ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;font-size:0.72rem;color:#9ca3af;padding:8px 0;">
  본 앱은 Goldkey AI Masters 2026의 서브 애플리케이션(Shadow App)입니다.<br>
  모든 AI 분석 및 정밀 상담 로직은 모 앱의 보안 프로토콜을 따릅니다.<br>
  GP 마스터-그림자 원칙 Phase 1~4 준수
</div>
""", unsafe_allow_html=True)
