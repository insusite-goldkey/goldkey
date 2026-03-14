# shared_components.py — Goldkey AI Masters 2026
"""
[GP 마스터-그림자 원칙 Phase 1] Python/Streamlit 공통 모듈
모 앱(app.py)과 자 앱(crm_app.py) 양쪽에서 import하여 사용.
이 파일이 바뀌면 양쪽 앱이 자동으로 반영된다.

export:
    CUSTOMER_SCHEMA          — 고객 필드 정의 딕셔너리
    customer_card_html()     — 고객 1행 카드 HTML
    customer_form()          — 고객 입력/수정 폼 (Streamlit 위젯)
    customer_input_form()    — 저장 로직 (양방향 Supabase upsert)
    render_customer_list()   — 고객 목록 FlatList 렌더
    build_deeplink_to_hq()   — 자 앱 → 모 앱 딥링크 URL 생성
    build_sso_redirect()     — SSO return_to URL 생성
"""

from __future__ import annotations
import streamlit as st
import os
import uuid, datetime
from typing import Optional


def get_env_secret(key: str, default_value: str = "") -> str:
    """st.secrets가 없어도 뻗지 않고 클라우드 환경변수로 대체하는 안전한 함수"""
    try:
        return st.secrets.get(key, os.environ.get(key, default_value))
    except Exception:
        return os.environ.get(key, default_value)

# ── 모 앱 URL (환경 자동 분기) ────────────────────────────────────────────────
# GK_APP_ID=crm  → CRM 앱 컨테이너 (Dockerfile.crm에서 설정)
# K_SERVICE 존재 → Cloud Run 프로덕션 환경
# 그 외           → 로컬 개발 환경
import os as _os
_on_cloud = bool(_os.environ.get("K_SERVICE", ""))
HQ_APP_URL = (
    "https://goldkey-ai-817097913199.asia-northeast3.run.app"
    if _on_cloud
    else "http://localhost:8501"
)
CRM_APP_URL = (
    "https://goldkey-crm-vje5ef5qka-du.a.run.app"
    if _on_cloud
    else "http://localhost:8502"
)

# ── 고객 데이터 스키마 (모/자 앱 공통) ────────────────────────────────────────
CUSTOMER_SCHEMA: dict = {
    "person_id":           {"type": "str",  "required": True,  "label": "고객 ID"},
    "name":                {"type": "str",  "required": True,  "label": "이름"},
    "contact":             {"type": "str",  "required": True,  "label": "연락처"},
    "birth_date":          {"type": "date", "required": False, "label": "생년월일"},
    "gender":              {"type": "str",  "required": False, "label": "성별",
                            "options": ["남성", "여성"]},
    "address":             {"type": "str",  "required": False, "label": "주소"},
    "job":                 {"type": "str",  "required": False, "label": "직업"},
    "memo":                {"type": "text", "required": False, "label": "메모"},
    "status":              {"type": "str",  "required": False, "label": "상태",
                            "options": ["potential", "active", "contracted", "closed"],
                            "default": "potential"},
    "management_tier":     {"type": "int",  "required": False, "label": "관리 등급",
                            "options": [1, 2, 3], "default": 3},
    "auto_renewal_month":  {"type": "int",  "required": False, "label": "자동차보험 만기월"},
    "fire_renewal_month":  {"type": "int",  "required": False, "label": "화재보험 만기월"},
    "last_auto_carrier":   {"type": "str",  "required": False, "label": "기존 자동차보험사"},
    "is_favorite":         {"type": "bool", "required": False, "label": "즐겨찾기",
                            "default": False},
    "prospecting_stage":   {"type": "str",  "required": False, "label": "개척 단계",
                            "options": ["lead", "contact", "proposal", "contracted"],
                            "default": "lead"},
    "community_tags":      {"type": "list", "required": False, "label": "소속 모임"},
    "risk_note":           {"type": "text", "required": False, "label": "고위험 메모"},
    "agent_id":            {"type": "str",  "required": False, "label": "담당 설계사 ID"},
}

