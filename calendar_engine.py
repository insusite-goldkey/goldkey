"""
calendar_engine.py — 스마트 캘린더 & 글로벌 영업 파이프라인 엔진
[GP-CALENDAR] Goldkey AI Masters 2026
"""
from __future__ import annotations
import re, json, uuid, datetime, calendar as _cal_mod, urllib.parse
from typing import Optional
import streamlit as st

# ══ [1] 상수 ══════════════════════════════════════════════════════════════════
_CATS: dict[str, tuple] = {
    "consult":     ("🔴 상담일정",  "#상담일정",  "#fee2e2","#b91c1c","#ef4444"),
    "expiry":      ("🟠 보험만기",  "#보험만기",  "#fff7ed","#c2410c","#f97316"),
    "upsell":      ("🟣 업셀링",    "#업셀링",    "#faf5ff","#6d28d9","#a855f7"),
    "appointment": ("🔵 약속",      "#약속",      "#dbeafe","#1d4ed8","#3b82f6"),
    "todo":        ("🟡 할 일",     "#할일",      "#fef9c3","#92400e","#f59e0b"),
    "personal":    ("🟢 개인일정",  "#개인일정",  "#f0fdf4","#166534","#22c55e"),
}

_WEEKDAY_KO = ["월","화","수","목","금","토","일"]

def _weekday_ko(wd: int) -> str:
    return _WEEKDAY_KO[wd % 7]

# ══ [2] DB 레이어 ════════════════════════════════════════════════════════════
def _get_sb():
    try:
        from db_utils import _get_sb as _sb
        return _sb()
    except Exception:
        return None

def extract_tags(text: str) -> list[str]:
    return re.findall(r"#\w+", text or "")

def cal_save(agent_id, title, body, date, start_time="09:00", end_time="10:00",
             category="consult", person_id="", customer_name="", schedule_id="") -> str:
    sid = schedule_id or str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat()
    payload = {
        "schedule_id": sid, "agent_id": agent_id, "title": title,
        "memo": body, "date": date, "start_time": start_time,
        "end_time": end_time, "category": category,
        "is_deleted": False, "updated_at": now,
    }
    if not schedule_id:
        payload["created_at"] = now
    if person_id:
        payload["person_id"] = person_id
    if customer_name:
        payload["customer_name"] = customer_name
    sb = _get_sb()
    if sb:
        try:
            sb.table("gk_schedules").upsert(payload, on_conflict="schedule_id").execute()
        except Exception:
            try:
                minimal = {k: payload[k] for k in [
                    "schedule_id","agent_id","title","memo","date",
                    "start_time","category","is_deleted","updated_at"]}
                if not schedule_id:
                    minimal["created_at"] = now
                if person_id:
                    minimal["person_id"] = person_id
                sb.table("gk_schedules").upsert(minimal, on_conflict="schedule_id").execute()
            except Exception:
                pass
    evs = st.session_state.get("_cal_events", [])
    evs = [e for e in evs if e.get("schedule_id") != sid]
    evs.append({"schedule_id":sid,"title":title,"memo":body,"date":date,
                "start_time":start_time,"end_time":end_time,"category":category,
                "tags":extract_tags(title+" "+body),"customer_name":customer_name,"person_id":person_id})
    st.session_state["_cal_events"] = evs
    return sid

def cal_delete(schedule_id: str, agent_id: str = "") -> bool:
    """
    [GP-SEC] agent_id 제공 시 소유권 검증 — 타 설계사 일정 삭제 원천 차단.
    """
    sb = _get_sb()
    if sb and schedule_id:
        try:
            q = sb.table("gk_schedules").update({
                "is_deleted": True,
                "updated_at": datetime.datetime.utcnow().isoformat(),
            }).eq("schedule_id", schedule_id)
            if agent_id:
                q = q.eq("agent_id", agent_id)
            q.execute()
        except Exception:
            pass
    evs = st.session_state.get("_cal_events", [])
    st.session_state["_cal_events"] = [e for e in evs if e.get("schedule_id") != schedule_id]
    return True

