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


def get_clean_phone(raw: str) -> str:
    """[GP-회원관리 §연락처표준] 연락처 표준 정규화 — 숫자만 추출
    하이픈(-), 공백, 괄호, 특수문자 등 모두 제거 후 순수 숫자만 반환.
    모든 연락처 비교·해싱·저장 전 반드시 이 함수를 먼저 호출할 것.
    """
    if not raw:
        return ""
    return "".join(filter(str.isdigit, str(raw)))

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
      {c.get('job', '')}  {'·' if c.get('job') and c.get('contact') else ''}  {decrypt_pii(c.get('contact', ''))}
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
        # [GP-SEC §1] 저장된 Fernet 암호화값 → 평문으로 복호화하여 표시
        _disp_contact = decrypt_pii(d.get("contact", "")) if d.get("contact") else ""
        contact = st.text_input("연락처 *",  value=_disp_contact, key=f"{key_prefix}_contact",
                                placeholder="010-00000000 (숫자만)")
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

    # [GP-SEC §1][GP-회원관리 §연락처표준] 저장 게이트웨이: 정규화 → Fernet 암호화
    _raw_contact = customer_data.get("contact", "")
    _clean_contact = get_clean_phone(_raw_contact)
    if _clean_contact:  # 유효한 전화번호인 경우만 암호화 (이미 암호화된 경우 skip)
        try:
            _dec_test = decrypt_pii(_raw_contact)
            if _dec_test == _raw_contact and not _raw_contact.startswith("gAAAA"):
                # 아직 평문 → 정규화 후 암호화
                customer_data = dict(customer_data)
                customer_data["contact"] = encrypt_pii(_clean_contact)
        except Exception:
            pass

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
def build_deeplink_to_hq(cid: str, agent_id: str = "", name: str = "", sector: str = "home",
                         token: str = "", user_id: str = "") -> str:
    """
    [Phase 3 — C-2 PII 보호 및 SSO 완성] CRM → HQ 딥링크 URL 생성.
    평문 PII(이름, 연락처) 절대 배제. AgentID + CID 결합 HMAC-SHA256 토큰 생성.
    name / token 파라미터는 하위 호환성 유지용 — URL에 포함하지 않음.
    user_id 제공 시: [GP-SEC §2] SSO auth_token 자동 생성 포함 → HQ 이중 로그인 방지.
    """
    import urllib.parse as _up
    import hmac as _hmac_dl
    _dl_secret = get_env_secret("ENCRYPTION_KEY", "gk_token_secret_2026")
    if isinstance(_dl_secret, bytes):
        _dl_secret = _dl_secret.decode()
    _dl_agent = agent_id or ""
    _dl_token = _hmac_dl.new(
        _dl_secret.encode(), (_dl_agent + cid).encode(), "sha256"
    ).hexdigest()[:32]
    params = {
        "gk_agent_id": _dl_agent,
        "gk_cid":      cid,
        "gk_sector":   sector,
        "gk_token":    _dl_token,
    }
    # [GP-SEC §2] SSO 핸드오프 — user_id 제공 시 타임스탬프 기반 auth_token 자동 삽입
    # 리플레이 공격 차단: HMAC(KEY, user_id + str(ts)) + ts 동시 전송 (300초 유효)
    if user_id:
        import time as _time_dl
        _ts = int(_time_dl.time())
        _auth_tok = _hmac_dl.new(
            _dl_secret.encode(), (user_id + str(_ts)).encode(), "sha256"
        ).hexdigest()[:32]
        params["auth_token"] = _auth_tok
        params["user_id"]    = user_id
        params["ts"]         = _ts
    return f"{HQ_APP_URL}/?{_up.urlencode(params)}"


def build_sso_redirect(return_to: str) -> str:
    """
    [Phase 2] SSO: 자 앱 → 모 앱 로그인 후 return_to로 리다이렉트.
    """
    import urllib.parse as _up
    return f"{HQ_APP_URL}/?{_up.urlencode({'return_to': return_to})}"


def build_deeplink_to_crm(user_id: str, pid: str = "", screen: str = "contact") -> str:
    """
    [GP-SEC §2] HQ → CRM 복귀 딥링크 URL 생성.
    auth_token + user_id + crm_pid 포함 → CRM 수신 시 자동 인증 + 고객 화면 복원.
    타임스탬프 기반 HMAC-SHA256 토큰 (300초 유효) — 리플레이 공격 차단.
    """
    import urllib.parse as _up
    import hmac as _hmac_crm
    import time as _time_crm
    _secret = get_env_secret("ENCRYPTION_KEY", "gk_token_secret_2026")
    if isinstance(_secret, bytes):
        _secret = _secret.decode()
    _ts = int(_time_crm.time())
    _auth_tok = _hmac_crm.new(
        _secret.encode(), (user_id + str(_ts)).encode(), "sha256"
    ).hexdigest()[:32]
    params: dict = {
        "auth_token": _auth_tok,
        "user_id":    user_id,
        "ts":         str(_ts),
    }
    if pid:
        params["crm_pid"] = pid
    if screen:
        params["crm_screen"] = screen
    return f"{CRM_APP_URL}/?{_up.urlencode(params)}"


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
            _rd_uid = st.session_state.get("user_id", "")
            if _rd_uid and _cid:
                try:
                    _crm_back_url = build_deeplink_to_crm(
                        user_id=_rd_uid, pid=_cid, screen="contact"
                    )
                    st.markdown(
                        f"<a href='{_crm_back_url}' target='_self' style='"
                        "display:block;text-align:center;background:#f0fdf4;"
                        "color:#15803d;border:1px solid #86efac;border-radius:8px;"
                        "padding:5px 4px;font-size:0.72rem;font-weight:900;"
                        "text-decoration:none;margin-bottom:4px;'>"
                        "🔙 CRM 복귀</a>",
                        unsafe_allow_html=True,
                    )
                except Exception:
                    pass
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


# ── [내보험다보여 연동 전용 안내문] — 신용정보법 제32조 별도 고지 의무 ──────────
_NIBO_CONSENT_VERSION = "2026-03-16-v1"   # 개정 시 이 값을 변경 (동의 이력에 기록)
_NIBO_CONSENT_HTML = """
<div style='font-size:0.80rem;line-height:1.85;color:#1e293b;'>
<b style='font-size:0.88rem;color:#1a3a5c;'>[내보험다보여 서비스 연동 및 신용정보 활용 안내]</b><br><br>

<b>1. 서비스 연계 개요</b><br>
본 서비스는 한국신용정보원의 '내보험다보여' 시스템과 연동하여 고객님의 보험 가입 내역을 통합 분석합니다.
법적 근거: 신용정보의 이용 및 보호에 관한 법률 제32조(개인신용정보 제공·활용에 대한 동의)<br><br>

<b>2. 신용정보 수집 및 활용</b><br>
• <b>수집 항목:</b> 보험사명, 상품명, 증권번호, 담보 내역, 보험료, 계약 상태<br>
• <b>활용 목적:</b> AI 트리니티 엔진 기반 보장 적정성 분석 및 실질 생계비 기반 리모델링 제안<br>
• <b>보유 기간:</b> 분석 완료 후 30일 경과 시 자동 파기 (보고서 이력은 최대 3년 암호화 보관)<br><br>

<b>3. 책임의 한계</b><br>
제공되는 정보는 한국신용정보원 등록 데이터 기준이며, 실제 증권 내용과 미세한 차이가 있을 수 있습니다.
정확한 분석을 위해 증권 스캔 기능을 병행하시길 권장합니다.<br><br>

<b>4. 정보 보호 조치</b><br>
• 연동 시 인증 정보(ID/PW/간편인증 세션)는 데이터 추출 후 <b>즉시 메모리에서 파기</b>되며 서버 저장 불가<br>
• 담보 내역 등 분석 결과는 AES-256 암호화 후 저장, 관리자도 원문 열람 불가<br>
• 연락처 등 PII는 SHA-256 단방향 해시로만 DB에 저장 (GP-SEC §1)<br><br>

<b>5. 동의 거부권 및 불이익</b><br>
본 동의를 거부할 권리가 있습니다. 단, 미동의 시 'AI 증권분석' 및 '트리니티 리포트' 서비스 이용이 제한됩니다.<br><br>

<i style='color:#6b7280;font-size:0.74rem;'>안내문 버전: 2026-03-16-v1 | 출처: 신용정보의 이용 및 보호에 관한 법률 제32조</i>
</div>
"""

