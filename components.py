"""
components.py — Goldkey AI CRM/HQ 공통 UI 컴포넌트

Outlook 파스텔 스타일 + 손보사 표준 입력폼 + SPA 라우터 지원
HQ(app.py) 와 CRM(crm_app.py) 양쪽에서 동일하게 호출.

사용법:
    from components import (
        apply_gp_pastel_theme, inject_outlook_css,
        render_radio_spa_nav, render_spa_nav,
        render_outlook_customer_list, render_mini_calendar,
        손보사_standard_form, auto_commit_field,
    )
"""
from __future__ import annotations

import datetime
import calendar as _calendar_mod
import os
from typing import Optional

import streamlit as st
import streamlit.components.v1 as _stc

# ══════════════════════════════════════════════════════════════════════════════
# §1 GP Outlook 파스텔 CSS
# ══════════════════════════════════════════════════════════════════════════════
_OUTLOOK_CSS = """<style>
/* ── GP Outlook Pastel Base (#F8FBFA) ────────────────────────────── */
.gko-page { background:#F8FBFA; font-family:'Noto Sans KR',sans-serif; font-size:14px; }
/* ── 연락처 리스트 ────────────────────────────────────────────────── */
.gko-contact-row {
  display:flex; align-items:center; gap:10px;
  padding:9px 12px; border-bottom:1px solid #EAEAEF;
  cursor:pointer; transition:background 0.12s;
  background:#ffffff;
}
.gko-contact-row:hover   { background:#EEF4FB; }
.gko-contact-row.selected { background:#dbeafe; border-left:3px solid #3b82f6; }
.gko-contact-avatar {
  width:34px; height:34px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  font-size:0.88rem; font-weight:900; flex-shrink:0;
}
.gko-contact-name { font-size:0.9rem; font-weight:700; color:#1e293b; }
.gko-contact-sub  { font-size:0.74rem; color:#64748b; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.gko-tier-badge   { font-size:0.65rem; font-weight:900; padding:1px 7px; border-radius:10px; white-space:nowrap; }
/* ── SPA 네비게이션 바 ───────────────────────────────────────────── */
.gko-nav-bar {
  display:flex; gap:4px; background:#f1f5f9;
  padding:6px 8px; border-radius:10px;
  border:1px solid #EAEAEF; margin-bottom:14px;
  overflow-x:auto;
}
/* ── 스케줄 블록 (파스텔 라벤더) ────────────────────────────────── */
.gko-sched-block {
  background:#E6E6FA; border:1px solid #c4b5fd;
  border-radius:8px; padding:8px 12px; margin-bottom:6px;
  font-size:0.82rem;
}
.gko-sched-time  { font-size:0.72rem; color:#7c3aed; font-weight:700; }
.gko-sched-title { font-weight:900; color:#3b0764; }
/* ── 메모장 (파스텔 옐로우 #FDFD96) ─────────────────────────────── */
.gko-memo-box {
  background:#FDFD96; border:1px dashed #d97706;
  border-radius:8px; padding:10px 14px; font-size:0.82rem;
}
/* ── 상세 패널 ───────────────────────────────────────────────────── */
.gko-detail-panel { background:#F8FBFA; padding:14px; border-radius:10px; border:1px solid #EAEAEF; }
.gko-field-label  { font-size:0.7rem; color:#64748b; font-weight:700; text-transform:uppercase; margin-bottom:2px; }
.gko-field-value  { font-size:0.9rem; color:#1e293b; font-weight:500; margin-bottom:10px; }
/* ── 섹션 헤더 ───────────────────────────────────────────────────── */
.gko-section-header {
  font-size:0.78rem; font-weight:900; color:#1e40af;
  letter-spacing:0.08em; text-transform:uppercase;
  border-bottom:2px solid #bfdbfe; padding-bottom:4px; margin:12px 0 10px;
}
/* ── 미니 달력 ───────────────────────────────────────────────────── */
.gko-mini-cal { font-size:0.78rem; width:100%; border-collapse:collapse; }
.gko-mini-cal th {
  text-align:center; padding:4px 2px;
  font-size:0.7rem; color:#64748b; font-weight:700;
}
.gko-mini-cal td {
  text-align:center; padding:4px 2px;
  border-radius:4px; cursor:pointer; width:14%;
}
.gko-mini-cal td:hover  { background:#dbeafe; }
.gko-mini-cal td.today  { background:#3b82f6; color:#fff; font-weight:900; border-radius:50%; }
.gko-mini-cal td.has-ev { font-weight:900; color:#1d4ed8; text-decoration:underline; }
.gko-mini-cal td.sel    { background:#bfdbfe; border-radius:50%; }
/* ── 고객 리스트 검색 박스 ───────────────────────────────────────── */
.gko-list-header {
  background:#F8FBFA; padding:10px 14px;
  border-bottom:1px solid #EAEAEF; display:flex;
  align-items:center; justify-content:space-between;
}
</style>"""