def cal_search_by_tag(agent_id: str, tag: str, limit: int = 50) -> list[dict]:
    q = tag.strip()
    if not q:
        return []
    sq = q if q.startswith("#") else ("#" + q if re.match(r"^\w+$", q) else q)
    sb = _get_sb()
    if sb:
        try:
            rows = (
                sb.table("gk_schedules").select("*")
                .eq("is_deleted", False).eq("agent_id", agent_id)
                .or_(f"memo.ilike.%{sq}%,title.ilike.%{q}%")
                .order("date", desc=True).limit(limit).execute().data or []
            )
            return rows
        except Exception:
            pass
    ql = sq.lower()
    return [e for e in st.session_state.get("_cal_events", [])
            if ql in (e.get("memo","") + e.get("title","")).lower()]

def cal_load_month(agent_id: str, year: int, month: int) -> list[dict]:
    start = f"{year:04d}-{month:02d}-01"
    days  = _cal_mod.monthrange(year, month)[1]
    end   = f"{year:04d}-{month:02d}-{days:02d}"
    sb = _get_sb()
    if sb:
        try:
            return (sb.table("gk_schedules").select("*, gk_people(name)")
                    .eq("is_deleted",False).eq("agent_id",agent_id)
                    .gte("date",start).lte("date",end)
                    .order("date").order("start_time").execute().data or [])
        except Exception:
            pass
    ym = f"{year:04d}-{month:02d}"
    return [e for e in st.session_state.get("_cal_events",[]) if e.get("date","")[:7]==ym]

def cal_load_today(agent_id: str) -> list[dict]:
    today = datetime.date.today().isoformat()
    sb = _get_sb()
    if sb:
        try:
            return (sb.table("gk_schedules").select("*, gk_people(name)")
                    .eq("is_deleted",False).eq("agent_id",agent_id)
                    .eq("date",today).order("start_time").execute().data or [])
        except Exception:
            pass
    return [e for e in st.session_state.get("_cal_events",[]) if e.get("date")==today]

def cal_load_expiry_soon(agent_id: str, days: int = 7) -> list[dict]:
    today_str = datetime.date.today().isoformat()
    end_str   = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
    sb = _get_sb()
    if sb:
        try:
            return (sb.table("gk_schedules").select("*")
                    .eq("is_deleted",False).eq("agent_id",agent_id)
                    .ilike("memo","%#보험만기%")
                    .gte("date",today_str).lte("date",end_str)
                    .order("date").execute().data or [])
        except Exception:
            pass
    return []

def cal_load_customer(agent_id: str, person_id: str) -> list[dict]:
    if not person_id:
        return []
    sb = _get_sb()
    if sb:
        try:
            return (sb.table("gk_schedules").select("*")
                    .eq("is_deleted",False).eq("agent_id",agent_id)
                    .eq("person_id",person_id).order("date").execute().data or [])
        except Exception:
            pass
    return [e for e in st.session_state.get("_cal_events",[]) if e.get("person_id")==person_id]

# ══ [3] ICS 생성기 (RFC 5545) ════════════════════════════════════════════════
def generate_ics(title, date_str, start_time="09:00", end_time="10:00",
                 description="", uid="") -> bytes:
    _uid = uid or str(uuid.uuid4())
    sh,sm = (start_time+":00").split(":")[:2]
    eh,em = (end_time+":00").split(":")[:2]
    d = date_str.replace("-","")
    dtstamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    def _esc(s):
        return s.replace("\\","\\\\").replace(",","\\,").replace(";","\\;").replace("\n","\\n")
    ics = (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\n"
        "PRODID:-//Goldkey AI Masters 2026//KR\r\n"
        "CALSCALE:GREGORIAN\r\nMETHOD:PUBLISH\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{_uid}@goldkey-ai\r\nDTSTAMP:{dtstamp}\r\n"
        f"DTSTART;TZID=Asia/Seoul:{d}T{sh}{sm}00\r\n"
        f"DTEND;TZID=Asia/Seoul:{d}T{eh}{em}00\r\n"
        f"SUMMARY:{_esc(title)}\r\nDESCRIPTION:{_esc(description)}\r\n"
        "END:VEVENT\r\nEND:VCALENDAR\r\n"
    )
    return ics.encode("utf-8")