# ── [GP-SEC §5] 공통 약관 원문 (HQ/CRM 양쪽 render_auth_screen에서 사용) ──────
_TERMS_TEXT = """■ Goldkey AI Master Lab. Beta 이용약관

[제1조 목적]
본 약관은 Goldkey AI Master Lab. Beta 서비스(이하 '서비스')의 이용 조건 및 절차,
운영자와 회원의 권리·의무 및 책임사항을 규정함을 목적으로 합니다.

[제2조 서비스 이용 조건]
- 현재 전체 무료 베타 서비스 운영 중
- 회원 1인당 1일 10회 AI 상담 이용 제한
- 사용기간: 2026.08.31. 한정 (앱 고도화기간)
- 만 19세 이상 보험 관련 업무 종사자 및 관심 고객 대상

[제5조 개인정보 수집 및 이용]
- 수집 항목: 이름, 연락처(암호화 저장), 이용 횟수
- 이용 목적: 회원 인증, 이용 한도 관리, 서비스 품질 개선
- 보유 기간: 회원 탈퇴 후 즉시 파기 (법령 의무 보존 기간 제외)
- 제3자 제공: 법령에 의한 경우 외 제공 금지

[제5조의2 회원 개인정보 암호화 보호]
본 서비스는 회원의 개인정보를 다음과 같이 기술적으로 보호합니다.
- 연락처(비밀번호): SHA-256 단방향 해시(One-Way Hash) 방식으로 변환하여 저장합니다.
  단방향 해시는 원문으로 되돌릴 수 없는 구조로, 운영자·관리자를 포함한 누구도
  가입 시 입력한 연락처 원문을 열람하거나 복원할 수 없습니다.
- 이름: 회원 인증 및 서비스 제공 목적으로만 사용되며, 외부에 제공되지 않습니다.
- 세션 데이터: AES 기반 Fernet 대칭키 암호화로 보호되며, 세션 종료 시 자동 파기됩니다.
- 전송 구간: TLS(HTTPS) 암호화를 통해 전송 중 데이터를 보호합니다.
▶ 요약: 가입 회원의 연락처(비밀번호)는 암호화된 해시값으로만 저장되며,
  관리자를 포함한 어떠한 주체도 원문을 확인할 수 없습니다.

[제6조 고객정보 보안 기준]
- 연락처: SHA-256 단방향 해시 암호화 저장 (복호화 불가 — 관리자 포함 원문 열람 불가)
- 세션 데이터: AES-128 Fernet 암호화
- 전송 구간: TLS 암호화 (서버 레벨)
- 분석 내용: 서버에 저장하지 않으며 세션 종료 시 자동 파기
- ISO/IEC 27001 정보보안 관리체계 준거 / GDPR 및 개인정보보호법 준거

[제7조 고객정보 폐기 지침]
- 즉시 파기: 회원 탈퇴 요청 시 회원 DB에서 즉시 삭제
- 자동 파기: 세션 종료 시 메모리 내 상담 내용 자동 초기화
- 정기 파기: 이용 로그는 90일 경과 후 자동 삭제
- 파기 방법: 전자적 파일은 복구 불가능한 방법으로 영구 삭제

[제8조 면책 고지]
본 서비스는 AI 기술을 활용한 상담 보조 도구이며, 모든 분석 결과의 최종 판단 및
법적 책임은 사용자(상담원)에게 있습니다.
보험금 지급 여부의 최종 결정은 보험사 심사 및 관련 법령에 따르며,
법률·세무·의료 분야의 최종 판단은 반드시 해당 전문가와 확인하십시오.
본 서비스는 보험 모집·중개·알선 행위와 무관한 순수 AI 분석 보조 도구이며,
분석 결과를 활용한 보험 계약 체결에 대해 앱 운영자는 일체의 법적 책임을 지지 않습니다.
"""