def inject_outlook_css() -> None:
    """GP Outlook 파스텔 CSS를 Streamlit 페이지에 주입."""
    st.markdown(_OUTLOOK_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# §2 SPA 라우터 (st.tabs 금지 대체)
# ══════════════════════════════════════════════════════════════════════════════
_SPA_MENUS = [
    ("👥", "연락처 상세",   "contact"),
    ("📅", "스케줄",        "schedule"),
    ("🌐", "내보험다보여",  "nibo"),
    ("📊", "증권분석",      "analysis"),
    ("🤖", "AI 브리핑",     "ai_brief"),
    ("💬", "카카오 발송",   "kakao"),
]


def render_spa_nav(
    active_screen: str,
    session_key: str = "crm_spa_screen",
    back_mode_key: str = "crm_spa_mode",
    back_pid_key:  str = "crm_selected_pid",
) -> str:
    """
    6대 SPA 네비게이션 바 + [🔙 목록으로] 버튼.
    st.tabs 금지 정책 준수 — session_state 라우팅.
    Returns: 현재 활성 screen 키
    """
    back_col, nav_col = st.columns([1, 7])
    with back_col:
        if st.button("🔙 목록", key=f"{session_key}_back", use_container_width=True):
            st.session_state[back_mode_key] = "list"
            st.session_state[back_pid_key]  = ""
            st.rerun()
    with nav_col:
        btn_cols = st.columns(len(_SPA_MENUS))
        for i, (icon, label, key) in enumerate(_SPA_MENUS):
            with btn_cols[i]:
                btn_type = "primary" if active_screen == key else "secondary"
                if st.button(
                    f"{icon} {label}",
                    key=f"{session_key}_{key}",
                    type=btn_type,
                    use_container_width=True,
                ):
                    st.session_state[session_key] = key
                    st.rerun()
    return active_screen


# ══════════════════════════════════════════════════════════════════════════════
# §3 고객 목록 (Outlook 연락처 리스트)
# ══════════════════════════════════════════════════════════════════════════════

def render_outlook_customer_list(
    customers: list[dict],
    selected_pid: str = "",
    session_key: str = "crm_selected_pid",
) -> Optional[str]:
    """
    Outlook 스타일 고객 카드 목록.
    고객 클릭 시 session_state 업데이트 후 rerun → SPA 전환.
    """
    try:
        from shared_components import TIER_META, STATUS_META, decrypt_pii as _dpii
    except ImportError:
        TIER_META   = {
            1: {"label": "VVIP", "color": "#b45309", "bg": "#fef3c7", "icon": "👑"},
            2: {"label": "핵심",  "color": "#1d4ed8", "bg": "#dbeafe", "icon": "⭐"},
            3: {"label": "일반",  "color": "#374151", "bg": "#f3f4f6", "icon": "👤"},
        }
        STATUS_META = {}
        def _dpii(x): return x or ""

    if not customers:
        st.info("🔍 등록된 고객이 없습니다. 위 [➕ 신규 등록] 버튼을 눌러 추가하세요.")
        return selected_pid

    today_mo = datetime.date.today().month

    for c in customers:
        pid  = c.get("person_id", "")
        name = c.get("name", "?")
        tier = c.get("management_tier", 3)
        tm   = TIER_META.get(tier, TIER_META[3])
        job  = c.get("job", "")
        is_sel = (pid == selected_pid)

        _avatar_fg = {1: "#b45309", 2: "#1d4ed8", 3: "#374151"}.get(tier, "#374151")
        _avatar_bg = {1: "#fef3c7", 2: "#dbeafe", 3: "#f3f4f6"}.get(tier, "#f3f4f6")
        sel_style = "border-left:3px solid #3b82f6;background:#dbeafe;" if is_sel else "background:#ffffff;"

        renewal_warn = ""
        if c.get("auto_renewal_month") == today_mo: renewal_warn += " 🚗만기"
        if c.get("fire_renewal_month") == today_mo: renewal_warn += " 🏠만기"

        flags = []
        if c.get("has_motorcycle"):        flags.append("🏍️")
        if c.get("is_commercial_driver"):  flags.append("🚛")
        if c.get("has_foreign_stay"):      flags.append("✈️")
        flag_str = " ".join(flags)

        st.markdown(
            f"<div style='{sel_style}display:flex;align-items:center;gap:10px;"
            f"padding:9px 12px;border-bottom:1px solid #EAEAEF;border:1px dashed #000;border-radius:8px;margin-bottom:4px;'>"
            f"<div style='width:34px;height:34px;border-radius:50%;background:{_avatar_bg};"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-size:0.85rem;font-weight:900;color:{_avatar_fg};flex-shrink:0;'>"
            f"{name[0] if name else '?'}</div>"
            f"<div style='flex:1;min-width:0;'>"
            f"<div style='font-size:0.88rem;font-weight:700;color:#1e293b;'>{name} "
            f"<span style='font-size:0.7rem;font-weight:900;padding:1px 7px;border-radius:10px;"
            f"background:{tm['bg']};color:{tm['color']};'>{tm['icon']} {tm['label']}</span>"
            f"<span style='font-size:0.7rem;color:#dc2626;font-weight:900;'>{renewal_warn}</span>"
            f"<span style='font-size:0.7rem;color:#7c3aed;margin-left:4px;'>{flag_str}</span></div>"
            f"<div style='font-size:0.74rem;color:#64748b;'>{job}</div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )
        if st.button(
            f"▶ {name} 상세보기",
            key=f"gko_sel_{pid}",
            use_container_width=True,
            help=f"{name} 고객 선택",
        ):
            st.session_state[session_key]           = pid
            st.session_state["crm_spa_mode"]        = "customer"
            st.session_state["crm_spa_screen"]      = "contact"
            st.session_state.pop("crm_spa_screen_radio", None)
            st.rerun()

    return selected_pid


# ══════════════════════════════════════════════════════════════════════════════
# §4 미니 달력 (캘린더 3분할 좌측 패널)
# ══════════════════════════════════════════════════════════════════════════════

def render_mini_calendar(
    year: int,
    month: int,
    scheduled_dates: set,
    selected_date: str = "",
    session_key: str = "crm_cal_sel",
) -> str:
    """
    Outlook 스타일 미니 달력 렌더링.
    Returns: 선택된 날짜 (YYYY-MM-DD)
    """
    today     = datetime.date.today()
    today_str = today.isoformat()
    cal_weeks = _calendar_mod.monthcalendar(year, month)

    prev_mo = (month - 2) % 12 + 1
    prev_yr = year - 1 if month == 1 else year
    next_mo = month % 12 + 1
    next_yr = year + 1 if month == 12 else year

    hd1, hd2, hd3 = st.columns([1, 4, 1])
    with hd1:
        if st.button("◀", key=f"{session_key}_prev", use_container_width=True):
            st.session_state[f"{session_key}_ym"] = (prev_yr, prev_mo)
            st.rerun()
    with hd2:
        st.markdown(
            f"<div style='text-align:center;font-size:0.85rem;font-weight:900;"
            f"color:#1e3a8a;padding:4px 0;'>{year}년 {month}월</div>",
            unsafe_allow_html=True,
        )
    with hd3:
        if st.button("▶", key=f"{session_key}_next", use_container_width=True):
            st.session_state[f"{session_key}_ym"] = (next_yr, next_mo)
            st.rerun()

    day_names = ["월", "화", "수", "목", "금", "토", "일"]
    html  = "<table class='gko-mini-cal'><tr>"
    for i, d in enumerate(day_names):
        color = "#dc2626" if d == "일" else ("#2563eb" if d == "토" else "#64748b")
        html += f"<th style='color:{color};'>{d}</th>"
    html += "</tr>"

    for week in cal_weeks:
        html += "<tr>"
        for i, day in enumerate(week):
            if day == 0:
                html += "<td></td>"
                continue
            ds = f"{year}-{month:02d}-{day:02d}"
            cls = ""
            if ds == today_str:
                cls = "today"
            elif ds == selected_date:
                cls = "sel"
            if ds in scheduled_dates and ds != today_str:
                cls = (cls + " has-ev").strip()
            c_style = "color:#dc2626;" if i == 6 else ("color:#2563eb;" if i == 5 else "")
            html += f"<td class='{cls}' style='{c_style}'>{day}</td>"
        html += "</tr>"
    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)

    sel_val = (
        datetime.date.fromisoformat(selected_date)
        if selected_date else today
    )
    sel_dt = st.date_input(
        "날짜 선택",
        value=sel_val,
        key=f"{session_key}_di",
        label_visibility="collapsed",
    )
    return str(sel_dt)


# ══════════════════════════════════════════════════════════════════════════════
# §5 손보사 표준 입력폼 (직업 1~3급, 이륜차/유상운송 등)
# ══════════════════════════════════════════════════════════════════════════════
_JOB_GRADE_1 = [
    "사무직 (1급)", "교사/공무원 (1급)", "전문직-의사·변호사 (1급)",
    "가정주부 (1급)", "대학생 (1급)",
]
_JOB_GRADE_2 = [
    "영업직 (2급)", "서비스업 (2급)", "운전직-비유상 (2급)",
    "판매직 (2급)", "기술직 (2급)", "건설직-관리직 (2급)", "농업/어업 (2급)",
]
_JOB_GRADE_3 = [
    "건설직-현장 (3급)", "이륜차 종사자 (3급)", "유상운송 종사자 (3급)",
    "스포츠 강사 (3급)", "군인/경찰 (3급)", "소방관 (3급)", "고위험직 (3급)",
]
_JOB_SPECIAL = [
    "이륜차 비유상 (특)", "이륜차 유상-배달 (특·고위험)",
    "해외 장기체류 6개월+ (특)", "선박·해상직 (특)",
]
ALL_JOB_OPTIONS = ["(선택)"] + _JOB_GRADE_1 + _JOB_GRADE_2 + _JOB_GRADE_3 + _JOB_SPECIAL


# ══════════════════════════════════════════════════════════════════════════════
# §4-B 다음(카카오) 우편번호 양방향 브릿지 컴포넌트
# ══════════════════════════════════════════════════════════════════════════════
_DAUM_COMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daum_address_component")

try:
    _daum_postcode_comp = _stc.declare_component("daum_address_v1", path=_DAUM_COMP_DIR)
except Exception:
    _daum_postcode_comp = None


def daum_address_component(key: str = "daum_addr_comp") -> dict | None:
    """
    다음(카카오) 우편번호 API 양방향 브릿지 컴포넌트.
    사용자가 주소를 선택하면 {zonecode, roadAddress, jibunAddress} dict 반환.
    선택 전에는 None 반환.
    """
    if _daum_postcode_comp is None:
        st.error("주소 검색 컴포넌트를 로드할 수 없습니다. (daum_address_component 폴더 확인)")
        return None
    result = _daum_postcode_comp(key=key, default=None)
    return result if isinstance(result, dict) else None


def 손보사_standard_form(
    initial: Optional[dict] = None,
    key_prefix: str = "sf",
    show_insurance_fields: bool = True,
) -> dict:
    """
    [손보사 표준 입력폼]
    직업 1~3급·특종, 이륜차/유상운송 고지, 보험 만기 정보 포함.
    Returns: 수정된 고객 딕셔너리 (저장은 db_utils.save_customer() 또는
             shared_components.customer_input_form() 호출)
    """
    try:
        from shared_components import TIER_META
    except ImportError:
        TIER_META = {1: {"label": "VVIP"}, 2: {"label": "핵심"}, 3: {"label": "일반"}}

    d = initial or {}

    job_val = d.get("job", "(선택)")
    if job_val and job_val not in ALL_JOB_OPTIONS:
        ALL_JOB_OPTIONS.append(job_val)
    job_idx = ALL_JOB_OPTIONS.index(job_val) if job_val in ALL_JOB_OPTIONS else 0

    st.markdown(
        "<div class='gko-section-header'>👤 기본 인적사항</div>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        name     = st.text_input("이름 *", value=d.get("name", ""), key=f"{key_prefix}_name")
        # 기존 연락처는 복호화하여 표시 (편집 용이성), 신규 입력 시 빈값으로 시작
        try:
            from shared_components import decrypt_pii as _dpii
            _raw_existing_contact = _dpii(d.get("contact", "") or "")
        except Exception:
            _raw_existing_contact = d.get("contact", "") or ""
        if _raw_existing_contact.startswith("gAAAA"):  # 복호화 실패 → 입력창 비움
            _raw_existing_contact = ""
        contact  = st.text_input(
            "연락처 * (암호화 저장)",
            value=_raw_existing_contact,
            placeholder="01012345678",
            key=f"{key_prefix}_contact",
            help="입력 시 Fernet 암호화되어 저장됩니다.",
        )
        birth    = st.text_input(
            "생년월일 (YYYYMMDD)",
            value=d.get("birth_date", ""),
            key=f"{key_prefix}_birth",
        )
        referrer = st.text_input(
            "소개자",
            value=d.get("referrer_name", ""),
            placeholder="소개한 분의 이름",
            key=f"{key_prefix}_referrer",
        )
    with c2:
        gender = st.selectbox(
            "성별", ["(선택)", "남성", "여성"],
            index=["(선택)", "남성", "여성"].index(d.get("gender") or "(선택)"),
            key=f"{key_prefix}_gender",
        )
        tier = st.selectbox(
            "관리 등급", [3, 2, 1],
            format_func=lambda x: TIER_META.get(x, {}).get("label", str(x)),
            index=[3, 2, 1].index(d.get("management_tier", 3)),
            key=f"{key_prefix}_tier",
        )
        status = st.selectbox(
            "상담 상태",
            ["potential", "active", "contracted", "closed"],
            format_func=lambda x: {
                "potential": "가망", "active": "진행중",
                "contracted": "계약", "closed": "종료",
            }.get(x, x),
            index=["potential", "active", "contracted", "closed"].index(
                d.get("status", "potential")
            ),
            key=f"{key_prefix}_status",
        )
        # ── 다음 우편번호 주소 검색 UI ──────────────────────────────
        _az_zone_key   = f"{key_prefix}_addr_zone"
        _az_road_key   = f"{key_prefix}_addr_road"
        _az_modal_key  = f"{key_prefix}_addr_modal"
        if _az_zone_key not in st.session_state:
            st.session_state[_az_zone_key] = ""
        if _az_road_key not in st.session_state:
            st.session_state[_az_road_key] = d.get("address", "") or ""
        _az_col1, _az_col2 = st.columns([3, 1])
        with _az_col1:
            st.text_input("📮 우편번호", value=st.session_state[_az_zone_key],
                          disabled=True, key=f"{key_prefix}_zone_disp",
                          label_visibility="visible")
        with _az_col2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("🔍 주소 검색", key=f"{key_prefix}_addr_btn", use_container_width=True):
                st.session_state[_az_modal_key] = True
                st.rerun()
        if st.session_state.get(_az_modal_key, False):
            _daum_result = daum_address_component(key=f"{key_prefix}_daum")
            if _daum_result:
                st.session_state[_az_zone_key] = _daum_result.get("zonecode", "")
                st.session_state[_az_road_key] = _daum_result.get("roadAddress", "")
                st.session_state[_az_modal_key] = False
                st.rerun()
            if st.button("✕ 닫기", key=f"{key_prefix}_addr_close"):
                st.session_state[_az_modal_key] = False
                st.rerun()
        st.text_input("🏠 기본 주소 (도로명)", value=st.session_state[_az_road_key],
                      disabled=True, key=f"{key_prefix}_road_disp")
        address_top = st.session_state[_az_road_key]

    st.markdown(
        "<div class='gko-section-header'>💼 직업 등급 & 손보사 고지 사항</div>",
        unsafe_allow_html=True,
    )
    c3, c4 = st.columns(2)
    with c3:
        job = st.selectbox(
            "직업 (손보사 표준 분류) *",
            ALL_JOB_OPTIONS,
            index=job_idx,
            key=f"{key_prefix}_job",
            help="1급=사무직·가정주부, 2급=영업·운전, 3급=건설·이륜차·고위험",
        )
    with c4:
        has_motorcycle       = st.checkbox(
            "🏍️ 이륜차 소유 또는 상시 이용",
            value=bool(d.get("has_motorcycle", False)),
            key=f"{key_prefix}_moto",
        )
        is_commercial_driver = st.checkbox(
            "🚛 유상운송 종사 (배달·택시·화물)",
            value=bool(d.get("is_commercial_driver", False)),
            key=f"{key_prefix}_comm",
        )
        has_foreign_stay     = st.checkbox(
            "✈️ 해외 6개월 이상 체류 예정",
            value=bool(d.get("has_foreign_stay", False)),
            key=f"{key_prefix}_for",
        )

    # 손보사 고지 경고
    if has_motorcycle or is_commercial_driver:
        st.markdown(
            "<div style='background:#fef3c7;border:1px dashed #f59e0b;border-radius:8px;"
            "padding:8px 12px;font-size:0.78rem;font-weight:900;color:#92400e;'>"
            "⚠️ 이륜차/유상운송 고지 필수 — 미고지 시 보험금 지급 거절 사유가 됩니다.</div>",
            unsafe_allow_html=True,
        )

    if show_insurance_fields:
        st.markdown(
            "<div class='gko-section-header'>🚗 보험 만기 정보</div>",
            unsafe_allow_html=True,
        )
        c5, c6 = st.columns(2)
        with c5:
            auto_mo = st.number_input(
                "자동차보험 만기월 (0=없음)", 0, 12,
                value=int(d.get("auto_renewal_month") or 0),
                key=f"{key_prefix}_automo",
            )
        with c6:
            fire_mo = st.number_input(
                "화재보험 만기월 (0=없음)", 0, 12,
                value=int(d.get("fire_renewal_month") or 0),
                key=f"{key_prefix}_firemo",
            )

    st.markdown(
        "<div class='gko-section-header'>📝 상담 메모</div>",
        unsafe_allow_html=True,
    )
    memo = st.text_area(
        "메모 (파스텔 메모장)",
        value=d.get("memo", ""),
        height=80,
        key=f"{key_prefix}_memo",
    )

    result = {
        **d,
        "name":                name,
        "gender":              None if gender == "(선택)" else gender,
        "birth_date":          birth,
        "job":                 None if job == "(선택)" else job,
        "address":             address_top,
        "referrer_name":       referrer,
        "management_tier":     tier,
        "status":              status,
        "has_motorcycle":      has_motorcycle,
        "is_commercial_driver": is_commercial_driver,
        "has_foreign_stay":    has_foreign_stay,
        "memo":                memo,
    }
    if show_insurance_fields:
        result["auto_renewal_month"] = auto_mo or None
        result["fire_renewal_month"] = fire_mo or None
    if contact:
        result["contact"] = contact

    return result


# ══════════════════════════════════════════════════════════════════════════════
# §5 손보사 표준 직업 검색 엔진 (상해급수 기반 Autocomplete)
# ══════════════════════════════════════════════════════════════════════════════

def render_job_search_engine(
    key_prefix: str = "job_srch",
    initial_job: str = "",
    initial_injury: int = 0,
) -> tuple[str, int]:
    """
    손보사 표준 직업 검색 엔진.
    실시간 키워드 필터링 + 상해급수 배지 표시 + session_state 바인딩.

    Returns:
        (선택된_직업명, 상해급수_정수)  — 미선택 시 ("", 0)
    """
    try:
        from standard_occupations import (
            search_occupations, INJURY_LEVEL_GUIDE, STANDARD_OCCUPATIONS
        )
    except ImportError:
        st.warning("standard_occupations.py 없음 — 직업 수동 입력 모드")
        _job_manual = st.text_input("💼 직업 (직접 입력)", value=initial_job, key=f"{key_prefix}_manual")
        return _job_manual, initial_injury

    _sel_key   = f"{key_prefix}_selected_job"
    _inj_key   = f"{key_prefix}_injury_level"
    _kw_key    = f"{key_prefix}_keyword"

    # 초기값 세팅
    if _sel_key not in st.session_state:
        st.session_state[_sel_key]  = initial_job
    if _inj_key not in st.session_state:
        st.session_state[_inj_key]  = initial_injury
    if _kw_key not in st.session_state:
        st.session_state[_kw_key]   = ""

    st.markdown(
        "<div style='font-size:0.8rem;font-weight:900;color:#1d4ed8;"
        "margin:6px 0 4px 0;'>💼 직업 (손보사 표준 상해급수 검색)</div>",
        unsafe_allow_html=True,
    )

    # ── 이미 선택된 직업 표시 ────────────────────────────────────────────
    _cur_job = st.session_state.get(_sel_key, "")
    _cur_inj = st.session_state.get(_inj_key, 0)

    if _cur_job and _cur_inj:
        _guide = INJURY_LEVEL_GUIDE.get(_cur_inj, {})
        _bg    = _guide.get("bg", "#f3f4f6")
        _clr   = _guide.get("color", "#374151")
        _brd   = _guide.get("border", "#d1d5db")
        _em    = _guide.get("badge_emoji", "⚪")
        st.markdown(
            f"<div style='background:{_bg};border:1px solid {_brd};"
            f"border-radius:8px;padding:8px 14px;font-size:0.85rem;"
            f"font-weight:900;color:{_clr};margin-bottom:6px;display:flex;"
            f"align-items:center;gap:8px;'>"
            f"{_em} <b>{_cur_job}</b>"
            f"<span style='font-size:0.75rem;margin-left:auto;"
            f"background:{_clr};color:#fff;padding:2px 8px;"
            f"border-radius:12px;'>{_guide.get('label','')}</span></div>",
            unsafe_allow_html=True,
        )
        _col_reset, _ = st.columns([1, 3])
        with _col_reset:
            if st.button("🔄 직업 재검색", key=f"{key_prefix}_reset", use_container_width=True):
                st.session_state[_sel_key] = ""
                st.session_state[_inj_key] = 0
                st.session_state[_kw_key]  = ""
                st.rerun()
        return _cur_job, _cur_inj

    # ── 검색 UI ──────────────────────────────────────────────────────────
    _kw = st.text_input(
        "🔍 직업 검색 (예: 사무원, 운전기사, 의사)",
        value=st.session_state.get(_kw_key, ""),
        placeholder="직업명 또는 업종을 입력하세요",
        key=f"{key_prefix}_kw_input",
    )
    st.session_state[_kw_key] = _kw

    # 빠른 선택 버튼 (급수별)
    _quick_col1, _quick_col2, _quick_col3 = st.columns(3)
    with _quick_col1:
        if st.button("🔵 1급 전체 보기", key=f"{key_prefix}_q1", use_container_width=True):
            st.session_state[_kw_key] = "1급"
            st.rerun()
    with _quick_col2:
        if st.button("🟡 2급 전체 보기", key=f"{key_prefix}_q2", use_container_width=True):
            st.session_state[_kw_key] = "2급"
            st.rerun()
    with _quick_col3:
        if st.button("🔴 3급 전체 보기", key=f"{key_prefix}_q3", use_container_width=True):
            st.session_state[_kw_key] = "3급"
            st.rerun()

    # 급수별 전체 보기 처리
    _kw_active = st.session_state.get(_kw_key, "")
    if _kw_active in ("1급", "2급", "3급"):
        _level_filter = int(_kw_active[0])
        _results = [j for j in STANDARD_OCCUPATIONS if j["injury_level"] == _level_filter]
    else:
        _results = search_occupations(_kw_active) if _kw_active.strip() else []

    if _results:
        _opts = [
            f"{j['job_name']} — 상해 {j['injury_level']}급  [{j['category']}]"
            for j in _results
        ]
        _chosen_str = st.selectbox(
            f"검색 결과 ({len(_results)}건)",
            ["— 선택 —"] + _opts,
            key=f"{key_prefix}_select",
        )
        if _chosen_str != "— 선택 —":
            _idx = _opts.index(_chosen_str)
            _chosen_occ = _results[_idx]
            if st.button(
                f"✅ [{_chosen_occ['job_name']}] 상해 {_chosen_occ['injury_level']}급 선택 확정",
                key=f"{key_prefix}_confirm",
                use_container_width=True,
                type="primary",
            ):
                st.session_state[_sel_key]  = _chosen_occ["job_name"]
                st.session_state[_inj_key]  = _chosen_occ["injury_level"]
                # HQ 파이프라인 세션 바인딩
                st.session_state["customer_job"]    = _chosen_occ["job_name"]
                st.session_state["injury_level"]    = _chosen_occ["injury_level"]
                st.session_state[_kw_key]           = ""
                st.rerun()
        # 인수심사 가이드 미리보기
        if _chosen_str != "— 선택 —":
            _idx2 = _opts.index(_chosen_str)
            _prev_occ = _results[_idx2]
            _g = INJURY_LEVEL_GUIDE.get(_prev_occ["injury_level"], {})
            st.markdown(
                f"<div style='background:{_g.get('bg','#f3f4f6')};"
                f"border:1px dashed {_g.get('border','#d1d5db')};"
                f"border-radius:6px;padding:6px 10px;font-size:0.74rem;"
                f"color:{_g.get('color','#374151')};margin-top:4px;'>"
                f"⚠️ <b>인수심사 가이드</b>: {_g.get('underwriting','')}</div>",
                unsafe_allow_html=True,
            )
    elif _kw_active.strip():
        st.caption("검색 결과 없음 — 다른 키워드로 시도하거나 직접 입력하세요.")
        _manual = st.text_input("직접 입력 (미등록 직업)", placeholder="직업명 입력", key=f"{key_prefix}_manual_fb")
        if st.button("✅ 직접 입력 직업 사용", key=f"{key_prefix}_manual_confirm"):
            if _manual.strip():
                st.session_state[_sel_key] = _manual.strip()
                st.session_state[_inj_key] = 1
                st.session_state["customer_job"]  = _manual.strip()
                st.session_state["injury_level"]  = 1
                st.rerun()

    return st.session_state.get(_sel_key, ""), st.session_state.get(_inj_key, 0)


# ══════════════════════════════════════════════════════════════════════════════
# §6 GP 파스텔 전역 테마 주입 (apply_gp_pastel_theme)
# ══════════════════════════════════════════════════════════════════════════════
_GP_PASTEL_THEME_CSS = """<style>
/* ── GP 전역 파스텔 테마 v2 ─────────────────────────────────────────── */
:root {
  --gp-bg:      #F8FBFA;
  --gp-border:  #EAEAEF;
  --gp-memo:    #FDFD96;
  --gp-sched:   #E6E6FA;
  --gp-font:    14px;
  --gp-navy:    #1e3a8a;
  --gp-text:    #1e293b;
  --gp-sub:     #64748b;
}
/* 전체 배경 + 폰트 */
[data-testid="stApp"],
[data-testid="stAppViewContainer"] > .main {
  background: var(--gp-bg) !important;
  font-size: var(--gp-font) !important;
  font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif !important;
}
/* 사이드바 */
[data-testid="stSidebar"] { background: #f1f5f9 !important; }
/* 카드/섹션 기본 테두리 */
.gp-card {
  background: #ffffff;
  border: 1px dashed #000;
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 10px;
}
/* 메모 박스 (#FDFD96) */
.gp-memo {
  background: var(--gp-memo);
  border: 1px dashed #d97706;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.85rem;
}
/* 스케줄 블록 (#E6E6FA) */
.gp-sched {
  background: var(--gp-sched);
  border: 1px solid #c4b5fd;
  border-radius: 8px;
  padding: 8px 12px;
  margin-bottom: 6px;
  font-size: 0.82rem;
}
/* 헤더 배지 */
.gp-header {
  background: var(--gp-bg);
  border: 1px dashed #000;
  border-radius: 10px;
  padding: 9px 14px;
  font-size: 1.0rem;
  font-weight: 900;
  color: var(--gp-navy);
  margin-bottom: 12px;
}
/* ── st.radio → 버튼형 SPA 네비 ───────────────────────────────────── */
div[data-testid="stRadio"] > div {
  display: flex !important;
  flex-wrap: nowrap !important;
  gap: 4px !important;
  background: #f1f5f9;
  padding: 5px 7px;
  border-radius: 10px;
  border: 1px solid var(--gp-border);
  overflow-x: auto;
}
div[data-testid="stRadio"] > div > label {
  flex: 1 !important;
  text-align: center !important;
  padding: 7px 10px !important;
  border-radius: 8px !important;
  border: 1px solid #d1d5db !important;
  background: #ffffff !important;
  font-size: 0.82rem !important;
  font-weight: 700 !important;
  cursor: pointer !important;
  white-space: nowrap !important;
  transition: background 0.12s, color 0.12s !important;
  color: var(--gp-text) !important;
}
div[data-testid="stRadio"] > div > label:has(input:checked) {
  background: var(--gp-navy) !important;
  color: #ffffff !important;
  border-color: var(--gp-navy) !important;
  font-weight: 900 !important;
}
div[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }
/* ── [GP-RESPONSIVE] 모바일 스태킹 강제 (768px 이하) ───────────────── */
@media (max-width: 768px) {
  [data-testid="column"] {
    width: 100% !important;
    flex: 1 1 100% !important;
    min-width: 100% !important;
    margin-bottom: 16px !important;
  }
  [data-testid="stHorizontalBlock"] {
    flex-direction: column !important;
  }
}
/* ── 로딩 바 (파스텔) ───────────────────────────────────────────────── */
.gp-progress-wrap {
  background: #e5e7eb;
  border-radius: 8px;
  height: 10px;
  overflow: hidden;
  margin: 8px 0;
}
.gp-progress-fill {
  height: 10px;
  border-radius: 8px;
  background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
  transition: width 0.4s ease;
}
/* ── 인증 결과창 ────────────────────────────────────────────────────── */
.gp-auth-ok {
  background: #f0fdf4;
  border: 2px solid #16a34a;
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 0.9rem;
  font-weight: 900;
  color: #15803d;
}
.gp-auth-fail {
  background: #fef2f2;
  border: 2px solid #dc2626;
  border-radius: 10px;
  padding: 12px 16px;
  font-size: 0.9rem;
  font-weight: 900;
  color: #991b1b;
}
/* ── 실시간 동기화 상태 배지 ──────────────────────────────────────── */
.gp-sync-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.72rem;
  font-weight: 900;
  padding: 2px 10px;
  border-radius: 12px;
}
.gp-sync-running { background: #fef3c7; color: #92400e; border: 1px solid #f59e0b; }
.gp-sync-done    { background: #dcfce7; color: #166534; border: 1px solid #16a34a; }
.gp-sync-idle    { background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; }
</style>"""


def apply_gp_pastel_theme() -> None:
    """
    GP 전역 파스텔 테마 주입 — 모든 HQ/CRM 화면 최상단에서 1회 호출.
    [GP-DESIGN-V3] shared_components.inject_global_gp_design()을 먼저 호출하여
    Single Source of Truth 원칙을 적용하고, 컴포넌트 전용(.gko-*) CSS를 추가한다.
    """
    try:
        from shared_components import inject_global_gp_design as _igd
        _igd()
    except Exception:
        pass
    st.markdown(_GP_PASTEL_THEME_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# §7 st.radio 버튼형 SPA 네비게이션 (render_radio_spa_nav)
# ══════════════════════════════════════════════════════════════════════════════

def render_radio_spa_nav(
    menus: list[tuple[str, str]],
    session_key: str = "crm_spa_screen",
    back_mode_key: str = "crm_spa_mode",
    back_pid_key:  str = "crm_selected_pid",
    show_back: bool = True,
    extra_clears: tuple[str, ...] = (),
) -> str:
    """
    st.radio(horizontal=True)를 GP 버튼형으로 커스텀한 SPA 네비게이션.
    menus: [(label, screen_key), ...]
    Returns: 현재 선택된 screen_key
    """
    labels = [m[0] for m in menus]
    keys   = [m[1] for m in menus]
    cur    = st.session_state.get(session_key, keys[0])
    cur_idx = keys.index(cur) if cur in keys else 0

    # ── [BUG1 FIX] 라디오 위젯 내부상태와 session_state 강제 동기화 ────────────
    # Streamlit st.radio는 위젯 자체 상태(key 기반)를 우선하므로,
    # session_state[session_key]가 외부에서 변경됐을 때(예: 신규 고객 선택)
    # 위젯 내부상태가 이전 선택을 복원하는 "유령 화면" 버그가 발생한다.
    # 위젯 상태가 session_state와 다르면 위젯 상태를 삭제해 index가 적용되게 한다.
    _radio_wkey = f"{session_key}_radio"
    if _radio_wkey in st.session_state:
        _stored_label = st.session_state[_radio_wkey]
        _expected_label = labels[cur_idx] if cur_idx < len(labels) else labels[0]
        if _stored_label != _expected_label:
            del st.session_state[_radio_wkey]

    if show_back:
        back_c, nav_c = st.columns([1, 8])
        with back_c:
            if st.button("🔙 목록", key=f"{session_key}_back_radio", use_container_width=True):
                st.session_state[back_mode_key] = "list"
                st.session_state[back_pid_key]  = ""
                for _eck in extra_clears:
                    st.session_state.pop(_eck, None)
                st.rerun()
        with nav_c:
            sel = st.radio(
                "화면 선택",
                labels,
                index=cur_idx,
                horizontal=True,
                key=f"{session_key}_radio",
                label_visibility="collapsed",
            )
    else:
        sel = st.radio(
            "화면 선택",
            labels,
            index=cur_idx,
            horizontal=True,
            key=f"{session_key}_radio",
            label_visibility="collapsed",
        )

    new_key = keys[labels.index(sel)] if sel in labels else cur
    if new_key != cur:
        st.session_state[session_key] = new_key
        st.rerun()
    return new_key


# ══════════════════════════════════════════════════════════════════════════════
# §8 GCS 자동 커밋 헬퍼 (auto_commit_field)
# ══════════════════════════════════════════════════════════════════════════════

def auto_commit_field(
    field_key: str,
    new_value,
    commit_store_key: str = "_gp_auto_commit",
) -> None:
    """
    입력폼 필드값이 바뀔 때 즉시 st.session_state에 반영 (탭 이동 시 데이터 보존).
    
    사용법:
        name = st.text_input("이름", key="sf_name")
        auto_commit_field("sf_name", name)
    """
    store = st.session_state.setdefault(commit_store_key, {})
    if store.get(field_key) != new_value:
        store[field_key] = new_value


def get_committed_fields(commit_store_key: str = "_gp_auto_commit") -> dict:
    """GCS 자동 커밋된 필드 전체 반환."""
    return dict(st.session_state.get(commit_store_key, {}))


def render_pastel_progress(pct: int, label: str = "") -> None:
    """GP 파스텔 로딩 바 렌더링. pct: 0-100"""
    pct = max(0, min(100, pct))
    st.markdown(
        f"<div style='font-size:0.78rem;font-weight:700;color:#64748b;margin-bottom:3px;'>{label}</div>"
        f"<div class='gp-progress-wrap'>"
        f"<div class='gp-progress-fill' style='width:{pct}%;'></div></div>"
        f"<div style='font-size:0.72rem;color:#6b7280;text-align:right;'>{pct}%</div>",
        unsafe_allow_html=True,
    )


def render_auth_result(ok: bool, msg: str) -> None:
    """GP 인증 결과창 렌더링."""
    cls = "gp-auth-ok" if ok else "gp-auth-fail"
    icon = "✅" if ok else "❌"
    st.markdown(
        f"<div class='{cls}'>{icon} {msg}</div>",
        unsafe_allow_html=True,
    )


def render_sync_badge(status: str, label: str = "") -> None:
    """
    GP 실시간 동기화 상태 배지.
    status: 'running' | 'done' | 'idle'
    """
    _map = {
        "running": ("gp-sync-running", "⚡ 수집중"),
        "done":    ("gp-sync-done",    "✅ 완료"),
        "idle":    ("gp-sync-idle",    "⏸ 대기"),
    }
    cls, default_lbl = _map.get(status, _map["idle"])
    display = label or default_lbl
    st.markdown(
        f"<span class='gp-sync-badge {cls}'>{display}</span>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# §9 반응형 CSS 전용 주입 (inject_responsive_css)
# ══════════════════════════════════════════════════════════════════════════════
_RESPONSIVE_CSS = """<style>
/* ── [GP-RESPONSIVE] 모바일 스태킹 강제 원칙 (768px 이하) ─────────────── */
/* 브레이크포인트: 768px = 폰 + 세로모드 태블릿 트리거                    */
@media (max-width: 768px) {
  /* ① st.columns → 강제 100% 세로 스태킹 */
  [data-testid="column"] {
    width: 100% !important;
    flex: 1 1 100% !important;
    min-width: 100% !important;
    margin-bottom: 16px !important;
  }
  /* ② Streamlit row 컨테이너도 세로 강제 */
  [data-testid="stHorizontalBlock"] {
    flex-direction: column !important;
  }
  /* ③ 아웃룩 3분할 뷰 → 세로형 전환 */
  .outlook-container {
    flex-direction: column !important;
  }
  /* ④ 유동 타이포그래피 — clamp() 함수로 모바일 폰트 자동 조정 */
  p, span, label, .stMarkdown {
    font-size: clamp(12px, 3.5vw, 15px) !important;
  }
  h1 { font-size: clamp(18px, 5vw, 28px) !important; }
  h2 { font-size: clamp(15px, 4.5vw, 22px) !important; }
  h3 { font-size: clamp(13px, 4vw, 18px) !important; }
  /* ⑤ 미니 달력 전체 너비 */
  .gko-mini-cal { width: 100% !important; }
  /* ⑥ SPA 네비게이션 줄바꿈 허용 */
  div[data-testid="stRadio"] > div {
    flex-wrap: wrap !important;
  }
  div[data-testid="stRadio"] > div > label {
    flex: 1 1 45% !important;
  }
  /* ⑦ 데이터테이블·차트 오버플로우 방지 */
  .stDataFrame, .element-container {
    max-width: 100% !important;
    overflow-x: auto !important;
  }
}

/* ── GP 파스텔 버튼 — 전역 그라디언트 (AEC6CF → B4F8C8) ──────────────── */
.stApp { background-color: #F8FBFA !important; }

[data-testid="stButton"] > button,
button[kind="primary"],
button[kind="secondary"] {
  border-radius: 12px !important;
  font-weight: 700 !important;
  transition: opacity 0.15s !important;
}
[data-testid="stButton"] > button[kind="secondary"] {
  background: linear-gradient(135deg, #AEC6CF 0%, #B4F8C8 100%) !important;
  color: #1e293b !important;
  border: 1px solid #93c5b8 !important;
}
[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
  color: #1e3a8a !important;
  border: 1.5px solid #93c5fd !important;
  font-weight: 900 !important;
}
[data-testid="stButton"] > button:hover {
  opacity: 0.88 !important;
}
/* ── [GP-BTN-V3] 액션 버튼 자동 실제 크기 (full-width 방지) ──────────── */
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-secondary"] {
  width: auto !important;
  min-width: fit-content !important;
}
/* ── [GP-TYPO-V3] word-break + line-height 전역 적용 ─────────────────── */
p, span, div.stMarkdown, label {
  word-break: keep-all;
  line-height: 1.5;
}

/* ── 입력 필드 테두리 ────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div {
  border-color: #EAEAEF !important;
  border-radius: 8px !important;
  background: #ffffff !important;
  font-size: 14px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
}
</style>"""


def inject_responsive_css() -> None:
    """
    반응형 레이아웃 CSS 주입.
    [GP-DESIGN-V3] shared_components.inject_global_gp_design()이 이미 호출된 경우
    이 함수는 추가 컴포넌트 CSS만 보충한다 (중복 안전).
    apply_gp_pastel_theme() 이후 추가로 호출하면 덮어씌움.
    """
    try:
        from shared_components import inject_global_gp_design as _igd2
        _igd2()
    except Exception:
        pass
    st.markdown(_RESPONSIVE_CSS, unsafe_allow_html=True)