# ══ [4] 오늘의 핵심 영업 일정 위젯 ══════════════════════════════════════════
def render_today_widget(agent_id: str) -> None:
    if not agent_id:
        return
    today       = datetime.date.today()
    today_evs   = cal_load_today(agent_id)
    expiry_evs  = cal_load_expiry_soon(agent_id, days=7)
    if not today_evs and not expiry_evs:
        return
    _bind_schedule_context(today_evs + expiry_evs)
    with st.expander(
        f"📅 오늘의 핵심 영업 일정 & 만기 알림 — {today.month}/{today.day}({_weekday_ko(today.weekday())})",
        expanded=True,
    ):
        if today_evs:
            st.markdown("**⚡ 오늘 일정**")
            for ev in today_evs:
                icon = _CATS.get(ev.get("category","consult"), ("⚪",))[0]
                tgs  = extract_tags(ev.get("memo",""))
                tbadges = "".join(
                    f'<span style="background:#e0f2fe;color:#0369a1;padding:1px 6px;'
                    f'border-radius:10px;font-size:.70rem;margin-left:3px;">{t}</span>' for t in tgs)
                st.markdown(
                    f"<div style='padding:3px 0;'>{icon} <b>{ev.get('title','')}</b> "
                    f"<span style='color:#64748b;font-size:.80rem;'>"
                    f"{ev.get('start_time','')}~{ev.get('end_time','')}</span>{tbadges}</div>",
                    unsafe_allow_html=True)
        if expiry_evs:
            st.markdown("**⚠️ 7일 내 보험 만기 임박**")
            for ev in expiry_evs:
                d_str = ev.get("date", today.isoformat())
                try:
                    dl = (datetime.date.fromisoformat(d_str) - today).days
                    badge = "오늘!" if dl==0 else f"D-{dl}"
                    bc = "#ef4444" if dl<=2 else "#f97316"
                except Exception:
                    badge, bc = "임박","#f97316"
                st.markdown(
                    f"<div style='padding:3px 0;'>🟠 <b>{ev.get('title','')}</b> "
                    f"<span style='background:{bc};color:#fff;padding:2px 8px;border-radius:8px;"
                    f"font-size:.75rem;font-weight:700;'>{badge}</span> "
                    f"<span style='color:#64748b;font-size:.78rem;'>{d_str}</span></div>",
                    unsafe_allow_html=True)

# ══ [5] 고객 타임라인 ════════════════════════════════════════════════════════
def render_customer_timeline(agent_id: str, person_id: str, customer_name: str = "") -> None:
    if not person_id:
        return
    evs       = cal_load_customer(agent_id, person_id)
    today_str = datetime.date.today().isoformat()
    st.markdown(
        "<div style='font-size:.88rem;font-weight:900;color:#1a3a5c;margin:10px 0 6px;'>"
        "📅 과거 상담 이력 및 향후 일정 타임라인</div>", unsafe_allow_html=True)
    if not evs:
        st.caption("등록된 일정이 없습니다.")
        return
    past   = sorted([e for e in evs if e.get("date","") <  today_str], key=lambda x:x.get("date",""), reverse=True)
    future = sorted([e for e in evs if e.get("date","") >= today_str], key=lambda x:x.get("date",""))
    if future:
        for ev in future:
            d = ev.get("date","")
            try:
                dl = (datetime.date.fromisoformat(d)-datetime.date.today()).days
                suf = "오늘" if dl==0 else f"D-{dl}"
            except Exception:
                suf = ""
            color = _CATS.get(ev.get("category","consult"),("","","","","#94a3b8"))[4]
            tgs   = extract_tags(ev.get("memo",""))
            thml  = "".join(f'<span style="background:#f0f9ff;color:#0369a1;padding:1px 5px;border-radius:8px;font-size:.70rem;margin-left:2px;">{t}</span>' for t in tgs)
            st.markdown(
                f"<div style='border-left:3px solid {color};padding:4px 0 4px 10px;margin:3px 0;'>"
                f"<b>{d}</b> <span style='background:{color};color:#fff;padding:1px 6px;"
                f"border-radius:6px;font-size:.72rem;'>{suf}</span> {ev.get('title','')} {thml}</div>",
                unsafe_allow_html=True)
    if past:
        with st.expander(f"📂 과거 상담 이력 ({len(past)}건)", expanded=False):
            for ev in past[:15]:
                tgs = extract_tags(ev.get("memo",""))
                st.markdown(f"`{ev.get('date','')}` {ev.get('title','')} " + " ".join(f"`{t}`" for t in tgs))