TIER_META = {
    1: {"label": "VVIP", "color": "#b45309", "bg": "#fef3c7", "icon": "👑"},
    2: {"label": "핵심",  "color": "#1d4ed8", "bg": "#dbeafe", "icon": "⭐"},
    3: {"label": "일반",  "color": "#374151", "bg": "#f3f4f6", "icon": "👤"},
}
STATUS_META = {
    "potential":  {"label": "가망",   "color": "#6b7280", "bg": "#f3f4f6"},
    "active":     {"label": "진행중", "color": "#2563eb", "bg": "#dbeafe"},
    "contracted": {"label": "계약",   "color": "#16a34a", "bg": "#dcfce7"},
    "closed":     {"label": "종료",   "color": "#dc2626", "bg": "#fee2e2"},
}
STAGE_META = {
    "lead":       {"label": "발굴", "step": 1},
    "contact":    {"label": "접촉", "step": 2},
    "proposal":   {"label": "제안", "step": 3},
    "contracted": {"label": "계약", "step": 4},
}


# ── 고객 카드 HTML ─────────────────────────────────────────────────────────────
def customer_card_html(c: dict, *, show_deeplink: bool = True, agent_tab: str = "t1") -> str:
    """
    고객 1명에 대한 카드 HTML 반환.
    show_deeplink=True 이면 [🚀 HQ 정밀 분석] 버튼 포함.
    """
    tier   = c.get("management_tier", 3)
    tm     = TIER_META.get(tier, TIER_META[3])
    status = c.get("status", "potential")
    sm     = STATUS_META.get(status, STATUS_META["potential"])

    renewal = ""
    if c.get("auto_renewal_month"):
        renewal += f"🚗 자동차 {c['auto_renewal_month']}월  "
    if c.get("fire_renewal_month"):
        renewal += f"🏠 화재 {c['fire_renewal_month']}월"
    renewal_html = (
        f"<div style='font-size:0.75rem;color:#d97706;margin-top:3px;'>🔔 만기: {renewal}</div>"
        if renewal else ""
    )

    deeplink_btn = ""
    if show_deeplink:
        deeplink_url = build_deeplink_to_hq(
            cid=c.get("person_id", ""),
            name=c.get("name", ""),
            sector=agent_tab,
        )
        deeplink_btn = f"""
<a href="{deeplink_url}" target="_blank" style="display:inline-block;margin-top:8px;
  padding:5px 12px;background:#1e3a8a;color:#fff;border-radius:7px;
  font-size:0.76rem;font-weight:900;text-decoration:none;
  border:1px dashed #93c5fd;">
  🚀 HQ 모 앱에서 정밀 분석 진행
</a>"""

    avatar_char = (c.get("name") or "?")[0]
    return f"""
<div style="background:#fff;border:1px dashed #000;border-radius:10px;
  padding:12px 14px;margin-bottom:8px;display:flex;align-items:flex-start;gap:12px;">
  <div style="width:44px;height:44px;border-radius:50%;background:{tm['bg']};
    border:1px dashed #000;display:flex;align-items:center;justify-content:center;
    font-size:1.2rem;font-weight:900;color:{tm['color']};flex-shrink:0;">
    {avatar_char}
  </div>
  <div style="flex:1;min-width:0;">
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
      <span style="font-size:1rem;font-weight:900;color:#1e293b;">{c.get('name','')}</span>
      <span style="font-size:0.72rem;font-weight:700;color:{tm['color']};
        background:{tm['bg']};padding:1px 6px;border-radius:5px;
        border:1px dashed {tm['color']};">{tm['icon']} {tm['label']}</span>
      <span style="font-size:0.72rem;font-weight:700;color:{sm['color']};
        background:{sm['bg']};padding:1px 6px;border-radius:5px;">{sm['label']}</span>
    </div>
    <div style="font-size:0.80rem;color:#6b7280;margin-top:2px;">
      {c.get('job', '')}  {'·' if c.get('job') and c.get('contact') else ''}  {c.get('contact', '')}
    </div>
    {renewal_html}
    {deeplink_btn}
  </div>
</div>"""


# ── 고객 목록 렌더 ─────────────────────────────────────────────────────────────
def render_customer_list(customers: list[dict], *, show_deeplink: bool = True,
                         agent_tab: str = "t1") -> None:
    """Streamlit에 고객 카드 목록 렌더링."""
    if not customers:
        st.info("등록된 고객이 없습니다.")
        return
    html_blocks = "".join(
        customer_card_html(c, show_deeplink=show_deeplink, agent_tab=agent_tab)
        for c in customers
    )
    st.markdown(html_blocks, unsafe_allow_html=True)


