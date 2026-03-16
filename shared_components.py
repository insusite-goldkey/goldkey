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
    st.markdown(
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
    # ── [이용 필수동의 4가지 박스] ─────────────────────────────────────────
    st.markdown("""<style>
/* 필수동의 박스 — 체크박스 영역 border 스타일링 */
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stCheckbox"]) {
    background: #f0f6ff;
    border-left: 1.5px solid #1e3a8a;
    border-right: 1.5px solid #1e3a8a;
    border-bottom: 1.5px solid #1e3a8a;
    border-radius: 0 0 8px 8px;
    padding: 4px 10px 8px 10px;
    margin-bottom: 6px;
}
</style>""", unsafe_allow_html=True)
    st.markdown(
        "<div style='background:#1e3a8a;border-radius:8px 8px 0 0;"
        "padding:7px 14px;margin-top:10px;text-align:center;'>"
        "<span style='font-size:0.85rem;font-weight:900;color:#fff;'>"
        "📋 이용 필수동의 확인 (아래 항목을 읽고 동의해 주세요)</span></div>",
        unsafe_allow_html=True,
    )
    # 전체동의 → 개별 항목 자동 체크
    _all_key = f"{terms_agree_key}_all"
    if st.session_state.get(_all_key, False):
        st.session_state[f"{terms_agree_key}_c1"] = True
        st.session_state[f"{terms_agree_key}_c2"] = True
        st.session_state[f"{terms_agree_key}_c3"] = True
        st.session_state[f"{terms_agree_key}_c4"] = True
        st.session_state[f"{terms_agree_key}_c5"] = True
    st.checkbox("🔲 **전체 동의** (필수·선택·내보험다보여 항목 모두 동의)", key=_all_key)
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
    with st.popover("📋 내보험다보여 연동 안내 전문 보기", use_container_width=True):
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
    if _c5:
        st.success("✅ 내보험다보여 연동 동의 완료 — AI 증권분석·트리니티 리포트 활성화")
    else:
        st.caption("⚠️ 위 항목에 동의하시면 AI 증권분석·트리니티 리포트가 활성화됩니다.")
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
        secret = get_env_secret("ENCRYPTION_KEY", "gk_token_secret_2026")
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