# ══ [6] 스마트 캘린더 메인 ═══════════════════════════════════════════════════
def render_smart_calendar(agent_id: str, customers: list | None = None) -> None:
    customers = customers or []
    if "cal_year" not in st.session_state:
        st.session_state.cal_year  = datetime.date.today().year
        st.session_state.cal_month = datetime.date.today().month
    year  = int(st.session_state.cal_year)
    month = int(st.session_state.cal_month)

    # JS 클릭 → query_param 흡수
    _qd = st.query_params.get("cal_date","")
    if _qd:
        st.session_state["_cal_sel_date"] = _qd
        st.query_params.clear()
        try:
            _qdate = datetime.date.fromisoformat(_qd)
            st.session_state.cal_year, st.session_state.cal_month = _qdate.year, _qdate.month
            year, month = _qdate.year, _qdate.month
        except Exception:
            pass

    # [A] 태그 검색 바
    st.markdown("<div style='font-size:.82rem;font-weight:900;color:#374151;margin-bottom:4px;'>🔍 태그 및 일정 검색</div>", unsafe_allow_html=True)
    _cs1, _cs2 = st.columns([5,1])
    with _cs1:
        _tq = st.text_input("검색", label_visibility="collapsed",
                            placeholder="#암보험, #보험만기, 고객명 검색", key="cal_tag_search")
    with _cs2:
        _do_s = st.button("검색", key="cal_search_btn", type="primary", use_container_width=True)
    if _do_s and _tq.strip():
        _sr = cal_search_by_tag(agent_id, _tq.strip())
        if _sr:
            st.success(f"**{len(_sr)}건** 검색됨")
            for r in _sr[:20]:
                tgs = extract_tags(r.get("memo",""))
                bdg = "".join(f'<span style="background:#dbeafe;color:#1d4ed8;padding:1px 6px;border-radius:8px;font-size:.72rem;margin-left:3px;">{t}</span>' for t in tgs)
                st.markdown(f"`{r.get('date','')}` **{r.get('title','')}** {bdg}", unsafe_allow_html=True)
        else:
            st.info("검색 결과가 없습니다.")
        st.divider()

    # 월 이동
    _n1, _n2, _n3, _n4 = st.columns([1,1,3,1])
    with _n1:
        if st.button("◀ 이전", key="cal_prev_btn", use_container_width=True):
            if month==1: st.session_state.cal_year-=1; st.session_state.cal_month=12
            else: st.session_state.cal_month-=1
            st.rerun()
    with _n2:
        if st.button("오늘", key="cal_today_btn", use_container_width=True):
            st.session_state.cal_year=datetime.date.today().year
            st.session_state.cal_month=datetime.date.today().month
            st.rerun()
    with _n3:
        st.markdown(f"<div style='text-align:center;font-size:1.1rem;font-weight:900;color:#1a3a5c;padding:6px 0;'>{year}년 {month}월</div>", unsafe_allow_html=True)
    with _n4:
        if st.button("다음 ▶", key="cal_next_btn", use_container_width=True):
            if month==12: st.session_state.cal_year+=1; st.session_state.cal_month=1
            else: st.session_state.cal_month+=1
            st.rerun()

    # DB 이벤트 로드 → JS에 주입
    _evs = cal_load_month(agent_id, year, month)
    _evs_js = json.dumps([{
        "schedule_id": e.get("schedule_id",""),
        "title":       e.get("title",""),
        "date":        e.get("date",""),
        "start_time":  e.get("start_time","09:00") or "09:00",
        "end_time":    e.get("end_time","10:00") or "10:00",
        "category":    e.get("category","consult") or "consult",
        "body":        e.get("memo",""),
        "customer":    e.get("customer_name") or (e.get("gk_people") or {}).get("name","") or "",
    } for e in _evs], ensure_ascii=False)
    _cat_tags_js = json.dumps({k:v[1] for k,v in _CATS.items()}, ensure_ascii=False)

    # [B] JS 캘린더
    import streamlit.components.v1 as _cv1
    _cv1.html(_build_cal_html(_evs_js, year, month, _cat_tags_js), height=660, scrolling=False)

    # [C] 일정 추가/편집 폼
    _render_event_form(agent_id, customers, year, month)


