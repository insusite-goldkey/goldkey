"""
components.py — Goldkey AI CRM/HQ 공통 UI 컴포넌트

Outlook 파스텔 스타일 + 손보사 표준 입력폼 + SPA 라우터 지원
HQ(app.py) 와 CRM(crm_app.py) 양쪽에서 동일하게 호출.

사용법:
    from components import inject_outlook_css, render_spa_nav, render_outlook_customer_list
    from components import render_mini_calendar, 손보사_standard_form
"""
from __future__ import annotations

import datetime
import calendar as _calendar_mod
from typing import Optional

import streamlit as st

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
            st.session_state[session_key]       = pid
            st.session_state["crm_spa_mode"]    = "customer"
            st.session_state["crm_spa_screen"]  = "contact"
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
        name    = st.text_input("이름 *", value=d.get("name", ""), key=f"{key_prefix}_name")
        contact = st.text_input(
            "연락처 * (암호화 저장)",
            value="",
            placeholder="01012345678",
            key=f"{key_prefix}_contact",
            help="입력 시 SHA-256 해시로 암호화되어 저장됩니다.",
        )
        birth   = st.text_input(
            "생년월일 (YYYYMMDD)",
            value=d.get("birth_date", ""),
            key=f"{key_prefix}_birth",
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
        address = st.text_input("주소", value=d.get("address", ""), key=f"{key_prefix}_addr")
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
        "address":             address,
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
        result["_raw_contact"] = contact

    return result