def render_auth_screen(
    app_name: str = "Goldkey AI",
    app_icon: str = "🏆",
    terms_agree_key: str = "_gp_terms_agreed",
    show_header: bool = True,
    show_terms_scroll: bool = True,
    show_nibo_box: bool = True,
    show_checkboxes: bool = True,
    consent_header_text: str = None,
    consent_header_bg: str = "#dbeafe",
    consent_header_fg: str = "#1e3a8a",
) -> bool:
    """
    [GP-SEC §5] 공통 로그인/약관 동의 UI.
    HQ 앱(사이드바 내부)과 CRM 앱(메인 화면) 양쪽에서 호출.

    약관 원문을 HTML div 스크롤 박스에 렌더링하고,
    동의 체크박스가 체크된 경우에만 로그인 버튼 활성화 가능하도록
    bool 값(동의 여부)을 반환한다.

    Returns:
        True  — 약관 동의 완료 (로그인 버튼 활성화 허용)
        False — 미동의 (로그인 버튼 disabled 처리)
    """
    if show_header:
        st.markdown(
            f"<div style='font-size:0.88rem;font-weight:900;color:#1e3a8a;"
            f"margin-bottom:6px;text-align:center;'>{app_icon} {app_name} 이용약관</div>",
            unsafe_allow_html=True,
        )
    _terms_md = st.markdown if show_terms_scroll else (lambda *a, **k: None)
    _terms_md(
        "<div style='max-height:220px;overflow-y:auto;font-size:0.76rem;"
        "color:#222;line-height:1.75;border:1px dashed #000;border-radius:8px;"
        "padding:10px 14px;background:#f9fafb;margin-bottom:8px;'>"

        "<b style='color:#0a1628;'>[제1조] 목적</b><br>"
        "본 약관은 Goldkey AI Master Lab. Beta(이하 '서비스')의 이용 조건·절차, 운영자와 회원 간의 권리·의무 및 책임사항을 규정합니다.<br><br>"

        "<b style='color:#0a1628;'>[제2조] 서비스 이용 조건</b><br>"
        "• 현재 <b>전체 무료</b> 베타 서비스 운영 중 / 회원 1인당 <b>1일 10회</b> AI 상담 이용 제한<br>"
        "• <b>사용기간: 2026.08.31. 한정</b> / 만 19세 이상 보험 관련 업무 종사자 대상<br><br>"

        "<b style='color:#0a1628;'>[제3조] 서비스 범위</b><br>"
        "보험 상담 보조 AI 분석 도구 / 세무·법인·상속·증여 참고 정보 / 보험사 연락처 및 청구 절차 안내<br><br>"

        "<b style='color:#0a1628;'>[제4조] 금지 행위</b><br>"
        "타인 명의 도용·허위 정보 입력 금지 / 서비스를 이용한 불법 행위·부당 승환 금지 / 시스템 해킹·크롤링·자동화 접근 금지<br><br>"

        "<b style='color:#0a1628;'>[제5조] 개인정보 수집 및 이용</b><br>"
        "• <b>수집 항목:</b> 이름, 연락처(암호화 저장), 이용 횟수<br>"
        "• <b>이용 목적:</b> 회원 인증, 이용 한도 관리, 서비스 품질 개선<br>"
        "• <b>보유 기간:</b> 회원 탈퇴 후 즉시 파기 (법령 의무 보존 기간 제외) / 제3자 제공: 법령 외 금지<br><br>"

        "<b style='color:#0a1628;'>[제5조의2] 회원 개인정보 암호화 보호</b><br>"
        "• <b>연락처(비밀번호):</b> SHA-256 <b>단방향 해시(One-Way Hash)</b>로 저장 — <b>운영자·관리자 포함 누구도 원문 열람·복원 불가</b><br>"
        "• 로그인 시 입력값을 동일 방식으로 해시 변환 후 저장값과 비교하는 방식으로만 인증<br>"
        "• 세션 데이터: AES 기반 Fernet 암호화, 세션 종료 시 자동 파기 / 전송 구간: TLS(HTTPS) 암호화<br><br>"

        "<b style='color:#0a1628;'>[제6조] 고객정보 보안 기준</b><br>"
        "SHA-256 단방향 해시 / AES-128 Fernet / TLS 전송 암호화 / ISO/IEC 27001 준거 / GDPR·개인정보보호법 준거<br><br>"

        "<b style='color:#0a1628;'>[제6조의2] 마이크 접근 권한 정책</b><br>"
        "• 음성 입력(STT) 기능용 마이크 권한 요청 — 녹음 파일 서버 미저장<br>"
        "• 권한 거부 시에도 텍스트 입력으로 모든 기능 정상 이용 가능<br>"
        "• Web Speech API(Google 제공)를 통해 음성→텍스트 변환 (Google 서버 처리)<br><br>"

        "<b style='color:#0a1628;'>[제7조] 고객정보 폐기 지침</b><br>"
        "• 즉시 파기: 탈퇴 요청 시 DB 즉시 삭제 / 자동 파기: 세션 종료 시 상담 내용 초기화<br>"
        "• 정기 파기: 이용 로그 90일 경과 후 자동 삭제 / 전자적 파일 복구 불가능 방법으로 영구 삭제<br><br>"

        "<b style='color:#0a1628;'>[제8조] 면책 고지</b><br>"
        "본 서비스는 AI 기술을 활용한 상담 <b>보조</b> 도구이며, 모든 분석 결과의 최종 판단 및 법적 책임은 <b>사용자(상담원)</b>에게 있습니다.<br>"
        "보험금 지급 여부의 최종 결정은 보험사 심사 및 관련 법령에 따르며, 법률·세무·의료 판단은 반드시 해당 전문가와 확인하십시오.<br>"
        "본 서비스는 보험 모집·중개·알선 행위와 <b>무관한 순수 AI 분석 보조 도구</b>이며, 앱 운영자는 일체의 법적 책임을 지지 않습니다.<br><br>"

        "<b style='color:#0a1628;'>[제8조의2] 회원정보 변경 및 책임</b><br>"
        "회원은 이름·연락처(비번)를 셀프 변경 기능으로 직접 변경할 수 있습니다. 회원이 직접 변경한 정보의 오류로 인한 결과는 회원 본인에게 귀속됩니다.<br>"
        "단, 시스템 오류·서버 장애로 인한 손해는 운영자가 책임집니다. 변경 불가 시: insusite@gmail.com / 010-3074-2616<br><br>"

        "<b style='color:#0a1628;'>[제9조] 금융소비자보호법(금소법) 준수 원칙</b><br>"
        "① 적합성 원칙(제17조): 고객 연령·소득·위험성향 기반 분석 / ② 적정성 원칙(제18조): 부적합 상품 경고 설계<br>"
        "③ 설명 의무(제19조): 보장범위·면책·위험요소 포함 / ④ 불공정영업 금지(제20조): 특정 보험사 제휴·수수료 없음<br>"
        "⑤ 부당권유 금지(제21조): 단정적 표현 자동 감지·치환 / ⑥ 허위·과장 광고 금지(제22조): 공인 통계·약관·판례 근거 분석<br>"
        "<b>본 서비스는 보험 모집·중개·알선 행위와 무관한 AI 분석 보조 도구입니다.</b><br><br>"

        "<b style='color:#0a1628;'>[제10조] 데이터 저장 분리 및 개인정보 주권 보호 (하이브리드 아키텍처)</b><br>"
        "• Public Zone: 공용 보험사 카탈로그·의학 논문·법령 데이터 (중앙 공용 서버)<br>"
        "• Private Zone: 회원 업로드 고객 의무기록·증권 분석 등 민감 정보 → 회원 UID 귀속 독립 보안 저장소<br>"
        "• 운영진·관리자는 기술적으로 Private Zone 접근 불가 (IAM 403 차단) / AES-256-GCM 암호화 저장<br>"
        "• 탈퇴 시 모든 파일·메타데이터·계정정보 즉시 완전 삭제(복구 불가)<br><br>"

        "<b style='color:#0a1628;'>[제11조] 준거법 및 관할</b><br>"
        "본 약관은 대한민국 법률에 따라 해석되며, 분쟁 발생 시 운영자 소재지 관할 법원을 전속 관할로 합니다.<br><br>"

        "<b style='color:#0a1628;'>[제12조] 내보험다보여 서비스 연계 이용</b><br>"
        "본 서비스는 금융감독원 <b>내보험다보여(www.insure.or.kr)</b> 조회 결과를 상담 보조 자료로 활용할 수 있습니다.<br>"
        "본 앱은 금융감독원과 제휴·위탁 관계가 없는 독립 보조 도구입니다.<br><br>"

        "<b style='color:#0a1628;'>[제13조] 카카오톡 메시지 발송 서비스 보안 및 권한 안내</b><br>"
        "• <b>서비스명:</b> 골드키 마스터 AI 리포트 전송 시스템<br>"
        "• <b>① 보안 확약:</b> 본 시스템은 마스터의 <b>대화 내용을 열람하거나 친구 목록을 수집하지 않습니다.</b> "
        "요청 권한은 <code>talk_message</code>(메시지 발송) 단 1개입니다.<br>"
        "• <b>② 데이터 처리:</b> 전송 데이터는 <b>TLS 암호화</b>되어 전송되며, 발송 즉시 <b>휘발성으로 관리</b>됩니다. "
        "서버에 리포트 내용이 저장되지 않습니다.<br>"
        "• <b>③ 권한 철회:</b> 카카오톡 앱 → <b>설정 → 자산 → 서비스 관리</b>에서 언제든지 권한을 철회하실 수 있습니다.<br><br>"

        "<b style='color:#0a1628;'>[제14조] 🔒 보안 기준 준수 (Security Standards)</b><br>"
        "• ISO/IEC 27001 정보보안 관리체계 인증 기준 준용<br>"
        "• GDPR 및 국내 개인정보보호법 가이드라인 철저 준거<br>"
        "• TLS 1.3 차세대 전송 암호화 적용 (서버-클라이언트 통신 보호)<br>"
        "• AES-256 Fernet 기반의 고강도 세션 데이터 암호화<br>"
        "• SHA-256 단방향 해시를 통한 연락처 및 비밀번호 암호화 저장<br>"
        "• 로그아웃 시 단말기 내 민감 정보 메모리 점유 즉시 해제 (임시 데이터 잔류 방지)<br><br>"

        "<b style='color:#0a1628;'>[제15조] 외부 캘린더 정보의 연동 및 활용</b><br>"
        "본 서비스는 회원의 편의를 위해 회원의 <b>명시적 동의</b>하에 외부 캘린더(Google, Apple 등)의 "
        "일정 정보를 <b>API(OAuth 2.0)</b> 방식을 통해 연동합니다. "
        "사용자가 <b>'🔄 외부 캘린더 일정 동기화' 버튼을 클릭할 때만</b> 정보가 갱신되며, "
        "자동 수집·스크래핑은 절대 수행하지 않습니다. 연동은 언제든 [⚙️ 연동/설정] 탭에서 해제할 수 있습니다.<br><br>"

        "<b style='color:#0a1628;'>[제16조] 절대적 데이터 폐쇄성 및 관리자 접근 제한 원칙 (Admin-Blind RLS)</b><br>"
        "본 서비스는 회원의 고객 DB 및 스케줄 정보에 <b>Zero-Knowledge에 준하는 "
        "RLS(Row Level Security) 아키텍처</b>를 적용합니다. "
        "회원의 데이터는 본인에게만 독점적으로 종속되며, "
        "당사의 시스템 관리자 및 개발자를 포함한 제3자는 이를 "
        "<b>절대 열람, 추출, 공유할 수 없습니다.</b> "
        "(Supabase RLS: auth.uid()::text = agent_id 정책 적용)<br><br>"

        "<b style='color:#0a1628;'>[제17조] 외부 캘린더 동기화 시 책임의 한계</b><br>"
        "회원이 외부 캘린더(Google, Apple 등)와 데이터를 동기화할 경우, "
        "전송된 데이터의 보안은 <b>해당 플랫폼의 개인정보 처리방침 및 보안 정책</b>을 따르며, "
        "당사는 플랫폼 측의 귀책으로 발생한 정보 유출, 서비스 중단, 데이터 손실에 대해 "
        "<b>법적 책임을 부담하지 않습니다.</b> "
        "동기화 전 해당 플랫폼의 약관을 반드시 확인하십시오.<br><br>"

        "<div style='background:#FFF3CD;border:1px solid #F0A500;border-radius:6px;padding:8px 10px;"
        "font-size:0.75rem;color:#7A4F00;margin-top:4px;'>"
        "<b>⚠️ 면책 및 서비스 이용 안내 (Disclaimer)</b><br>"
        "① 본 앱(Goldkey_AI_Master2026)은 고객 상담 보조 업무 도구입니다. 모든 AI 분석 결과는 참고용 보조 지표이며, 법적 효력 및 보험 계약·청구·설계 행위가 아닙니다.<br>"
        "② 보장 내용·약관 해석·보험금 청구는 반드시 해당 보험회사 보상담당자 또는 손해사정인에게 확인하십시오.<br>"
        "③ AI 분석 결과는 오답(AI 할루시네이션) 발생 가능성이 있으며, 이로 인한 손해에 대해 당사는 법적 책임을 지지 않습니다.<br>"
        "④ 본 앱은 의료·법률·세무·회계·부동산 등 전문적 진단·상담을 대체할 수 없습니다. 최종 판단과 책임은 이용자 본인에게 있습니다.<br>"
        "<i>최종 개정일: 2026년 3월 31일</i>"
        "</div>"

        "<div style='margin-top:8px;padding:6px 10px;font-size:0.74rem;color:#374151;"
        "border-top:1px dashed #cbd5e1;'>"
        "<b style='color:#0a1628;'>■ 서비스명:</b> Goldkey AI Master Lab. Beta &nbsp;|&nbsp; "
        "<b style='color:#0a1628;'>운영자:</b> 이세윤 &nbsp;|&nbsp; "
        "<b style='color:#0a1628;'>문의:</b> 010-3074-2616 / insusite@gmail.com"
        "</div>"
        "<div style='margin-top:8px;padding:7px 12px;background:#fff3cd;"
        "border:1px solid #f0a500;border-radius:6px;font-size:0.78rem;"
        "font-weight:700;color:#7a4f00;text-align:center;'>"
        "⚠️ 필수 동의 항목(3가지)에 모두 체크하셔야 로그인/가입 버튼이 활성화됩니다."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    if not show_checkboxes:
        return False
    # ── [이용 필수동의 4가지 박스] ─────────────────────────────────────────
    st.markdown("""<style>
/* 필수동의 박스 — 체크박스 영역 border 스타일링 */
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stCheckbox"]) {
    background: #f0f8ff;
    border-left: 1.5px solid #93c5fd;
    border-right: 1.5px solid #93c5fd;
    border-bottom: 1.5px solid #93c5fd;
    border-radius: 0 0 8px 8px;
    padding: 4px 10px 8px 10px;
    margin-bottom: 6px;
}
</style>""", unsafe_allow_html=True)
    _consent_header_text = consent_header_text or "📋 이용 필수동의 확인 (아래 항목을 읽고 동의해 주세요)"
    st.markdown(
        f"<div style='background:{consent_header_bg};border-radius:8px 8px 0 0;"
        "padding:7px 14px;margin-top:10px;text-align:center;'>"
        f"<span style='font-size:0.85rem;font-weight:900;color:{consent_header_fg};'>"
        f"{_consent_header_text}</span></div>",
        unsafe_allow_html=True,
    )
    # 전체동의 → 개별 항목 자동 체크
    _all_key = f"{terms_agree_key}_all"

    def _on_all_consent_change(_k=terms_agree_key, _ak=_all_key):
        _v = st.session_state.get(_ak, False)
        for _ck in ("_c1", "_c2", "_c3", "_c4", "_c5", "_c6"):
            st.session_state[f"{_k}{_ck}"] = _v
        st.session_state["voice_consent_agreed"] = _v

    if st.session_state.get(_all_key, False):
        st.session_state[f"{terms_agree_key}_c1"] = True
        st.session_state[f"{terms_agree_key}_c2"] = True
        st.session_state[f"{terms_agree_key}_c3"] = True
        st.session_state[f"{terms_agree_key}_c4"] = True
        st.session_state[f"{terms_agree_key}_c5"] = True
        st.session_state[f"{terms_agree_key}_c6"] = True
        st.session_state["voice_consent_agreed"]   = True
    st.checkbox(
        "🔲 **전체 동의** (필수·선택·내보험다보여·AI음성 항목 모두 동의)",
        key=_all_key,
        on_change=_on_all_consent_change,
    )
    _c1 = st.checkbox(
        "✅ **[필수]** 서비스 이용약관에 동의합니다 (제1조~제11조)",
        key=f"{terms_agree_key}_c1",
    )
    _c2 = st.checkbox(
        "✅ **[필수]** 개인정보 수집·이용에 동의합니다 (개인정보보호법 제15조)",
        key=f"{terms_agree_key}_c2",
    )
    _c3 = st.checkbox(
        "✅ **[필수]** 개인정보 암호화·보관·파기 정책에 동의합니다 (제5조의2·제7조)",
        key=f"{terms_agree_key}_c3",
    )
    _c4 = st.checkbox(
        "☑️ **[선택]** 마케팅·서비스 개선 목적 정보 활용에 동의합니다",
        key=f"{terms_agree_key}_c4",
    )
    # ── [ID-100-AUTH] 내보험다보여 연동 동의 입구 제어 카드 ──────────────────
    if show_nibo_box:
        st.markdown(
            "<div style='background:#fffbeb;border:2px dashed #f59e0b;"
            "border-radius:10px;padding:12px 14px;margin-top:14px;'>"
            "<div style='font-size:0.82rem;font-weight:900;color:#92400e;margin-bottom:8px;'>"
            "🔐 [내보험다보여 연동 동의] — 신용정보법 제32조 별도 고지</div>"
            "<div style='font-size:0.75rem;color:#78350f;line-height:1.85;'>"
            "• <b>수집:</b> 보험사명·상품명·담보내역·계약상태 (신용정보원 등록 데이터)<br>"
            "• <b>목적:</b> AI 트리니티 엔진 — 보장 적정성 분석 및 실질 생계비 기반 리모델링<br>"
            "• <b>보유:</b> 분석 완료 후 30일 경과 시 자동 파기 (리포트 이력 최대 3년 암호화)<br>"
            "• <b>인증정보:</b> 데이터 추출 후 <b>즉시 메모리 파기</b> — 서버 저장 절대 불가<br>"
            "• <b>미동의 시:</b> AI 증권분석 · 트리니티 리포트 기능 비활성화 (나머지 기능 정상 이용)"
            "</div></div>",
            unsafe_allow_html=True,
        )
        with st.popover("📋 내보험다보여 신용정보의 이용및 보호에 관한 법률 제32조 안내문.", use_container_width=True):
            st.markdown(
                "<div style='font-size:0.78rem;color:#92400e;font-weight:700;"
                "margin-bottom:6px;'>📌 신용정보의 이용 및 보호에 관한 법률 제32조 적용</div>",
                unsafe_allow_html=True,
            )
            st.markdown(_NIBO_CONSENT_HTML, unsafe_allow_html=True)
    _c5 = st.checkbox(
        "✅ **[내보험다보여 필수]** 신용정보원 '내보험다보여' 연동 및 신용정보 조회·분석에 동의합니다 (신용정보법 제32조)",
        key=f"{terms_agree_key}_c5",
        help="AI 증권분석·트리니티 리포트 기능 사용 시 필수. 미동의 시 해당 기능이 비활성화됩니다.",
    )
    # ── [GP-VOICE] AI 음성 브리핑 동의 (선택) ──────────────────────────────────
    st.markdown(
        "<div style='background:#f0fdf4;border:1px dashed #86efac;border-radius:8px;"
        "padding:6px 12px;margin-top:10px;margin-bottom:4px;font-size:0.76rem;color:#14532d;'>"
        "🔊 <b>AI 음성 브리핑 안내:</b> 설계사님의 스케줄 및 고객 분석 결과를 AI 아나운서의 "
        "음성으로 자동 브리핑받는 기능입니다. <b>(마이크 수집 없음, 스피커 출력 전용)</b>"
        "</div>",
        unsafe_allow_html=True,
    )
    _c6 = st.checkbox(
        "🔊 **[선택]** AI 음성 브리핑 및 오디오 자동 재생 동의",
        key=f"{terms_agree_key}_c6",
        help="설계사님의 스케줄 및 고객 분석 결과를 AI 아나운서의 음성으로 자동 브리핑받는 기능입니다. (마이크 수집 없음, 스피커 출력 전용)",
    )
    st.session_state["voice_consent_agreed"] = _c6
    # ── [GP-CAL §15] 외부 캘린더 연동 동의 (선택) ──────────────────────────────
    st.markdown(
        "<div style='background:#f0fdf4;border:1px dashed #86efac;border-radius:8px;"
        "padding:6px 12px;margin-top:10px;margin-bottom:4px;font-size:0.76rem;color:#14532d;'>"
        "📅 <b>외부 캘린더 연동 안내:</b> Google·Apple 캘린더의 일정을 "
        "<b>사용자가 직접 클릭할 때만</b> 동기화합니다. "
        "자동 수집 없음 / OAuth 2.0 표준 / 언제든 연동 해제 가능 "
        "<b>(제15조·제17조 적용)</b>"
        "</div>",
        unsafe_allow_html=True,
    )
    _c7 = st.checkbox(
        "📅 **[선택]** 외부 캘린더(Google/Apple) 연동 및 일정 동기화 동의 (제15조·제17조)",
        key=f"{terms_agree_key}_c7",
        help="Google·Apple 캘린더를 OAuth 2.0으로 연동하여 일정을 수동으로 동기화하는 기능입니다. 동의 시에만 [⚙️ 연동/설정] 탭의 캘린더 연동 버튼이 활성화됩니다.",
    )
    st.session_state["cal_sync_consent_agreed"] = _c7
    # 내보험다보여 동의 여부를 독립 세션키로도 저장 (feature gate용)
    st.session_state["nibo_consent_agreed"]    = _c5
    st.session_state["nibo_consent_version"]   = _NIBO_CONSENT_VERSION if _c5 else ""
    st.session_state["nibo_consent_timestamp"] = (
        __import__("datetime").datetime.now().isoformat() if _c5 else ""
    )
    agreed = _c1 and _c2 and _c3
    st.session_state[terms_agree_key] = agreed
    return agreed


# ── [GP-SEC §2] SSO 핸드오프 빌더 ─────────────────────────────────────────────
def build_sso_handoff_to_hq(
    user_id: str,
    auth_token: str,
    cid: str = "",
    sector: str = "home",
) -> str:
    """
    [GP-SEC §2] CRM → HQ 앱 SSO 핸드오프 URL 생성.
    - URL에 PII(전화번호 등 원문) 절대 포함 금지
    - auth_token(HMAC-SHA256 32자 hex) + user_id + cid(암호화된 ID) 만 전달
    """
    import urllib.parse as _up
    params: dict = {"auth_token": auth_token, "user_id": user_id}
    if cid:
        params["gk_cid"] = cid
    if sector and sector != "home":
        params["gk_sector"] = sector
    return f"{HQ_APP_URL}/?{_up.urlencode(params)}"


def verify_sso_token(token: str, user_id: str, user_name: str = "") -> bool:
    """
    [GP-SEC §2] HQ 앱에서 SSO 토큰 검증.
    HMAC-SHA256(secret, user_id + user_name)[:32] 과 비교.
    """
    import hmac as _hmac
    try:
        secret = get_env_secret("ENCRYPTION_KEY", "")
        if not secret:
            # [GP-SEC §6] ENCRYPTION_KEY 미설정 — 운영 환경에서는 반드시 환경변수 설정 필요
            import os as _os
            if _os.environ.get("K_SERVICE"):
                # Cloud Run 운영 환경에서 키 미설정은 보안 위반
                return False
            secret = "gk_token_secret_2026"  # 로컬 개발 전용 폴백
        if isinstance(secret, bytes):
            secret = secret.decode()
        expected = _hmac.new(
            secret.encode(),
            (user_id + user_name).encode(),
            "sha256",
        ).hexdigest()[:32]
        return _hmac.compare_digest(token, expected)
    except Exception:
        return False


# ── [GP-SEC §1] PII 암호화 헬퍼 ────────────────────────────────────────────────
def encrypt_pii(plaintext: str) -> str:
    """
    [GP-SEC §1] 복호화가 필요한 PII(고객 연락처 등) Fernet 양방향 암호화.
    암호화 키: FERNET_KEY 환경변수 (없으면 ENCRYPTION_KEY 기반 파생).
    """
    try:
        from cryptography.fernet import Fernet
        import base64, hashlib
        raw_key = get_env_secret("FERNET_KEY", "")
        if not raw_key:
            seed = get_env_secret("ENCRYPTION_KEY", "gk_token_secret_2026")
            raw_key = base64.urlsafe_b64encode(
                hashlib.sha256(seed.encode()).digest()
            ).decode()
        f = Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
        return f.encrypt(plaintext.encode()).decode()
    except Exception:
        return plaintext


def decrypt_pii(ciphertext: str) -> str:
    """
    [GP-SEC §1] Fernet 복호화. 실패 시 원문 반환(이미 평문인 경우 대비).
    """
    try:
        from cryptography.fernet import Fernet
        import base64, hashlib
        raw_key = get_env_secret("FERNET_KEY", "")
        if not raw_key:
            seed = get_env_secret("ENCRYPTION_KEY", "gk_token_secret_2026")
            raw_key = base64.urlsafe_b64encode(
                hashlib.sha256(seed.encode()).digest()
            ).decode()
        f = Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext


# ── [GP-SEC §4] Storage 태깅 업로드 ────────────────────────────────────────────
def upload_file_with_tag(
    file_bytes: bytes,
    filename: str,
    agent_id: str,
    person_id: str,
    bucket_name: str = "",
    supabase_client=None,
) -> str:
    """
    [GP-SEC §4] Supabase Storage에 파일 업로드.
    경로 규칙: {agent_id}/{person_id}/{filename}
    반드시 agent_id + person_id 태깅 — 연결 고리 영구 보존.

    Returns:
        업로드된 파일의 public URL (또는 storage path)
    Raises:
        RuntimeError: 업로드 실패
    """
    if not agent_id:
        raise ValueError("agent_id 필수 — Storage 태깅 규칙 위반 방지")
    if not person_id:
        raise ValueError("person_id 필수 — Storage 태깅 규칙 위반 방지")

    storage_path = f"{agent_id}/{person_id}/{filename}"
    bucket = bucket_name or get_env_secret("STORAGE_BUCKET", "gk-files")

    if supabase_client is None:
        try:
            from supabase import create_client
            sb_url = get_env_secret("SUPABASE_URL", "")
            sb_key = get_env_secret("SUPABASE_SERVICE_ROLE_KEY",
                        get_env_secret("SUPABASE_KEY", ""))
            supabase_client = create_client(sb_url, sb_key)
        except Exception as e:
            raise RuntimeError(f"Supabase 연결 실패: {e}")

    try:
        res = supabase_client.storage.from_(bucket).upload(
            storage_path, file_bytes, {"upsert": "true"}
        )
        return storage_path
    except Exception as e:
        raise RuntimeError(f"Storage 업로드 실패 ({storage_path}): {e}")


# ===========================================================================
# [GP-ALERT §1·§2] 회원 인증 오류 알람 + 관리자 긴급 신고 프로토콜
# HQ/CRM 양쪽 앱 공통 — 동일 함수, 동일 운용 프로토콜
# ===========================================================================

def notify_admin_member_error(
    member_name: str,
    error_type: str = "AUTH_MISMATCH",
    app_name: str = "HQ",
    extra_note: str = "",
) -> dict:
    """
    [GP-ALERT §1] 회원 인증 오류 발생 시:
      1) Supabase member_errors 테이블에 오류 기록 (status='pending')
      2) 관리자에게 카카오톡 알림톡 / SMS 즉시 발송
    error_type: "AUTH_MISMATCH" | "LOGIN_BLOCKED" | "MANUAL_REPORT"
    Returns: {"success": bool, "error_id": str, "sb_saved": bool, "notified": bool, "msg": str}
    """
    import datetime as _dt, hashlib as _hl
    now_str  = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_id = _hl.md5(f"{member_name}{now_str}".encode()).hexdigest()[:12].upper()
    _app_label = {"HQ": "HQ(정밀분석)", "CRM": "CRM(모바일)"}
    _type_labels = {
        "AUTH_MISMATCH": "연락처/비밀번호 불일치 (DB·GCS 매칭 오류)",
        "LOGIN_BLOCKED": "로그인 잠금 횟수 초과",
        "MANUAL_REPORT": "회원 직접 신고",
    }
    _label = _type_labels.get(error_type, error_type)

    # ── 1) Supabase member_errors 기록 ──────────────────────────────────────
    _sb_ok = False
    try:
        from supabase import create_client as _sc_sb
        _sb_url = get_env_secret("SUPABASE_URL", "")
        _sb_key = get_env_secret("SUPABASE_SERVICE_ROLE_KEY",
                      get_env_secret("SUPABASE_KEY", ""))
        if _sb_url and _sb_key:
            _sb2 = _sc_sb(_sb_url, _sb_key)
            _sb2.table("member_errors").upsert({
                "error_id":    error_id,
                "member_name": member_name,
                "error_type":  error_type,
                "app_name":    app_name,
                "status":      "pending",
                "created_at":  _dt.datetime.now().isoformat(),
                "note":        extra_note or "",
            }, on_conflict="error_id").execute()
            _sb_ok = True
    except Exception:
        pass

    # ── 2) 관리자 카카오/SMS 알림 ────────────────────────────────────────────
    _admin_phone = get_env_secret("ADMIN_NOTIFY_PHONE", "")
    if not _admin_phone:
        try:
            import streamlit as _st2
            _admin_phone = _st2.session_state.get("gp200_master_phone", "")
        except Exception:
            pass

    _send_ok  = False
    _send_msg = "관리자 연락처(ADMIN_NOTIFY_PHONE) 미설정"
    if _admin_phone:
        try:
            from modules.kakao_service import send_report, MSG_TYPE_NOTICE
            _alert_text = (
                f"[회원 오류 알람] #{error_id}\n\n"
                f"앱: {_app_label.get(app_name, app_name)}\n"
                f"회원명: {member_name}\n"
                f"오류유형: {_label}\n"
                f"발생시각: {now_str}\n"
            )
            if extra_note:
                _alert_text += f"메모: {extra_note}\n"
            _alert_text += "\n→ 관리자 시스템 설정 > '회원정보 오류 관리' 탭에서 초기화하세요."
            _res = send_report(
                _admin_phone, _alert_text,
                msg_type=MSG_TYPE_NOTICE,
                client_name="관리자",
                title=f"[긴급] 회원 인증 오류 — {member_name}",
            )
            _send_ok  = _res.get("success", False)
            _send_msg = _res.get("msg", "")
        except Exception as _e:
            _send_msg = str(_e)

    return {
        "success":  True,
        "error_id": error_id,
        "sb_saved": _sb_ok,
        "notified": _send_ok,
        "msg":      _send_msg,
    }


def render_member_emergency_btn(
    app_name: str = "HQ",
    key_prefix: str = "emergency",
    show_admin_login: bool = False,
) -> None:
    """
    [GP-ALERT §2] 로그인 화면 — '관리자 오류 신고' 긴급 버튼.
    회원이 진입 불가 시 클릭 → 이름 입력 → 관리자에게 즉시 신고.
    HQ/CRM 양쪽 앱 동일 함수로 공유.
    show_admin_login=True 시 '관리자 신고' 좌측에 '관리자 로그인' 버튼 추가.
    """
    try:
        import streamlit as _st3
    except ImportError:
        return

    _show_key = f"{key_prefix}_show_form"
    _done_key = f"{key_prefix}_sent_done"
    _adm_key  = f"{key_prefix}_show_admin"

    if _st3.session_state.get(_done_key):
        _st3.success("✅ 관리자에게 신고 완료. 확인 후 조치합니다.", icon="📞")
        if _st3.button("↩️ 다시 로그인 시도", key=f"{key_prefix}_retry"):
            _st3.session_state.pop(_done_key, None)
            _st3.session_state.pop(_show_key, None)
            _st3.rerun()
        return

    _st3.markdown(
        "<div style='border:1px dashed #DC2626;border-radius:8px;"
        "padding:6px 10px;margin-top:6px;background:#FEF2F2;'>",
        unsafe_allow_html=True,
    )

    if show_admin_login:
        _ec1, _ec2, _ec3 = _st3.columns([4, 3, 3])
        with _ec1:
            _st3.markdown(
                "<span style='font-size:0.78rem;color:#DC2626;font-weight:700;'>"
                "🆘 로그인 오류가 계속되시나요?</span>",
                unsafe_allow_html=True,
            )
        with _ec2:
            if _st3.button("🔐 관리자 로그인", key=f"{key_prefix}_admin_toggle",
                           use_container_width=True):
                _st3.session_state[_adm_key]  = not _st3.session_state.get(_adm_key, False)
                _st3.session_state[_show_key] = False
        with _ec3:
            if _st3.button("🆘 관리자 신고", key=f"{key_prefix}_toggle",
                           use_container_width=True):
                _st3.session_state[_show_key] = not _st3.session_state.get(_show_key, False)
                _st3.session_state[_adm_key]  = False
    else:
        _ec1, _ec2 = _st3.columns([6, 4])
        with _ec1:
            _st3.markdown(
                "<span style='font-size:0.78rem;color:#DC2626;font-weight:700;'>"
                "🆘 로그인 오류가 계속되시나요?</span>",
                unsafe_allow_html=True,
            )
        with _ec2:
            if _st3.button("🆘 관리자 신고", key=f"{key_prefix}_toggle",
                           use_container_width=True):
                _st3.session_state[_show_key] = not _st3.session_state.get(_show_key, False)

    # ── 관리자 로그인 인라인 폼 ───────────────────────────────────────────────
    if show_admin_login and _st3.session_state.get(_adm_key):
        _st3.markdown(
            "<div style='background:#EFF6FF;border:1px solid #BFDBFE;"
            "border-radius:8px;padding:10px 12px;margin-top:8px;'>",
            unsafe_allow_html=True,
        )
        _st3.markdown(
            "<span style='font-size:0.80rem;font-weight:800;color:#1e3a8a;'>"
            "🔐 관리자 로그인</span>",
            unsafe_allow_html=True,
        )
        with _st3.form(f"{key_prefix}_admin_form", clear_on_submit=False):
            _adm_id_in   = _st3.text_input(
                "관리자 ID", placeholder="admin 또는 이세윤",
                key=f"{key_prefix}_adm_id", label_visibility="collapsed",
            )
            _adm_code_in = _st3.text_input(
                "관리자 코드", type="password", placeholder="관리자 코드 입력",
                key=f"{key_prefix}_adm_code", label_visibility="collapsed",
            )
            _adm_sub = _st3.form_submit_button("🔐 로그인", use_container_width=True, type="primary")
        if _adm_sub:
            _aid = (_adm_id_in   or "").strip()
            _acd = (_adm_code_in or "").strip()
            _env_code   = get_env_secret("ADMIN_CODE", "")
            _master_env = get_env_secret("MASTER_CODE", "")
            import hashlib as _hl_emg
            _adm_default_hash = _hl_emg.sha256(b"kgagold6803").hexdigest()
            _adm_pw_hash      = get_env_secret("CRM_ADMIN_PW_HASH", _adm_default_hash)
            _adm_input_hash   = _hl_emg.sha256(_acd.encode()).hexdigest()
            if _aid.lower() in ("admin", "이세윤") and _acd == _env_code and _env_code:
                _st3.session_state["crm_is_admin"]      = True
                _st3.session_state["crm_authenticated"] = True
                _st3.session_state["crm_user_id"]       = "ADMIN_MASTER"
                _st3.session_state["crm_user_name"]     = "이세윤"
                _st3.session_state["crm_role"]          = "admin"
                _st3.rerun()
            elif _acd == _master_env and _master_env:
                _mname = get_env_secret("MASTER_NAME", "이세윤")
                _st3.session_state["crm_is_admin"]      = True
                _st3.session_state["crm_authenticated"] = True
                _st3.session_state["crm_user_id"]       = "PERMANENT_MASTER"
                _st3.session_state["crm_user_name"]     = _mname
                _st3.session_state["crm_role"]          = "admin"
                _st3.rerun()
            elif _aid.lower() in ("admin", "이세윤") and _adm_input_hash == _adm_pw_hash:
                _st3.session_state["crm_is_admin"]      = True
                _st3.session_state["crm_authenticated"] = True
                _st3.session_state["crm_user_id"]       = "ADMIN_MASTER"
                _st3.session_state["crm_user_name"]     = "이세윤"
                _st3.session_state["crm_role"]          = "admin"
                _st3.rerun()
            else:
                _st3.error("❌ ID 또는 코드가 올바르지 않습니다.")
        _st3.markdown("</div>", unsafe_allow_html=True)

    # ── 관리자 신고 폼 ────────────────────────────────────────────────────────
    if _st3.session_state.get(_show_key):
        _nm = _st3.text_input(
            "가입 시 이름 입력", key=f"{key_prefix}_report_name",
            placeholder="등록한 이름을 입력하세요",
            label_visibility="collapsed",
        )
        if _st3.button("📨 관리자에게 오류 신고 발송", key=f"{key_prefix}_send",
                       use_container_width=True, type="primary"):
            if not (_nm or "").strip() or len((_nm or "").strip()) < 2:
                _st3.warning("이름을 2자 이상 입력하세요.")
            else:
                with _st3.spinner("신고 중..."):
                    notify_admin_member_error(
                        member_name=_nm.strip(),
                        error_type="MANUAL_REPORT",
                        app_name=app_name,
                    )
                _st3.session_state[_done_key] = True
                _st3.rerun()
    _st3.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [GP-PHASE-4] 반응형 통합 증권분석 센터 (내보험다보여)
# HQ 앱(app.py) + CRM 앱(crm_app.py) 양쪽에서 동일 렌더링
# ══════════════════════════════════════════════════════════════════════════════
# ── [GP-L-SEC] 내보험다보여 동의 상수 (ImportError 방지) ─────────────────────
_NIBO_CONSENT_VERSION = "2026-03-16-v1"
_NIBO_CONSENT_HTML = """
<div style='font-size:0.82rem;color:#1e3a8a;line-height:1.85;'>
<b>[신용정보의 이용 및 보호에 관한 법률 제32조 안내문]</b><br><br>
본 서비스는 한국신용정보원 '내보험다보여' 시스템과 연동하여 고객님의 보험 가입 현황을 조회합니다.<br>
<b>1. 수집·이용 항목:</b> 보험사명, 상품명, 담보·특약 내역, 계약상태, 보험료<br>
<b>2. 수집·이용 목적:</b> AI 트리니티 엔진 기반 보장 적정성 및 실질 생계비 분석<br>
<b>3. 보유 및 이용 기간:</b> 분석 완료 후 30일 경과 시 자동 파기<br>
<b>4. 인증정보 처리:</b> 데이터 추출 후 즉시 메모리 파기 — 서버에 저장되지 않습니다.<br>
<b>5. 제3자 제공:</b> 본인 동의 없이 제3자에게 절대 제공하지 않습니다.<br>
<b>6. 책임 한계:</b> 신용정보원 데이터 기반으로 실제 증권과 차이가 있을 수 있습니다.<br><br>
위 사항에 동의하시면 아래 동의 버튼을 클릭해 주세요.
</div>
"""


def render_unified_analysis_center(
    *,
    key_prefix: str = "_uac",
    compact: bool = False,
) -> None:
    """반응형 통합 증권분석 센터 — 고객 대면용 AI 컨설팅 보드.
    좌우 5:5 레이아웃, 모바일 자동 스태킹.
    """
    st.markdown("""
<style>
@media(max-width:640px){
  div[data-testid="stHorizontalBlock"]>div[data-testid="stVerticalBlockBorderWrapper"],
  div[data-testid="stHorizontalBlock"]>div[data-testid="stVerticalBlock"]{
    width:100%!important;min-width:100%!important;flex:none!important;
  }
  .uac-gauge-label{font-size:0.65rem!important;}
}
.uac-header{background:linear-gradient(135deg,#059669 0%,#047857 100%);
  border-radius:12px;padding:14px 20px 12px;margin-bottom:14px;}
.uac-summary-card{background:linear-gradient(90deg,#f0fdf4,#ecfdf5);
  border:1.5px solid #6ee7b7;border-radius:10px;padding:10px 14px;
  margin-top:10px;font-size:0.82rem;}
.uac-alert-box{background:linear-gradient(90deg,#fffbeb,#fff7ed);
  border:2px solid #f59e0b;border-radius:10px;padding:12px 16px;margin-bottom:12px;}
.uac-prescription{background:#f8faff;border-left:4px solid #3b82f6;
  border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.80rem;line-height:1.75;}
.uac-gauge-label{font-size:0.72rem;font-weight:700;color:#374151;}
.uac-data-card{background:#fff;border:1px dashed #000;border-radius:12px;
  padding:14px 16px 6px;margin-bottom:10px;}
.uac-red-alert{border:1.5px solid #FF4B4B;background:rgba(255,75,75,0.05);
  border-radius:8px;padding:10px 14px;color:#FF4B4B;font-size:0.76rem;
  font-weight:600;margin:8px 0 10px;word-break:keep-all;line-height:1.65;}
button[data-testid="baseButton-primary"]{
  background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%)!important;
  color:white!important;border:none!important;border-radius:12px!important;
  box-shadow:0 6px 14px rgba(0,192,255,0.28)!important;
  font-weight:800!important;transition:transform .15s,box-shadow .15s!important;}
button[data-testid="baseButton-primary"]:hover{
  transform:translateY(-2px)!important;
  box-shadow:0 10px 20px rgba(0,192,255,0.4)!important;}
</style>""", unsafe_allow_html=True)

    st.markdown(
        '<div class="uac-header">'
        '<span style="font-size:1.05rem;font-weight:900;color:white;letter-spacing:0.04em;">'
        '📊 통합 증권분석 센터 (내보험다보여)</span>'
        '<span style="background:rgba(255,255,255,0.25);color:white;font-size:0.65rem;'
        'font-weight:700;padding:2px 8px;border-radius:4px;margin-left:12px;">'
        'AI 분석 엔진 가동중</span></div>',
        unsafe_allow_html=True,
    )

    _kj = f"{key_prefix}_json"
    _kr = f"{key_prefix}_result"
    _left, _right = st.columns([1, 1], gap="medium")

    # ── 좌측: 데이터 & 가치 입력 영역 ──────────────────────────────────────
    with _left:
        st.markdown(
            "<div style='font-size:0.78rem;font-weight:900;color:#065f46;"
            "margin-bottom:8px;'>👈 데이터 & 가치 입력 영역</div>",
            unsafe_allow_html=True,
        )
        _tab_nibo, _tab_scan = st.tabs(["🌐 내보험다보여 크롤링", "📄 증권 파일 스캔/업로드"])

        with _tab_nibo:
            if not st.session_state.get("nibo_consent_agreed", False):
                st.warning("🔐 신용정보 조회 동의 후 이용 가능합니다.")
                if st.checkbox("✅ 신용정보 조회·분석 동의 (신용정보법 제32조)",
                               key=f"{key_prefix}_consent"):
                    st.session_state["nibo_consent_agreed"]    = True
                    st.session_state["nibo_consent_version"]   = "2026-03-16-v1"
                    st.session_state["nibo_consent_timestamp"] = (
                        __import__("datetime").datetime.now().isoformat()
                    )
                    st.rerun()
            else:
                _kp = key_prefix
                _uac_tok = st.session_state.get(f"{_kp}_auth_token")

                # ── 데이터 수집 & 인증 카드 (인증 전) ──────────────────────────
                if not _uac_tok:
                    st.markdown("<div class='uac-data-card'>", unsafe_allow_html=True)
                    st.markdown(
                        "<div style='font-size:0.82rem;font-weight:900;color:#065f46;"
                        "margin-bottom:10px;'>🌐 내보험다보여 크롤링 연결 — 피보험자 인증</div>",
                        unsafe_allow_html=True,
                    )
                    _uac_name = st.text_input(
                        "👤 피보험자 성명 *",
                        placeholder="실명을 입력하세요",
                        value=st.session_state.get("gs_c_name", ""),
                        key=f"{_kp}_auth_name",
                        max_chars=30,
                    )
                    _dc1, _dc2 = st.columns([3, 2])
                    with _dc1:
                        _uac_dob = st.text_input(
                            "🎂 생년월일 * (YYYYMMDD)",
                            placeholder="예: 19901231",
                            key=f"{_kp}_auth_dob",
                            max_chars=8,
                        )
                    with _dc2:
                        _uac_carrier = st.selectbox(
                            "📶 통신사 *",
                            ["─ 선택 ─", "SKT", "KT", "LG U+",
                             "SKT 알뜰폰", "KT 알뜰폰", "LG 알뜰폰"],
                            key=f"{_kp}_auth_carrier",
                        )
                    _uac_phone = st.text_input(
                        "📱 휴대폰 번호 * (숫자만, - 없이)",
                        placeholder="01012345678",
                        key=f"{_kp}_auth_phone",
                        max_chars=11,
                    )
                    st.markdown(
                        "<div class='uac-red-alert'>"
                        "⚠️ 생년월일·연락처는 한국신용정보원 본인확인에만 사용되는 <b>1회성 소모 정보</b>입니다. "
                        "인증 즉시 SHA-256 해시로 변환되며, 원본 정보는 <b>서버에 일체 저장되지 않습니다.</b> "
                        "<span style='font-size:0.68rem;'>(개인정보보호법 제15조 · 신용정보법 제32조)</span>"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                    _uac_method = st.radio(
                        "🔑 인증 수단 선택",
                        ["카카오톡", "PASS", "NICE 본인확인", "간편인증(데모)"],
                        horizontal=True,
                        key=f"{_kp}_auth_method",
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                    _method_map = {
                        "카카오톡": "kakao", "PASS": "pass",
                        "NICE 본인확인": "nice", "간편인증(데모)": "simulate",
                    }
                    _dob_clean   = "".join(c for c in (_uac_dob   or "") if c.isdigit())
                    _phone_clean = "".join(c for c in (_uac_phone  or "") if c.isdigit())
                    _auth_ready  = (
                        bool((_uac_name or "").strip())
                        and len(_dob_clean) == 8
                        and _uac_carrier != "─ 선택 ─"
                        and len(_phone_clean) >= 10
                    )
                    if _auth_ready:
                        if st.button(
                            "🚀 트리니티 진단 시작 (인증 요청)",
                            key=f"{_kp}_auth_run",
                            type="primary",
                            use_container_width=True,
                        ):
                            import hashlib as _hl
                            import time as _agt
                            with st.spinner("🔐 인증 게이트웨이 처리 중..."):
                                try:
                                    from modules.auth_gateway import authenticate as _ag_auth
                                    _tok = _ag_auth(
                                        name=(_uac_name or "").strip(),
                                        phone=_uac_phone,
                                        dob=_dob_clean,
                                        carrier=_uac_carrier,
                                        method=_method_map.get(_uac_method, "simulate"),
                                    )
                                except Exception as _age:
                                    _nm = (_uac_name or "").strip()
                                    _tok = {
                                        "token":        _hl.sha256((_nm + _phone_clean).encode()).hexdigest()[:32],
                                        "ci_hash":      _hl.sha256((_dob_clean + _nm).encode()).hexdigest()[:24],
                                        "name_initial": _nm[0] + "*" * max(len(_nm) - 2, 0) + (_nm[-1] if len(_nm) > 1 else ""),
                                        "phone_masked": _phone_clean[:3] + "-****-" + _phone_clean[-4:],
                                        "method":       "simulate",
                                        "issued_at":    _agt.time(),
                                        "expires_at":   _agt.time() + 1800,
                                        "error":        str(_age)[:120],
                                    }
                            st.session_state[f"{_kp}_auth_token"] = {
                                "name_initial": _tok.get("name_initial", "*"),
                                "phone_masked": _tok.get("phone_masked", "***"),
                                "method":       _tok.get("method", "simulate"),
                                "issued_at":    _tok.get("issued_at", 0),
                            }
                            st.session_state["gs_c_name"] = (_uac_name or "").strip()
                            for _sk in [f"{_kp}_auth_dob", f"{_kp}_auth_phone"]:
                                st.session_state.pop(_sk, None)
                            if _tok.get("error"):
                                st.warning(f"⚠️ {_tok['error']} — 시뮬레이션 모드로 진행")
                            try:
                                from modules.mydata_connector import fetch_mydata_insurance as _fmi
                                import json as _mj
                                _mdata = _fmi((_uac_name or "").strip(), use_simulate=True)
                                st.session_state["_nibo_raw_json"] = _mj.dumps(
                                    _mdata.get("insurance_list", []),
                                    ensure_ascii=False, indent=2,
                                )
                                st.session_state[_kj] = st.session_state["_nibo_raw_json"]
                            except Exception:
                                pass
                            st.rerun()
                    else:
                        st.button(
                            "🚀 트리니티 진단 시작 (필수 정보 입력 후 활성화)",
                            key=f"{_kp}_auth_run_dis",
                            disabled=True,
                            use_container_width=True,
                        )
                        _miss = []
                        if not (_uac_name or "").strip(): _miss.append("성명")
                        if len(_dob_clean) != 8:          _miss.append("생년월일 8자리")
                        if _uac_carrier == "─ 선택 ─":    _miss.append("통신사")
                        if len(_phone_clean) < 10:        _miss.append("휴대폰")
                        if _miss:
                            st.caption(f"⚠️ 미입력: {' · '.join(_miss)}")
                else:
                    # ── 인증 완료 배너 + 재인증 ──────────────────────────────
                    _at = _uac_tok
                    _ml = {"kakao": "카카오톡", "pass": "PASS", "nice": "NICE",
                           "simulate": "간편인증(데모)"}.get(_at.get("method", "simulate"), "간편인증")
                    st.markdown(
                        f"<div style='background:#dcfce7;border:1px solid #86efac;"
                        f"border-radius:8px;padding:8px 14px;font-size:0.8rem;"
                        f"color:#166534;font-weight:700;margin-bottom:10px;'>"
                        f"✅ 인증 완료 &nbsp;|&nbsp; {_at.get('name_initial','*')} &nbsp;|&nbsp; "
                        f"{_at.get('phone_masked','***')} &nbsp;|&nbsp; {_ml}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button("🔄 재인증", key=f"{_kp}_reauth"):
                        st.session_state.pop(f"{_kp}_auth_token", None)
                        st.rerun()

                # ── JSON 입력창 (인증 완료 후 자동 채워짐) ─────────────────────
                _json_val = st.text_area(
                    "내보험다보여 JSON",
                    value=st.session_state.get(_kj, st.session_state.get("_nibo_raw_json", "")),
                    placeholder='[{"prodName":"삼성생명 종신","traitName":"암진단비","amt":"3000만원","status":"유효"}]',
                    height=110,
                    key=f"{key_prefix}_json_ta",
                    label_visibility="collapsed",
                )
                if _json_val != st.session_state.get(_kj, ""):
                    st.session_state[_kj] = _json_val
                    st.session_state["_nibo_raw_json"] = _json_val
                if st.button("📋 샘플 데이터 불러오기", key=f"{key_prefix}_sample",
                             use_container_width=True):
                    import json as _ujs
                    _s = _ujs.dumps([
                        {"prodName": "(무)뉴-하이콜 암진단비",   "traitName": "암진단비특약",    "amt": "3000만원",  "status": "유효"},
                        {"prodName": "뇌졸중진단확정비",          "traitName": "뇌졸중진단특약",  "amt": "10000000", "status": "유효"},
                        {"prodName": "급성심근경색진단비",         "traitName": "심근경색진단특약","amt": "2000만원",  "status": "유효"},
                        {"prodName": "일반상해후유장해(3~100%)", "traitName": "상해후유장해",    "amt": "5000만원",  "status": "유효"},
                        {"prodName": "DB손해 통합",               "traitName": "암진단비(소액암)","amt": "2000만원",  "status": "유효"},
                    ], ensure_ascii=False, indent=2)
                    st.session_state[_kj] = _s
                    st.session_state["_nibo_raw_json"] = _s
                    st.rerun()

        with _tab_scan:
            _uploaded = st.file_uploader(
                "증권 PDF 또는 이미지 업로드",
                type=["pdf", "jpg", "jpeg", "png"],
                key=f"{key_prefix}_file_up",
                help="보험증권 PDF/이미지를 업로드하면 AI가 담보를 자동 파싱합니다.",
                label_visibility="collapsed",
            )
            if _uploaded:
                st.success(f"✅ {_uploaded.name} 업로드 완료")
                if st.button("🔍 AI 파싱 시작", key=f"{key_prefix}_parse_btn",
                             type="primary", use_container_width=True):
                    st.info("📄 정밀 PDF 파싱은 A-SECTION '② 통합 스캔 허브'에서 이용 가능합니다.")

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:0.76rem;font-weight:800;color:#92400e;margin-bottom:4px;'>"
            "💰 월 건강보험료 납부액 "
            "<span style='font-weight:400;color:#6b7280;'>(가치 산출용)</span></div>",
            unsafe_allow_html=True,
        )
        _nhi = st.number_input(
            "월 건강보험료(원)",
            min_value=0, max_value=2_000_000,
            value=int(st.session_state.get("gs_hi_premium") or 0),
            step=10_000,
            key=f"{key_prefix}_nhi",
            help="직장인: 보수월액×7.19% | 추정 월소득 = 건보료×30",
            label_visibility="collapsed",
        )
        if _nhi != int(st.session_state.get("gs_hi_premium") or 0):
            st.session_state["gs_hi_premium"] = _nhi
        if _nhi > 0:
            st.caption(f"📊 추정 월소득 **{_nhi*30:,.0f}원** | 연소득 **{_nhi*360:,.0f}원**")

        _cname   = (st.session_state.get("scan_client_name")
                    or st.session_state.get("gp200_name") or "")
        _cbirth  = st.session_state.get("scan_client_birth", "")
        _cgender = st.session_state.get("scan_client_gender", "")
        _has_data = bool(st.session_state.get(_kj) or st.session_state.get("_nibo_raw_json"))
        if _cname or _has_data:
            _b = f"({_cbirth[:4]}년생, " if _cbirth else "("
            _g = _cgender + "성)" if _cgender else ")"
            st.markdown(
                f'<div class="uac-summary-card">'
                f'👤 <b>분석 대상:</b> [{_cname or "미입력"}] 님 {_b}{_g}<br>'
                f'<span style="font-size:0.70rem;color:#6b7280;">'
                f'{"✅ 데이터 준비 완료" if _has_data else "⏳ 데이터 입력 대기"}'
                f'</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        if st.button("⚡ AI 통합 분석 실행", key=f"{key_prefix}_run",
                     type="primary", use_container_width=True):
            _run_json = st.session_state.get(_kj) or st.session_state.get("_nibo_raw_json", "")
            _run_nhi  = float(st.session_state.get("gs_hi_premium") or 0)
            if not (_run_json or "").strip():
                st.warning("⬆️ 내보험다보여 JSON을 입력해 주세요.")
            elif _run_nhi <= 0:
                st.warning("💰 월 건강보험료를 입력해 주세요.")
            else:
                with st.spinner("🤖 AI 정밀 분석 중…"):
                    try:
                        import json as _j2
                        from trinity_engine import execute_integrated_analysis as _exec
                        _raw = _j2.loads(_run_json.strip())
                        if isinstance(_raw, dict):
                            _raw = [_raw]
                        _adata, _unm, _ok = _exec(
                            raw_external_data = _raw,
                            client_contact    = st.session_state.get("scan_client_contact", ""),
                            nhi_premium       = _run_nhi,
                            consultant_info   = {
                                "소속": st.session_state.get("gp200_company",
                                        st.session_state.get("_mp_company", "")),
                                "이름": st.session_state.get("gp200_name",
                                        st.session_state.get("_mp_name", "")),
                                "연락처": st.session_state.get("gp200_contact",
                                          st.session_state.get("_mp_phone", "")),
                            },
                            client_name     = _cname,
                            agent_id        = st.session_state.get("user_id", ""),
                            person_id       = st.session_state.get("selected_customer_id", ""),
                            kb7_score       = int(st.session_state.get("_sops_kb_score", 0) or 0),
                            consent_version = st.session_state.get("nibo_consent_version", ""),
                            source          = "UAC-통합분석센터",
                        )
                        st.session_state[_kr] = _adata
                        if _ok:
                            st.success("✅ 분석 완료! 우측에서 결과를 확인하세요.")
                        else:
                            st.warning("⚠️ 분석 완료 (DB 저장 실패 — 연결 확인)")
                        st.rerun()
                    except Exception as _ue:
                        st.error(f"❌ 분석 오류: {_ue}")

    # ── 우측: AI 가입결과 보고서 ────────────────────────────────────────────
    with _right:
        st.markdown(
            "<div style='font-size:0.78rem;font-weight:900;color:#1e3a8a;"
            "margin-bottom:8px;'>👉 AI 가입결과 보고서</div>",
            unsafe_allow_html=True,
        )
        _result = st.session_state.get(_kr)
        _nhi_r  = float(st.session_state.get("gs_hi_premium") or 0)

        if not _result:
            st.markdown(
                '<div style="background:#f8faff;border:1.5px dashed #93c5fd;'
                'border-radius:10px;padding:32px 20px;text-align:center;color:#6b7280;">'
                '🔍 좌측에서 보험 데이터를 입력하고<br>'
                '<b>⚡ AI 통합 분석 실행</b> 버튼을 눌러주세요.</div>',
                unsafe_allow_html=True,
            )
        else:
            _GAUGES = [
                ("암진단비", ["암진단", "암진"],      50_000_000),
                ("뇌졸중",   ["뇌졸중", "뇌경색"],    30_000_000),
                ("심근경색", ["심근경색", "급성심"],   20_000_000),
                ("수술비",   ["수술비", "수술"],       20_000_000),
                ("입원비",   ["입원비", "입원"],       10_000_000),
                ("후유장해", ["후유장해", "장해"],    100_000_000),
                ("질병사망", ["질병사망", "사망"],    100_000_000),
                ("실손의료", ["실손", "의료비"],        5_000_000),
                ("간병보험", ["간병"],                 50_000_000),
                ("치매보험", ["치매"],                 30_000_000),
            ]
            _cov: dict = {}
            for _gl, _kws, _ideal in _GAUGES:
                _amt = 0.0
                for _rk, _rv in (_result or {}).items():
                    if isinstance(_rv, dict):
                        if any(kw in str(_rk).lower() for kw in _kws):
                            try:
                                _amt = float(_rv.get("현재가입", 0) or 0)
                            except Exception:
                                _amt = 0.0
                            break
                _cov[_gl] = _amt

            _total_cov  = sum(_cov.values())
            _est_annual = _nhi_r * 360 if _nhi_r > 0 else 40_000_000
            _gap        = max(0.0, _est_annual * 10 - _total_cov)
            _gap_disp   = (f"{_gap/100_000_000:.1f}억 원"
                           if _gap >= 100_000_000 else f"{_gap/10_000:.0f}만 원")
            _sev = "🔴" if _gap > 50_000_000 else ("🟡" if _gap > 10_000_000 else "🟢")

            st.markdown(
                f'<div class="uac-alert-box">'
                f'<div style="font-size:0.80rem;font-weight:900;color:#92400e;margin-bottom:4px;">'
                f'{_sev} AI 분석 총평</div>'
                f'<div style="font-size:0.96rem;font-weight:800;color:#1c1917;line-height:1.5;">'
                f'현재 <b style="color:#dc2626;">{_gap_disp}</b>의 소득 공백 위험이 존재합니다</div>'
                f'<div style="font-size:0.70rem;color:#78350f;margin-top:4px;">'
                f'추정 연소득 {_est_annual/10_000:.0f}만원 기준 · 10년치 보장 갭 분석</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                "<div style='font-size:0.72rem;font-weight:800;color:#374151;"
                "margin-bottom:6px;'>🔰 10대 핵심 담보 적정도 게이지</div>",
                unsafe_allow_html=True,
            )
            _gc1, _gc2 = st.columns(2, gap="small")
            for _gi, (_gl, _kws, _ideal) in enumerate(_GAUGES):
                with (_gc1 if _gi % 2 == 0 else _gc2):
                    _v   = _cov.get(_gl, 0)
                    _pct = min(100, int(_v / _ideal * 100)) if _ideal > 0 else 0
                    _clr = "#16a34a" if _pct >= 80 else ("#f59e0b" if _pct >= 40 else "#dc2626")
                    _sts = "적정" if _pct >= 80 else ("보통" if _pct >= 40 else "취약")
                    st.markdown(
                        f'<div class="uac-gauge-label" style="margin-bottom:1px;">'
                        f'{_gl} <span style="float:right;color:{_clr};font-size:0.65rem;">{_sts}</span></div>',
                        unsafe_allow_html=True,
                    )
                    st.progress(_pct / 100)

            if _nhi_r > 0 and _total_cov > 0:
                _survive = int(_total_cov / (_nhi_r * 30)) if _nhi_r > 0 else 0
                st.metric(
                    label="⏱️ 현재 보험으로 버틸 수 있는 시간",
                    value=f"{_survive}개월",
                    delta="충분" if _survive >= 36 else "보강 필요",
                    delta_color="normal" if _survive >= 36 else "inverse",
                )

            _weak = [
                f"• {_gl} {_ideal//10_000:,}만원 보강 필요"
                for _gl, _kws, _ideal in _GAUGES
                if _cov.get(_gl, 0) < _ideal * 0.5
            ][:4]
            if _weak:
                st.markdown(
                    '<div class="uac-prescription"><b>📋 AI 맞춤형 처방전</b><br>'
                    + "<br>".join(_weak) + "</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button(
        "� 내보험다보여 실행버튼",
        key=f"{key_prefix}_deepdive",
        use_container_width=True,
    ):
        if "current_tab" in st.session_state:
            st.session_state["current_tab"] = "gk_sec10"
            st.session_state["_scroll_top"] = True
            st.rerun()
        else:
            _hq_url = get_env_secret("HQ_APP_URL", HQ_APP_URL)
            st.markdown(
                f'<a href="{_hq_url}/?tab=gk_sec10" target="_blank">'
                '🔗 통합 증권분석 센터(GK-SEC-10) 열기</a>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# [GP-SEC §14] 보안 기준 준수 사이드바 — HQ·CRM 공통 모듈
# ══════════════════════════════════════════════════════════════════════════════
def render_security_sidebar() -> None:
    """
    [GP-SEC §14] 사이드바 최하단 보안 기준 준수 박스.
    HQ(app.py) · CRM(crm_app.py) 양쪽에서 동일하게 호출.
    """
    try:
        import streamlit as _st_sec
    except ImportError:
        return
    _st_sec.sidebar.markdown(
        "<div style='background:#eff6ff;padding:12px;border-radius:10px;"
        "font-size:0.77rem;border:1px dashed #3b82f6;margin-top:8px;'>"
        "<strong style='color:#1e3a8a;'>🔒 보안 기준 준수 (Security Standards)</strong><br><br>"
        "• ISO/IEC 27001 정보보안 관리체계 인증 기준 준용<br>"
        "• GDPR 및 국내 개인정보보호법 가이드라인 철저 준거<br>"
        "• TLS 1.3 차세대 전송 암호화 적용 (서버-클라이언트 통신 보호)<br>"
        "• AES-256 Fernet 기반의 고강도 세션 데이터 암호화<br>"
        "• SHA-256 단방향 해시를 통한 연락처 및 비밀번호 암호화 저장<br>"
        "• 로그아웃 시 단말기 내 민감 정보 메모리 점유 즉시 해제 (임시 데이터 잔류 방지)"
        "</div>",
        unsafe_allow_html=True,
    )