# ── 고객 입력 폼 (Streamlit 위젯) ────────────────────────────────────────────
def customer_form(initial: Optional[dict] = None, *, key_prefix: str = "cf") -> dict:
    """
    [Phase 1 §2] 고객 정보 입력/수정 폼 — 모/자 앱 양방향 공통.
    반환값: 수정된 고객 딕셔너리 (저장하려면 customer_input_form() 호출)
    """
    d = initial or {}
    col1, col2 = st.columns(2)
    with col1:
        name    = st.text_input("이름 *",    value=d.get("name", ""),    key=f"{key_prefix}_name")
        contact = st.text_input("연락처 *",  value=d.get("contact", ""), key=f"{key_prefix}_contact",
                                placeholder="010-0000-0000")
        job     = st.text_input("직업",      value=d.get("job", ""),     key=f"{key_prefix}_job")
    with col2:
        gender  = st.selectbox("성별",        ["(선택)", "남성", "여성"],
                               index=["(선택)", "남성", "여성"].index(d.get("gender") or "(선택)"),
                               key=f"{key_prefix}_gender")
        tier    = st.selectbox("관리 등급",   [3, 2, 1],
                               format_func=lambda x: TIER_META[x]["label"],
                               index=[3, 2, 1].index(d.get("management_tier", 3)),
                               key=f"{key_prefix}_tier")
        auto_mo = st.number_input("자동차보험 만기월", min_value=0, max_value=12,
                                  value=d.get("auto_renewal_month") or 0,
                                  key=f"{key_prefix}_auto_mo",
                                  help="0=없음, 1~12=월")
    memo = st.text_area("메모", value=d.get("memo", ""), key=f"{key_prefix}_memo", height=80)

    return {
        **d,
        "name":                name,
        "contact":             contact,
        "job":                 job,
        "gender":              None if gender == "(선택)" else gender,
        "management_tier":     tier,
        "auto_renewal_month":  auto_mo or None,
        "memo":                memo,
    }


# ── [Phase 1 §2] 양방향 CRUD — customer_input_form() ─────────────────────────
def customer_input_form(customer_data: dict, agent_id: str,
                        supabase_client=None) -> dict:
    """
    고객 정보 저장 (Supabase upsert).
    모 앱과 자 앱 양쪽에서 동일하게 호출. 동일한 gk_people 테이블 업데이트.

    Args:
        customer_data:   CUSTOMER_SCHEMA 기반 dict
        agent_id:        현재 설계사 user_id
        supabase_client: supabase-py Client 인스턴스 (없으면 secrets에서 자동 생성)
    Returns:
        저장된 레코드 dict
    Raises:
        ValueError: 필수 필드 누락
        Exception:  Supabase 오류
    """
    if not customer_data.get("name", "").strip():
        raise ValueError("이름을 입력해 주세요.")
    if not customer_data.get("contact", "").strip():
        raise ValueError("연락처를 입력해 주세요.")

    if supabase_client is None:
        try:
            from supabase import create_client
            sb_url = get_env_secret("SUPABASE_URL", "")
            sb_key = get_env_secret("SUPABASE_SERVICE_ROLE_KEY",
                        get_env_secret("SUPABASE_KEY", ""))
            supabase_client = create_client(sb_url, sb_key)
        except Exception as e:
            raise RuntimeError(f"Supabase 연결 실패: {e}")

    now = datetime.datetime.utcnow().isoformat()
    row = {
        **customer_data,
        "agent_id":   agent_id,
        "updated_at": now,
        "is_deleted": False,
    }
    if not row.get("person_id"):
        row["person_id"] = str(uuid.uuid4())
        row["created_at"] = now

    resp = (
        supabase_client.table("gk_people")
        .upsert(row, on_conflict="person_id")
        .execute()
    )
    if resp.data:
        return resp.data[0]
    raise RuntimeError("저장 응답 데이터 없음")


# ── 딥링크 빌더 ─────────────────────────────────────────────────────────────
def build_deeplink_to_hq(cid: str, name: str = "", sector: str = "home",
                         token: str = "") -> str:
    """
    [Phase 3] 자 앱 → 모 앱(HQ) 딥링크 URL 생성.
    cid, token, sector를 URL 파라미터로 전달.
    """
    import urllib.parse as _up
    params = {"gk_cid": cid, "gk_sector": sector}
    if name:    params["gk_name"]  = name
    if token:   params["gk_token"] = token
    return f"{HQ_APP_URL}/?{_up.urlencode(params)}"


def build_sso_redirect(return_to: str) -> str:
    """
    [Phase 2] SSO: 자 앱 → 모 앱 로그인 후 return_to로 리다이렉트.
    """
    import urllib.parse as _up
    return f"{HQ_APP_URL}/?{_up.urlencode({'return_to': return_to})}"