def _render_event_form(agent_id, customers, year, month):
    sel_date_str = st.session_state.get("_cal_sel_date","")
    try:
        sel_date = datetime.date.fromisoformat(sel_date_str) if sel_date_str else datetime.date(year, month, 1)
    except Exception:
        sel_date = datetime.date(year, month, 1)
    edit_ev = st.session_state.get("_cal_edit_ev", None)
    form_title = "✏️ 일정 수정" if edit_ev else "📅 일정 추가"

    st.divider()
    with st.expander(form_title, expanded=bool(sel_date_str or edit_ev)):
        # 오토-태깅 분류 선택
        st.markdown("<div style='font-size:.78rem;font-weight:700;color:#374151;margin-bottom:4px;'>① 일정 분류 선택 → 해시태그 자동 입력</div>", unsafe_allow_html=True)
        _cat_default = edit_ev.get("category","consult") if edit_ev else "consult"
        _cat_idx = list(_CATS.keys()).index(_cat_default) if _cat_default in _CATS else 0
        _sel_cat = st.selectbox("일정 분류", options=list(_CATS.keys()),
                                format_func=lambda k: _CATS[k][0],
                                index=_cat_idx, key="cal_form_cat",
                                label_visibility="collapsed")
        # 빠른 해시태그 버튼 (오토-태깅 넛지)
        st.markdown("<div style='font-size:.73rem;color:#6b7280;margin-bottom:3px;'>빠른 해시태그 삽입:</div>", unsafe_allow_html=True)
        _tcols = st.columns(len(_CATS))
        for _ci, (_ck, _cv) in enumerate(_CATS.items()):
            with _tcols[_ci]:
                if st.button(_cv[1], key=f"qtag_{_ck}", use_container_width=True, help=_cv[0]):
                    st.session_state["_cal_body_prefill"] = _cv[1] + " "
                    st.session_state["cal_form_cat"] = _ck
                    st.rerun()

        # 날짜/시간
        _fc1, _fc2, _fc3 = st.columns([2,1,1])
        with _fc1:
            _f_date = st.date_input("날짜", value=datetime.date.fromisoformat(edit_ev["date"]) if edit_ev and edit_ev.get("date") else sel_date, key="cal_form_date")
        with _fc2:
            _f_stime = st.text_input("시작", value=edit_ev.get("start_time","09:00") if edit_ev else "09:00", key="cal_form_stime", placeholder="09:00")
        with _fc3:
            _f_etime = st.text_input("종료", value=edit_ev.get("end_time","10:00") if edit_ev else "10:00", key="cal_form_etime", placeholder="10:00")

        # 제목
        _f_title = st.text_input("② 일정 제목 *",
                                 value=edit_ev.get("title","") if edit_ev else "",
                                 placeholder="예: 홍길동 고객 #암보험 #VIP 상담",
                                 key="cal_form_title")
        # 메모/태그
        _body_default = (st.session_state.pop("_cal_body_prefill", None)
                         or (edit_ev.get("memo","") if edit_ev else _CATS.get(_sel_cat,("","#상담일정"))[1] + " "))
        _f_body = st.text_area("③ 메모 / 해시태그", value=_body_default,
                               placeholder="가이드(핵심주요) 단어를 입력하세요. (예: 홍길동 고객 #암보험 #VIP)",
                               height=80, key="cal_form_body")
        _ptags = extract_tags(_f_title + " " + _f_body)
        if _ptags:
            st.markdown("📎 추출된 태그: " + "".join(f'<span style="background:#e0f2fe;color:#0369a1;padding:1px 8px;border-radius:10px;font-size:.72rem;margin-right:3px;">{t}</span>' for t in _ptags), unsafe_allow_html=True)

        # 고객 연동
        _copts = ["— 선택 안 함 —"] + [c.get("name","") for c in customers if c.get("name")]
        _cdef  = edit_ev.get("customer_name","") if edit_ev else ""
        _cidx  = _copts.index(_cdef) if _cdef in _copts else 0
        _f_cust = st.selectbox("관련 고객", options=_copts, index=_cidx, key="cal_form_cust")
        _pid = ""
        if _f_cust and _f_cust != "— 선택 안 함 —":
            for c in customers:
                if c.get("name","") == _f_cust:
                    _pid = c.get("person_id","") or c.get("cust_id","")
                    break

        # 저장/ICS/삭제
        _b1, _b2, _b3 = st.columns([2,1,1])
        with _b1:
            _do_save = st.button("💾 저장", key="cal_form_save", type="primary", use_container_width=True)
        with _b2:
            _do_ics = st.button("📥 ICS", key="cal_form_ics", use_container_width=True, help="스마트폰 캘린더 저장용 .ics 생성")
        with _b3:
            _do_del = st.button("🗑️ 삭제", key="cal_form_del", use_container_width=True) if edit_ev else False

        if _do_save:
            if not _f_title.strip():
                st.error("일정 제목을 입력하세요.")
            else:
                cal_save(agent_id=agent_id, title=_f_title.strip(), body=_f_body.strip(),
                         date=_f_date.isoformat(), start_time=_f_stime or "09:00",
                         end_time=_f_etime or "10:00", category=_sel_cat,
                         person_id=_pid,
                         customer_name=_f_cust if _f_cust!="— 선택 안 함 —" else "",
                         schedule_id=edit_ev.get("schedule_id","") if edit_ev else "")
                for _k in ["_cal_sel_date","_cal_edit_ev"]:
                    st.session_state.pop(_k, None)
                st.session_state["_schedule_ctx_dirty"] = True
                st.success("✅ 저장되었습니다.")
                st.rerun()

        if _do_ics and _f_title.strip():
            _ics = generate_ics(_f_title.strip(), _f_date.isoformat(),
                                _f_stime or "09:00", _f_etime or "10:00", _f_body.strip())
            st.download_button("📅 .ics 다운로드 (스마트폰 캘린더 저장)", data=_ics,
                               file_name=f"goldkey_{_f_date.isoformat()}.ics",
                               mime="text/calendar", key="cal_ics_dl")
            _stext = (f"[Goldkey AI 일정 공유]\n📅 {_f_title.strip()}\n"
                      f"일시: {_f_date.isoformat()} {_f_stime}~{_f_etime}\n"
                      f"메모: {_f_body.strip()}\n\n"
                      f"▼ 첨부 파일을 열면 스마트폰 기본 캘린더에 바로 저장됩니다.\n"
                      f"※ 2026 Goldkey AI Masters")
            _kurl = "kakaotalk://send?text=" + urllib.parse.quote(_stext)
            st.markdown(
                f'<a href="{_kurl}" target="_blank" style="text-decoration:none;">'
                f'<div style="background:#FEE500;color:#000;padding:10px;border-radius:8px;'
                f'text-align:center;font-weight:900;font-size:.90rem;margin-top:6px;">'
                f'📤 고객 캘린더로 전송 (카카오톡)</div></a>',
                unsafe_allow_html=True)

        if _do_del and edit_ev:
            cal_delete(edit_ev.get("schedule_id",""), agent_id=agent_id)
            for _k in ["_cal_sel_date","_cal_edit_ev"]:
                st.session_state.pop(_k, None)
            st.success("🗑️ 삭제되었습니다.")
            st.rerun()