# ── 응접 데스크 패널 렌더 (모 앱 전용) ────────────────────────────────────────
def render_reception_desk(*, key_prefix: str = "_rd") -> None:
    """
    [Phase 4] 모 앱 홈 상단에 영구 고정되는 'HQ 응접 데스크' 패널.
    URL query_params에서 gk_cid / gk_token / gk_sector 수신 시 자동 도킹.
    """
    cid    = st.query_params.get("gk_cid",    "")
    name   = st.query_params.get("gk_name",   "")
    sector = st.query_params.get("gk_sector", "")
    token  = st.query_params.get("gk_token",  "")

    # 도킹 상태 세션에 보존 (query_params는 곧 지워지므로)
    if cid and not st.session_state.get(f"{key_prefix}_docked_cid"):
        st.session_state[f"{key_prefix}_docked_cid"]    = cid
        st.session_state[f"{key_prefix}_docked_name"]   = name
        st.session_state[f"{key_prefix}_docked_sector"] = sector
        st.session_state[f"{key_prefix}_docked_token"]  = token
        st.session_state[f"{key_prefix}_loading"]       = True
        st.query_params.clear()
        st.rerun()

    _cid    = st.session_state.get(f"{key_prefix}_docked_cid",    "")
    _name   = st.session_state.get(f"{key_prefix}_docked_name",   "")
    _sector = st.session_state.get(f"{key_prefix}_docked_sector", "")
    _loading = st.session_state.get(f"{key_prefix}_loading", False)

    with st.container(border=True):
        if not _cid:
            # 비어있는 기본 상태
            st.markdown(
                "<div style='padding:6px 0;color:#94a3b8;font-size:0.85rem;text-align:center;'>"
                "🛎️ <b>응접 데스크</b> — CRM에서 고객을 선택하면 여기에 자동 도킹됩니다.</div>",
                unsafe_allow_html=True,
            )
            return

        if _loading:
            with st.spinner("🛎️ CRM에서 고객 정보를 안전하게 불러오고 있습니다..."):
                import time; time.sleep(0.6)
            st.session_state[f"{key_prefix}_loading"] = False
            st.rerun()

        # 도킹 완료 상태
        col_info, col_action = st.columns([3, 1])
        with col_info:
            st.markdown(
                f"<div style='padding:4px 0;'>"
                f"<span style='font-size:1.0rem;font-weight:900;color:#16a34a;'>✅ HQ 정밀 상담 도킹 완료</span>"
                f"<span style='font-size:0.9rem;font-weight:900;color:#1e293b;margin-left:10px;'>{_name}</span>"
                f"<span style='font-size:0.75rem;color:#6b7280;margin-left:8px;'>CID: {_cid[:8]}...</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if _sector and _sector not in ("home", ""):
                _sector_labels = {
                    "cancer": "암보험 분석", "brain": "뇌혈관 분석",
                    "heart": "심장 분석", "fire": "화재보험",
                    "auto": "자동차보험", "t1": "보험금 청구 상담",
                    "t2": "실손 분석", "t3": "KB7 보장 분석",
                }
                _label = _sector_labels.get(_sector, _sector)
                st.caption(f"📍 목적지 섹터: **{_label}** — 자동 이동 중")
        with col_action:
            if st.button("✕ 도킹 해제", key=f"{key_prefix}_undock", use_container_width=True):
                for _k in [f"{key_prefix}_docked_cid", f"{key_prefix}_docked_name",
                            f"{key_prefix}_docked_sector", f"{key_prefix}_docked_token",
                            f"{key_prefix}_loading"]:
                    st.session_state.pop(_k, None)
                st.rerun()

        # 섹터 자동 점프 (JS Smooth Scroll)
        if _sector and _sector not in ("home", ""):
            _jump_done_key = f"{key_prefix}_jumped_{_cid}_{_sector}"
            if not st.session_state.get(_jump_done_key):
                st.session_state[_jump_done_key] = True
                # current_tab을 섹터로 이동
                st.session_state["current_tab"] = _sector
                st.session_state["_scroll_top"] = True
                import streamlit.components.v1 as _jcomp
                _jcomp.html(f"""
<script>
(function() {{
  function scrollToSector() {{
    try {{
      var pd = window.parent.document;
      var el = pd.getElementById('{_sector}') || pd.querySelector('[data-sector="{_sector}"]');
      if (el) {{
        el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
    }} catch(e) {{}}
  }}
  setTimeout(scrollToSector, 800);
  setTimeout(scrollToSector, 1800);
}})();
</script>""", height=0)
                st.rerun()