# ══ [7] AI 컨텍스트 바인딩 ═══════════════════════════════════════════════════
def _bind_schedule_context(evs: list) -> None:
    all_tags, summary = [], []
    for ev in evs:
        tgs = extract_tags(ev.get("memo","") + ev.get("title",""))
        all_tags.extend(tgs)
        summary.append(f"{ev.get('date','')} {ev.get('title','')} [{','.join(tgs)}]")
    st.session_state["_schedule_tags"] = list(dict.fromkeys(all_tags))
    st.session_state["_schedule_ctx"]  = "\n".join(summary[:10])

def get_schedule_ai_context() -> str:
    ctx  = st.session_state.get("_schedule_ctx","")
    tags = st.session_state.get("_schedule_tags",[])
    if not ctx and not tags:
        return ""
    tag_str = ", ".join(tags) if tags else "없음"
    return (
        f"\n\n## [캘린더 스케줄 컨텍스트 — 자동 주입]\n"
        f"현재 열람 중인 고객 관련 최근/예정 일정 태그: {tag_str}\n"
        f"일정 상세:\n{ctx}\n"
        f"→ 위 일정 태그(예: #상담예약, #업셀링, #보험만기)의 목적에 맞춘 "
        f"맞춤형 오프닝 멘트와 클로징 제안을 브리핑 리포트에 반드시 포함하시오."
    )

# ══ [8] JS 캘린더 HTML 빌더 ══════════════════════════════════════════════════
def _build_cal_html(evs_json: str, year: int, month: int, cat_tags_json: str) -> str:
    return f"""<!DOCTYPE html><html lang="ko"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:'Malgun Gothic','Noto Sans KR',sans-serif;}}
body{{background:#f0f4f8;padding:8px;}}
.cal-grid{{background:#fff;border-radius:12px;box-shadow:0 1px 6px rgba(30,80,160,.10);overflow:hidden;}}
.cal-wdays{{display:grid;grid-template-columns:repeat(7,1fr);background:#f8fafc;border-bottom:2px solid #e2e8f0;}}
.cal-wd{{text-align:center;padding:8px 0;font-size:.78rem;font-weight:900;color:#475569;}}
.cal-wd.sun{{color:#ef4444;}}.cal-wd.sat{{color:#3b82f6;}}
.cal-days{{display:grid;grid-template-columns:repeat(7,1fr);}}
.cc{{min-height:84px;border-right:1px solid #e2e8f0;border-bottom:1px solid #e2e8f0;
  padding:5px 6px;cursor:pointer;transition:background .12s;}}
.cc:hover{{background:#eff6ff;}}
.cc.other{{background:#f8fafc;}}.cc.other .dn{{color:#cbd5e1;}}
.cc.today .dn{{background:#1e5ba4;color:#fff;border-radius:50%;
  width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-weight:900;}}
.dn{{font-size:.82rem;font-weight:700;color:#1e293b;margin-bottom:3px;
  width:26px;height:26px;display:flex;align-items:center;justify-content:center;}}
.cc.sun .dn{{color:#ef4444;}}.cc.sat .dn{{color:#3b82f6;}}
.cc.today.sun .dn,.cc.today.sat .dn{{color:#fff;}}
.badges{{display:flex;flex-direction:column;gap:2px;}}
.badge{{display:block;border-radius:4px;padding:1px 5px;font-size:.68rem;font-weight:700;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;cursor:pointer;}}
.badge-consult{{background:#fee2e2;color:#b91c1c;border-left:3px solid #ef4444;}}
.badge-expiry{{background:#fff7ed;color:#c2410c;border-left:3px solid #f97316;}}
.badge-upsell{{background:#faf5ff;color:#6d28d9;border-left:3px solid #a855f7;}}
.badge-appointment{{background:#dbeafe;color:#1d4ed8;border-left:3px solid #3b82f6;}}
.badge-todo{{background:#fef9c3;color:#92400e;border-left:3px solid #f59e0b;}}
.badge-personal{{background:#f0fdf4;color:#166534;border-left:3px solid #22c55e;}}
.badge-more{{background:#f1f5f9;color:#64748b;border-left:3px solid #94a3b8;}}
</style></head><body>
<div class="cal-grid">
<div class="cal-wdays">
  <div class="cal-wd sun">일</div><div class="cal-wd">월</div>
  <div class="cal-wd">화</div><div class="cal-wd">수</div>
  <div class="cal-wd">목</div><div class="cal-wd">금</div>
  <div class="cal-wd sat">토</div>
</div>
<div class="cal-days" id="cal-days"></div>
</div>
<div style="font-size:.72rem;color:#94a3b8;padding:5px 4px;">
  💡 날짜 클릭 → 일정 추가 폼 활성화 | 배지 클릭 → 수정
</div>
<script>
var events   = {evs_json};
var catTags  = {cat_tags_json};
var today    = new Date();
var curYear  = {year}, curMonth = {month}-1;
function pad(n){{return n<10?'0'+n:''+n;}}
function renderCal(){{
  var tY=today.getFullYear(),tM=today.getMonth(),tD=today.getDate();
  var fd=new Date(curYear,curMonth,1).getDay();
  var dim=new Date(curYear,curMonth+1,0).getDate();
  var dip=new Date(curYear,curMonth,0).getDate();
  var el=document.getElementById('cal-days'); el.innerHTML='';
  function makeCell(y,m,d,other,isToday){{
    var rd=new Date(y,m,d),ry=rd.getFullYear(),rm=rd.getMonth(),rdd=rd.getDate(),dow=rd.getDay();
    var ds=ry+'-'+pad(rm+1)+'-'+pad(rdd);
    var cc=document.createElement('div'); cc.className='cc';
    if(other)cc.classList.add('other');
    if(isToday)cc.classList.add('today');
    if(dow===0)cc.classList.add('sun');
    if(dow===6)cc.classList.add('sat');
    cc.dataset.date=ds;
    cc.onclick=function(){{
      window.top.location.href=window.top.location.pathname+'?cal_date='+ds;
    }};
    var dn=document.createElement('div'); dn.className='dn'; dn.textContent=rdd; cc.appendChild(dn);
    var bw=document.createElement('div'); bw.className='badges';
    var de=events.filter(function(e){{return e.date===ds;}});
    de.slice(0,3).forEach(function(ev){{
      var b=document.createElement('span');
      b.className='badge badge-'+(ev.category||'consult');
      var icons={{consult:'🔴',expiry:'🟠',upsell:'🟣',appointment:'🔵',todo:'🟡',personal:'🟢'}};
      var tgs=(ev.body||'').match(/#\w+/g)||[];
      b.textContent=(icons[ev.category]||'⚪')+' '+ev.title+(tgs.length?' '+tgs.slice(0,2).join(' '):'');
      b.title=ev.body||'';
      bw.appendChild(b);
    }});
    if(de.length>3){{
      var m=document.createElement('span'); m.className='badge badge-more';
      m.textContent='+'+(de.length-3)+'개 더'; bw.appendChild(m);
    }}
    cc.appendChild(bw); return cc;
  }}
  for(var i=0;i<fd;i++)el.appendChild(makeCell(curYear,curMonth-1,dip-fd+1+i,true,false));
  for(var d=1;d<=dim;d++)el.appendChild(makeCell(curYear,curMonth,d,false,curYear===tY&&curMonth===tM&&d===tD));
  var tot=fd+dim,rem=tot%7===0?0:7-(tot%7);
  for(var d=1;d<=rem;d++)el.appendChild(makeCell(curYear,curMonth+1,d,true,false));
}}
renderCal();
</script></body></html>"""
