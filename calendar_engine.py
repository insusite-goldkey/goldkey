"""
calendar_engine.py — 스마트 캘린더 & 글로벌 영업 파이프라인 엔진
[GP-CALENDAR] Goldkey AI Masters 2026
"""
import re, json, uuid, datetime, calendar as _cal_mod, urllib.parse
from typing import Optional
import streamlit as st

# [GP-STEP4] 석세스 캘린더 모듈 임포트
try:
    from success_calendar import (
        detect_stage_color,
        search_customers_by_name,
        render_customer_quick_link_selector,
        show_year_month_picker,
        get_agentic_recurrence_suggestion,
        render_success_calendar_guide
    )
    _SUCCESS_CAL_AVAILABLE = True
except ImportError:
    _SUCCESS_CAL_AVAILABLE = False

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
            for idx, ev in enumerate(today_evs):
                icon = _CATS.get(ev.get("category","consult"), ("⚪",))[0]
                tgs  = extract_tags(ev.get("memo",""))
                tbadges = "".join(
                    f'<span style="background:#e0f2fe;color:#0369a1;padding:1px 6px;'
                    f'border-radius:10px;font-size:.70rem;margin-left:3px;">{t}</span>' for t in tgs)
                
                _ec1, _ec2 = st.columns([3, 1])
                with _ec1:
                    st.markdown(
                        f"<div style='padding:3px 0;'>{icon} <b>{ev.get('title','')}</b> "
                        f"<span style='color:#64748b;font-size:.80rem;'>"
                        f"{ev.get('start_time','')}~{ev.get('end_time','')}</span>{tbadges}</div>",
                        unsafe_allow_html=True)
                with _ec2:
                    # [GP-STEP11 하이브리드] AI 전략 버튼
                    if st.button(
                        "🤖 AI",
                        key=f"ai_today_{idx}_{ev.get('schedule_id','')}",
                        help="AI 맞춤 작문 (⭐프로전용)",
                        use_container_width=True
                    ):
                        try:
                            from modules.calendar_ai_helper import check_pro_tier, render_pro_upsell_tooltip, render_ai_strategy_briefing
                            if check_pro_tier(agent_id):
                                # 프로: AI 기능 실행
                                customer_name = ev.get("customer_name", "") or (ev.get("gk_people") or {}).get("name", "") or ev.get("title", "고객")
                                render_ai_strategy_briefing(
                                    user_id=agent_id,
                                    customer_name=customer_name,
                                    event_date=ev.get("date", ""),
                                    event_type=_CATS.get(ev.get("category", "consult"), ("⚪", "일정"))[0],
                                    person_id=ev.get("person_id", "")
                                )
                            else:
                                # 베이직: 업셀링 팝업 (고객명 포함)
                                render_pro_upsell_tooltip("AI 맞춤 작문", customer_name=customer_name)
                        except Exception:
                            st.error("AI 기능을 불러올 수 없습니다.")
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
    
    # ── [GP-REFERRAL] 리워드 현황 바 (달력 위젯 하단) ──────────────────────────
    _render_referral_reward_bar(agent_id)

# ══ [5] 고객 타임라인 ════════════════════════════════════════════════════════
def _render_referral_reward_bar(agent_id: str) -> None:
    """
    [GP-REFERRAL] 리워드 현황 바 렌더링
    - 현재 크레딧 기반 무료 이용 기간 계산
    - 50코인(월 구독료) vs 100코인(소개 리워드) 대비 강조
    """
    if not agent_id:
        return
    
    try:
        sb = _get_sb()
        if not sb:
            return
        
        # gk_members에서 현재 크레딧 및 만기일 조회
        resp = sb.table("gk_members").select("current_credits, subscription_expires_at, referral_count").eq("user_id", agent_id).execute()
        if not resp.data:
            return
        
        member = resp.data[0]
        current_credits = member.get("current_credits", 0)
        expires_at = member.get("subscription_expires_at", "")
        referral_count = member.get("referral_count", 0)
        
        # 50코인 = 1개월, 현재 크레딧으로 추가 가능한 개월 수 계산
        months_from_credits = current_credits // 50
        
        # 만기일 계산
        if expires_at:
            try:
                expire_date = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00")).date()
                # 크레딧으로 추가 연장 가능한 날짜 계산
                from dateutil.relativedelta import relativedelta
                extended_date = expire_date + relativedelta(months=months_from_credits)
                expire_str = extended_date.strftime("%Y.%m.%d")
            except Exception:
                expire_str = "2026.12.31"
        else:
            expire_str = "2026.12.31"
        
        # 리워드 바 렌더링
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%);"
            f"border:1px dashed #f59e0b;border-radius:12px;padding:12px 16px;margin:12px 0 0;'>"
            f"<div style='font-size:0.88rem;font-weight:700;color:#92400e;margin-bottom:6px;'>"
            f"🎁 [리워드 현황] 현재 <span style='color:#dc2626;font-weight:900;'>{referral_count}명</span> 소개로 "
            f"<span style='color:#059669;font-weight:900;'>{expire_str}</span>까지 무료 이용 중!</div>"
            f"<div style='font-size:0.82rem;color:#78350f;line-height:1.6;'>"
            f"(월 구독료: <span style='background:#fee2e2;color:#dc2626;padding:2px 6px;border-radius:6px;font-weight:700;'>50🪙</span> | "
            f"'월 구독료 납부 신규' 1명 초대 시 <span style='background:#dcfce7;color:#059669;padding:2px 6px;border-radius:6px;font-weight:900;'>100🪙</span> 지급 "
            f"➔ 즉시 <span style='font-weight:900;color:#dc2626;'>2개월 추가 연장!</span>)</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    except Exception as e:
        # 에러 발생 시 조용히 무시 (리워드 바는 선택적 UI)
        pass


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
    
    # ── [GP-STEP11 하이브리드] AI 전략 브리핑 버튼 (프로 전용) ──────────────────
    try:
        from modules.calendar_ai_helper import render_ai_strategy_briefing
        if customer_name and evs:
            # 가장 가까운 미래 일정 찾기
            future_evs = sorted([e for e in evs if e.get("date","") >= today_str], key=lambda x:x.get("date",""))
            if future_evs:
                next_ev = future_evs[0]
                render_ai_strategy_briefing(
                    user_id=agent_id,
                    customer_name=customer_name,
                    event_date=next_ev.get("date", ""),
                    event_type=_CATS.get(next_ev.get("category", "consult"), ("⚪", "일정"))[0],
                    person_id=person_id
                )
    except Exception:
        pass
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

# ══ [6-A] 되풀이 날짜 생성기 ════════════════════════════════════════════════
def _gen_recur_dates(start_str: str, recur_type: str, interval: int,
                    end_type: str, end_date_str: str, count: int,
                    weekdays: list) -> list:
    """되풀이 날짜 목록 생성. weekdays: JS 기준 0=일~6=토"""
    import datetime as _dt
    dates: list = []
    try:
        cur = _dt.date.fromisoformat(start_str)
    except Exception:
        return dates
    interval = max(1, interval)
    if end_type == "date" and end_date_str:
        try:
            end_d = _dt.date.fromisoformat(end_date_str)
        except Exception:
            end_d = cur + _dt.timedelta(days=365)
    else:
        end_d = cur + _dt.timedelta(days=365)
    max_n = min(count, 365) if end_type == "count" else 365

    if recur_type == "daily":
        while cur <= end_d and len(dates) < max_n:
            dates.append(cur.isoformat())
            cur += _dt.timedelta(days=interval)

    elif recur_type == "weekly":
        if not weekdays:
            weekdays = [(cur.weekday() + 1) % 7]
        py_days = {(d - 1) % 7 for d in weekdays}
        week_start = cur - _dt.timedelta(days=cur.weekday())
        while week_start <= end_d and len(dates) < max_n:
            for offset in range(7):
                d = week_start + _dt.timedelta(days=offset)
                if d < cur or d > end_d:
                    continue
                if d.weekday() in py_days:
                    dates.append(d.isoformat())
                    if len(dates) >= max_n:
                        break
            week_start += _dt.timedelta(weeks=interval)

    elif recur_type == "monthly":
        while cur <= end_d and len(dates) < max_n:
            dates.append(cur.isoformat())
            m = cur.month + interval
            y = cur.year + (m - 1) // 12
            m = (m - 1) % 12 + 1
            leap = 1 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 0
            max_day = [31, 28+leap, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m-1]
            cur = _dt.date(y, m, min(cur.day, max_day))

    elif recur_type == "yearly":
        while cur <= end_d and len(dates) < max_n:
            dates.append(cur.isoformat())
            try:
                cur = _dt.date(cur.year + interval, cur.month, cur.day)
            except ValueError:
                cur = _dt.date(cur.year + interval, cur.month, 28)

    return dates


# ══ [6-B] 공휴일 · 월간 메모/TA 지원 함수 ════════════════════════════════════
_HOLIDAYS_KR: dict = {
    "01-01": "신정",  "03-01": "삼일절",  "05-05": "어린이날",
    "06-06": "현충일", "08-15": "광복절",  "10-03": "개천절",
    "10-09": "한글날", "12-25": "성탄절",
}
_HOLIDAYS_LUNAR: dict = {
    "2025-01-28": "설날연휴", "2025-01-29": "설날",      "2025-01-30": "설날연휴",
    "2025-05-05": "석가탄신일","2025-10-05": "추석연휴",  "2025-10-06": "추석",
    "2025-10-07": "추석연휴",
    "2026-02-16": "설날연휴", "2026-02-17": "설날",      "2026-02-18": "설날연휴",
    "2026-05-24": "석가탄신일","2026-09-24": "추석연휴",  "2026-09-25": "추석",
    "2026-09-26": "추석연휴",
}

def _get_holidays_for_month(year: int, month: int) -> dict:
    """해당 월의 공휴일 {DD: 이름} 반환"""
    m2 = f"{month:02d}"
    result: dict = {}
    for mmdd, name in _HOLIDAYS_KR.items():
        if mmdd.startswith(m2 + "-"):
            result[mmdd[3:]] = name
    prefix = f"{year:04d}-{m2}-"
    for ds, name in _HOLIDAYS_LUNAR.items():
        if ds.startswith(prefix):
            result[ds[8:]] = name
    return result

def cal_save_monthly_memo(agent_id: str, month_key: str, memo: str) -> None:
    """월간 메모 Supabase upsert (key: YYYY-MM)"""
    try:
        sb = _get_sb()
        if sb:
            sb.table("gk_monthly_memos").upsert(
                {"agent_id": agent_id, "month_key": month_key, "memo": memo},
                on_conflict="agent_id,month_key",
            ).execute()
    except Exception:
        pass

def cal_load_monthly_memo(agent_id: str, month_key: str) -> str:
    """월간 메모 로드"""
    try:
        sb = _get_sb()
        if sb:
            r = (sb.table("gk_monthly_memos").select("memo")
                 .eq("agent_id", agent_id).eq("month_key", month_key)
                 .maybe_single().execute())
            return ((r.data or {}).get("memo") or "") if r and r.data else ""
    except Exception:
        pass
    return ""

def cal_load_ta_list(agent_id: str, year: int, month: int) -> dict:
    """TA(콜) 리스트 — 생일자·보험만기·6개월 미접촉"""
    import datetime as _dt
    result: dict = {"birthday": [], "expiry": [], "no_contact": []}
    try:
        sb = _get_sb()
        if not sb:
            return result
        m2 = f"{month:02d}"
        bd = (sb.table("gk_people").select("name,birth_date,person_id")
              .eq("agent_id", agent_id).eq("is_deleted", False).execute())
        for p in (bd.data or []):
            b = p.get("birth_date", "") or ""
            if len(b) >= 7 and b[5:7] == m2:
                result["birthday"].append(p)
        last_day = _cal_mod.monthrange(year, month)[1]
        start = f"{year:04d}-{m2}-01"
        end   = f"{year:04d}-{m2}-{last_day:02d}"
        ex = (sb.table("gk_schedules").select("title,date,gk_people(name)")
              .eq("agent_id", agent_id).eq("category", "expiry")
              .gte("date", start).lte("date", end).execute())
        result["expiry"] = ex.data or []
        six_ago = (_dt.date.today() - _dt.timedelta(days=180)).isoformat()
        nc = (sb.table("gk_people").select("name,person_id,last_contact")
              .eq("agent_id", agent_id).eq("is_deleted", False)
              .not_.is_("last_contact", "null")
              .lt("last_contact", six_ago)
              .order("last_contact", desc=False).limit(8).execute())
        result["no_contact"] = nc.data or []
    except Exception:
        pass
    return result


# ══ [6] 스마트 캘린더 메인 ═══════════════════════════════════════════════════
def render_smart_calendar(agent_id: str, customers: list | None = None) -> None:
    customers = customers or []
    today = datetime.date.today()
    if "current_month" not in st.session_state:
        st.session_state["current_month"] = today.strftime("%Y-%m")
    cur_m = st.session_state["current_month"]
    try:
        year, month = int(cur_m[:4]), int(cur_m[5:7])
    except Exception:
        year, month = today.year, today.month
        st.session_state["current_month"] = today.strftime("%Y-%m")
    month_key = f"{year:04d}-{month:02d}"

    # JS 팝업 저장/삭제 → query_param 흡수
    _save_f = st.query_params.get("cal_save", "")
    _del_f  = st.query_params.get("cal_del",  "")
    if _save_f == "1":
        _p_title = st.query_params.get("cal_title", "")
        _p_date  = st.query_params.get("cal_date",  "")
        _p_stime = st.query_params.get("cal_stime", "09:00")
        _p_etime = st.query_params.get("cal_etime", "10:00")
        _p_cat   = st.query_params.get("cal_cat",   "consult")
        _p_memo  = st.query_params.get("cal_memo",  "")
        _p_sid   = st.query_params.get("cal_sid",   "")
        _p_recur  = st.query_params.get("cal_recur", "")
        if _p_title and _p_date:
            if _p_recur == "1":
                _r_type  = st.query_params.get("cal_recur_type",     "daily")
                _r_int   = max(1, int(st.query_params.get("cal_recur_int",  "1") or "1"))
                _r_end_t = st.query_params.get("cal_recur_end_type", "noend")
                _r_end_d = st.query_params.get("cal_recur_end_date", "")
                _r_cnt   = max(1, min(365, int(st.query_params.get("cal_recur_cnt", "10") or "10")))
                _r_days  = [int(x) for x in st.query_params.get("cal_recur_days","").split(",") if x.strip().isdigit()]
                for _d in _gen_recur_dates(_p_date, _r_type, _r_int, _r_end_t, _r_end_d, _r_cnt, _r_days):
                    cal_save(agent_id=agent_id, title=_p_title, body=_p_memo,
                             date=_d, start_time=_p_stime, end_time=_p_etime, category=_p_cat)
            else:
                cal_save(agent_id=agent_id, title=_p_title, body=_p_memo,
                         date=_p_date, start_time=_p_stime, end_time=_p_etime,
                         category=_p_cat, schedule_id=_p_sid)
        st.query_params.clear()
        st.rerun()
    if _del_f == "1":
        _p_sid = st.query_params.get("cal_sid", "")
        if _p_sid:
            cal_delete(_p_sid, agent_id=agent_id)
        st.query_params.clear()
        st.rerun()
    
    # [GP-NAV] 달력 팝업 → 고객 상세 화면 이동
    _nav_cust = st.query_params.get("cal_nav_customer", "")
    if _nav_cust == "1":
        _nav_pid = st.query_params.get("cal_nav_pid", "")
        if _nav_pid:
            st.session_state["crm_selected_pid"] = _nav_pid
            st.session_state["crm_spa_mode"] = "customer"
            st.session_state["crm_spa_screen"] = "contact"
        st.query_params.clear()
        st.rerun()

    # [Fix: WebSocket 세션 보존] query_param 방식 제거 — st.button 방식으로 대체

    # JS 날짜 클릭 → query_param 흡수 (구형 fallback)
    _qd = st.query_params.get("cal_date","")
    if _qd:
        st.session_state["_cal_sel_date"] = _qd
        st.query_params.clear()
        try:
            _qdate = datetime.date.fromisoformat(_qd)
            st.session_state["current_month"] = _qdate.strftime("%Y-%m")
            year, month = _qdate.year, _qdate.month
            month_key = f"{year:04d}-{month:02d}"
        except Exception:
            pass

    # [A] 태그 검색 바 — 전역 st.columns 스태킹 방지 CSS 포함
    st.markdown("""
<style>
/* ── 태블릿 세로 모드: st.columns 스태킹 방지 (480px 이상) ── */
@media (min-width:480px){
  [data-testid="stHorizontalBlock"]{
    flex-wrap:nowrap !important;
    flex-direction:row !important;
    align-items:stretch;
    gap:0.25rem !important;
  }
  [data-testid="column"]{
    min-width:0 !important;
    overflow:visible !important;
  }
}
/* 버튼 텍스트: 세로모드에서 자동 축소 + 잘림 방지 */
@media (min-width:480px) and (max-width:900px){
  [data-testid="stHorizontalBlock"] button{
    font-size:clamp(.82rem,2.2vw,1rem) !important;
    padding:6px 4px !important;
    white-space:nowrap !important;
    overflow:hidden !important;
    text-overflow:ellipsis !important;
  }
  [data-testid="stTextInputRootElement"]{
    min-width:0 !important;
  }
}
/* 달력 네비게이션 전역 버튼 크기 — 모든 해상도에서 1rem 이상 */
[data-testid="stHorizontalBlock"] button {
  font-size:1rem !important;
  font-weight:700 !important;
}
/* 달력 검색/네비게이션 행 — 모든 화면 크기에서 수평(row) 강제 유지 */
.gp-sw ~ div [data-testid="stHorizontalBlock"] {
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  align-items: center !important;
  gap: 0.25rem !important;
}
.gp-sw ~ div [data-testid="column"] {
  width: auto !important;
  flex: 1 1 auto !important;
  min-width: 0 !important;
  margin-bottom: 0 !important;
}
/* 480px 미만 폰: 버튼 글자 자동 축소 */
@media (max-width: 479px) {
  .gp-sw ~ div [data-testid="stHorizontalBlock"] button {
    font-size: clamp(0.7rem, 3.5vw, 0.9rem) !important;
    padding: 5px 4px !important;
    white-space: nowrap !important;
  }
}
/* 검색 버튼 스타일 */
.gp-sw ~ div [data-testid="column"]:last-child button {
  background:linear-gradient(135deg,#fce7f3,#fecdd3)!important;
  color:#9f1239!important;border:1.5px solid #fda4af!important;font-weight:700!important;}
.gp-sw ~ div [data-testid="column"]:last-child button:hover {
  background:linear-gradient(135deg,#fbcfe8,#fca5a5)!important;}
</style><span class='gp-sw'></span>""", unsafe_allow_html=True)
    st.markdown("<div style='font-size:1rem;font-weight:900;color:#374151;margin-bottom:4px;'>�️ 상담 일정 관리</div>", unsafe_allow_html=True)
    _cs1, _cs2 = st.columns([5,1])
    with _cs1:
        _tq = st.text_input("검색", label_visibility="collapsed",
                            placeholder="#암보험, #보험만기, 고객명 검색", key="cal_tag_search")
    with _cs2:
        _do_s = st.button("🔍 검색", key="cal_search_btn", use_container_width=True)
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

    # [GP-STEP4] 석세스 캘린더 가이드
    if _SUCCESS_CAL_AVAILABLE:
        render_success_calendar_guide()
    
    # ── 월 네비게이션: st.button (WebSocket 세션 보존 — href 링크 완전 제거)
    _nb1, _nb2, _nb3, _nb4 = st.columns([1, 1, 4, 1])
    with _nb1:
        if st.button("◀ 이전", key="cal_mo_prev_eng", use_container_width=True):
            _pm = month - 1; _py = year
            if _pm < 1: _py -= 1; _pm = 12
            st.session_state["current_month"] = f"{_py:04d}-{_pm:02d}"
            st.rerun()
    with _nb2:
        if st.button(f"📅 {today.month}/{today.day}", key="cal_mo_today_eng", use_container_width=True, help="오늘 날짜로 이동"):
            st.session_state["current_month"] = today.strftime("%Y-%m")
            st.rerun()
    with _nb3:
        # [GP-STEP4] 연도/월 선택 모달 버튼
        if _SUCCESS_CAL_AVAILABLE:
            if st.button(f"{year}년 {month}월", key="cal_year_month_picker", use_container_width=True, help="연도/월 빠른 이동"):
                show_year_month_picker(year, month)
        else:
            st.markdown(
                f"<div style='text-align:center;font-size:1.3rem;font-weight:900;"
                f"color:#1a3a5c;padding:8px 4px;white-space:nowrap;'>{year}년 {month}월</div>",
                unsafe_allow_html=True,
            )
    with _nb4:
        if st.button("다음 ▶", key="cal_mo_next_eng", use_container_width=True):
            _nm = month + 1; _ny = year
            if _nm > 12: _ny += 1; _nm = 1
            st.session_state["current_month"] = f"{_ny:04d}-{_nm:02d}"
            st.rerun()

    # DB 이벤트 로드 → JS에 주입
    _evs = cal_load_month(agent_id, year, month)
    # [GP-STEP4] 심리적 컬러 코딩 적용
    _evs_enhanced = []
    for e in _evs:
        ev_dict = {
            "schedule_id": e.get("schedule_id",""),
            "title":       e.get("title",""),
            "date":        e.get("date",""),
            "start_time":  e.get("start_time","09:00") or "09:00",
            "end_time":    e.get("end_time","10:00") or "10:00",
            "category":    e.get("category","consult") or "consult",
            "body":        e.get("memo",""),
            "customer":    e.get("customer_name") or (e.get("gk_people") or {}).get("name","") or "",
            "person_id":   e.get("person_id",""),
        }
        
        # 심리적 컬러 코딩 적용
        if _SUCCESS_CAL_AVAILABLE:
            color_info = detect_stage_color(
                title=e.get("title", ""),
                memo=e.get("memo", ""),
                category=e.get("category", "")
            )
            ev_dict["stage_color"] = color_info["color"]
            ev_dict["stage_border"] = color_info["border"]
            ev_dict["stage_name"] = color_info["stage_name"]
        
        _evs_enhanced.append(ev_dict)
    
    _evs_js = json.dumps(_evs_enhanced, ensure_ascii=False)
    _holidays    = _get_holidays_for_month(year, month)
    _holidays_js = json.dumps(_holidays, ensure_ascii=False)
    _cat_tags_js = json.dumps({k:v[1] for k,v in _CATS.items()}, ensure_ascii=False)

    # [B] JS 캘린더 (도트 기반 클린 UI) — 화수 기반 동적 높이
    import calendar as _cal_mod
    import streamlit.components.v1 as _cv1
    _first_wd, _days = _cal_mod.monthrange(year, month)
    _num_weeks = (_first_wd + _days + 6) // 7
    _cal_frame_h = 500 + (_num_weeks - 5) * 70
    _cv1.html(_build_cal_html(_evs_js, year, month, _cat_tags_js, _holidays_js), height=_cal_frame_h, scrolling=False)

    # ── 5:5 월간 전략 대시보드 (current_month 동기화)
    st.markdown("<div style='border-top:2px solid #EAEAEF;margin:8px 0 10px;'></div>", unsafe_allow_html=True)
    _ta = cal_load_ta_list(agent_id, year, month)
    _render_monthly_dashboard(agent_id, year, month, _ta)

    # ── 월간 영업 전략 메모장 (자동저장)
    _render_monthly_memo(agent_id, month_key)

    # [C] 일정 추가/편집 폼
    _render_event_form(agent_id, customers, year, month)


def _render_monthly_dashboard(agent_id: str, year: int, month: int, ta: dict) -> None:
    """5:5 월간 전략 대시보드 — 좌: 온도계 / 우: TA 리스트"""
    left, right = st.columns([1, 1], gap="medium")
    with left:
        st.markdown(
            f"<div style='font-size:1.02rem;font-weight:900;color:#1e3a8a;margin-bottom:10px;'>"
            f"📊 월간 활동 성과 온도계 — {year}년 {month}월</div>",
            unsafe_allow_html=True)
        try:
            sb = _get_sb()
            last_day = _cal_mod.monthrange(year, month)[1]
            start = f"{year:04d}-{month:02d}-01"
            end   = f"{year:04d}-{month:02d}-{last_day:02d}"
            rows = (sb.table("gk_schedules").select("category")
                    .eq("agent_id", agent_id).eq("is_deleted", False)
                    .gte("date", start).lte("date", end).execute()) if sb else None
            data = rows.data or [] if rows else []
        except Exception:
            data = []
        cnt: dict = {}
        for e in data:
            c = e.get("category", "")
            cnt[c] = cnt.get(c, 0) + 1
        items = [
            ("consult",     "🔴 상담일정",  20, "#a7f3d0"),
            ("upsell",      "🟣 업셀링",    10, "#e9d5ff"),
            ("appointment", "🔵 약속·미팅", 15, "#bfdbfe"),
            ("expiry",      "🟠 보험만기",   5, "#fed7aa"),
        ]
        for cat, lbl, tgt, col in items:
            n   = cnt.get(cat, 0)
            pct = min(100, int(n / tgt * 100)) if tgt > 0 else 0
            st.markdown(f"""<div style="margin-bottom:12px;">
  <div style="display:flex;justify-content:space-between;font-size:.78rem;font-weight:700;
    color:#374151;margin-bottom:4px;">
    <span>{lbl}</span><span style="color:#64748b;">{n}/{tgt}건 ({pct}%)</span>
  </div>
  <div style="background:#EAEAEF;border-radius:8px;height:16px;border:1px solid #d1d5db;overflow:hidden;">
    <div style="background:{col};width:{pct}%;height:100%;border-radius:8px;transition:width .4s ease;"></div>
  </div>
</div>""", unsafe_allow_html=True)
    with right:
        st.markdown(
            "<div style='font-size:1.02rem;font-weight:900;color:#1e3a8a;margin-bottom:10px;'>"
            "📞 월간 핵심 TA 리스트</div>",
            unsafe_allow_html=True)
        def _ta_row(emoji: str, name: str, badge: str, bg: str) -> str:
            return (
                f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'padding:5px 8px;border-radius:6px;background:#fff;'
                f'border:1px solid #EAEAEF;margin-bottom:4px;">'
                f'<span style="font-size:.8rem;font-weight:700;">{emoji} {name}</span>'
                f'<span style="background:{bg};padding:2px 8px;border-radius:10px;'
                f'font-size:.68rem;font-weight:700;">{badge}</span></div>'
            )
        any_ta = False
        for p in ta.get("birthday", [])[:4]:
            bd = p.get("birth_date", "")
            st.markdown(_ta_row("🎂", p.get("name",""), f"생일 {bd[5:] if bd else ''}", "#dbeafe"), unsafe_allow_html=True)
            any_ta = True
        for e in ta.get("expiry", [])[:4]:
            nm = (e.get("gk_people") or {}).get("name","") or e.get("title","")
            dt = e.get("date","")
            st.markdown(_ta_row("🟠", nm, f"만기 {dt[5:] if dt else ''}", "#fed7aa"), unsafe_allow_html=True)
            any_ta = True
        for p in ta.get("no_contact", [])[:3]:
            lc = p.get("last_contact","")
            st.markdown(_ta_row("❄️", p.get("name",""), f"미접촉 {lc[:7] if lc else '?'}", "#e0f2fe"), unsafe_allow_html=True)
            any_ta = True
        if not any_ta:
            st.markdown(
                "<div style='font-size:.8rem;color:#94a3b8;padding:12px;text-align:center;'>"
                "이달 핵심 TA 대상이 없습니다.</div>", unsafe_allow_html=True)
    st.markdown("""<style>
/* 대시보드 5:5 블록만 모바일 스태킹 (전역 충돌 방지를 위해 .gp-dash 클래스 스코프) */
.gp-dash-wrap { display:flex; flex-wrap:wrap; gap:1rem; }
.gp-dash-col  { flex:1; min-width:280px; }
@media(max-width:560px){
  .gp-dash-wrap { flex-direction:column; }
  .gp-dash-col  { min-width:100%; }
}
</style>""",
        unsafe_allow_html=True)


def _render_monthly_memo(agent_id: str, month_key: str) -> None:
    """파스텔 옐로우 월간 영업 전략 메모장 — on_change 자동저장"""
    mk = f"mmemo_{month_key}"
    if mk not in st.session_state:
        st.session_state[mk] = cal_load_monthly_memo(agent_id, month_key)
    def _on_change() -> None:
        cal_save_monthly_memo(agent_id, month_key, st.session_state[mk])
    st.markdown(
        f'<div style="display:inline-block;width:fit-content;max-width:100%;'
        f'background:#FFF8E1;border:1.5px solid #fde68a;border-radius:10px;'
        f'padding:8px 14px;margin:10px 0 4px;">'
        f'<span style="font-size:.82rem;font-weight:900;color:#92400e;">📝 월간 영업 전략 메모 — {month_key}'
        f'<span style="font-size:.7rem;font-weight:400;color:#a16207;margin-left:8px;">✅ 자동저장</span></span>'
        f'</div>',
        unsafe_allow_html=True)
    st.text_area(
        "월간메모", key=mk, label_visibility="collapsed",
        placeholder="이달의 영업 전략, 핵심 목표, 중요 이슈를 자유롭게 기록하세요...",
        height=100, on_change=_on_change)


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
        st.markdown("<div style='display:inline-block;width:fit-content;background:#FFF8E1;border:1px solid #fde68a;border-radius:6px;padding:3px 10px;font-size:.78rem;font-weight:700;color:#92400e;margin-bottom:4px;'>① 일정 분류 선택 → 해시태그 자동 입력</div>", unsafe_allow_html=True)
        _cat_default = edit_ev.get("category","consult") if edit_ev else "consult"
        _cat_idx = list(_CATS.keys()).index(_cat_default) if _cat_default in _CATS else 0
        _sel_cat = st.selectbox("일정 분류", options=list(_CATS.keys()),
                                format_func=lambda k: _CATS[k][0],
                                index=_cat_idx, key="cal_form_cat",
                                label_visibility="collapsed")
        # 빠른 해시태그 버튼 (오토-태깅 넛지)
        st.markdown("""
<style>
/* 카테고리 버튼 6개: 세로모드 텍스트 축약 */
@media (max-width:900px){
  div[data-testid="stHorizontalBlock"]:has(button[data-testid^="baseButton"]:nth-child(1)):has(button:nth-child(6)) button{
    font-size:clamp(.58rem,1.5vw,.8rem) !important;
    padding:4px 2px !important;
  }
}
</style>
<div style='font-size:.73rem;color:#6b7280;margin-bottom:3px;'>빠른 해시태그 삽입:</div>""",
            unsafe_allow_html=True)
        _cat_labels = {
            "consult":     ("🔴", "상담"),
            "expiry":      ("🟠", "만기"),
            "upsell":      ("🟣", "업셀"),
            "appointment": ("🔵", "약속"),
            "todo":        ("🟡", "할일"),
            "personal":    ("🟢", "개인"),
        }
        _tcols = st.columns(len(_CATS))
        for _ci, (_ck, _cv) in enumerate(_CATS.items()):
            with _tcols[_ci]:
                _lbl = _cat_labels.get(_ck, ("⚪", _cv[0][:2]))
                if st.button(f"{_lbl[0]}\n{_lbl[1]}", key=f"qtag_{_ck}", use_container_width=True, help=_cv[0]):
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

        # [GP-STEP4] 고객 퀵링크 (@) 자동완성
        _quick_selected = None
        if _SUCCESS_CAL_AVAILABLE:
            st.markdown("<div style='border-top:1px dashed #e2e8f0;margin:12px 0;'></div>", unsafe_allow_html=True)
            _quick_selected = render_customer_quick_link_selector(agent_id, key_prefix="cal_form")
        
        # 고객 연동
        _copts = ["— 선택 안 함 —"] + [c.get("name","") for c in customers if c.get("name")]
        _cdef  = edit_ev.get("customer_name","") if edit_ev else ""
        
        # 퀵링크로 선택된 고객이 있으면 자동 선택
        if _quick_selected:
            _cdef = _quick_selected.get("name", "")
            if _cdef not in _copts:
                _copts.append(_cdef)
        
        _cidx  = _copts.index(_cdef) if _cdef in _copts else 0
        _f_cust = st.selectbox("관련 고객", options=_copts, index=_cidx, key="cal_form_cust")
        _pid = ""
        
        # 퀵링크로 선택된 경우 person_id 사용
        if _quick_selected and _f_cust == _quick_selected.get("name", ""):
            _pid = _quick_selected.get("person_id", "")
        elif _f_cust and _f_cust != "— 선택 안 함 —":
            for c in customers:
                if c.get("name","") == _f_cust:
                    _pid = c.get("person_id","") or c.get("cust_id","")
                    break
        
        # [GP-STEP4] 에이젠틱 반복 일정 추천
        if _SUCCESS_CAL_AVAILABLE and _f_cust and _f_cust != "— 선택 안 함 —":
            # 고객의 현재 단계 조회 (gk_people.current_stage)
            try:
                sb = _get_sb()
                if sb and _pid:
                    person_data = sb.table("gk_people").select("current_stage").eq("person_id", _pid).maybe_single().execute()
                    if person_data and person_data.data:
                        current_stage = person_data.data.get("current_stage", 1)
                        suggestion = get_agentic_recurrence_suggestion(_f_cust, current_stage)
                        st.info(suggestion)
            except Exception:
                pass

        # 저장/ICS/삭제 — [GP-BTN] width:auto 파스텔 버튼 (full-width 제거)
        st.markdown("""
<style>
/* 캘린더 폼 버튼 — 파스텔 블루 + width:auto (화면 전체 채움 방지) */
[data-testid="stButton"] > button[kind="primaryFormSubmit"],
[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg,#dbeafe,#bfdbfe) !important;
  color: #1e3a8a !important; border: 1.5px solid #93c5fd !important;
  font-weight: 900 !important; width: auto !important;
}
</style>""", unsafe_allow_html=True)
        _b1, _b2, _b3 = st.columns([2,1,1])
        with _b1:
            _do_save = st.button("💾 저장", key="cal_form_save")
        with _b2:
            _do_ics = st.button("📥 ICS", key="cal_form_ics", help="스마트폰 캘린더 저장용 .ics 생성")
        with _b3:
            _do_del = st.button("🗑️ 삭제", key="cal_form_del") if edit_ev else False

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

# ══ [8] JS 캘린더 HTML 빌더 (Outlook 팝업 모달 포함) ════════════════════════
def _build_cal_html(evs_json: str, year: int, month: int, cat_tags_json: str, holidays_json: str = "{}") -> str:
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
.ev-dots{{display:flex;gap:3px;flex-wrap:wrap;align-items:center;margin-bottom:2px;}}
.ev-dot{{width:7px;height:7px;border-radius:50%;display:inline-block;cursor:pointer;flex-shrink:0;}}
.ev-kw{{font-size:.62rem;color:#475569;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;max-width:100%;line-height:1.3;cursor:pointer;display:block;}}
.ev-more{{font-size:.6rem;color:#94a3b8;cursor:pointer;display:block;}}
.cc.holiday .dn{{color:#ef4444!important;}}
.cc.today.holiday .dn{{color:#fff!important;}}
.hname{{font-size:.58rem;color:#ef4444;font-weight:700;line-height:1.2;margin-bottom:1px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;}}
/* ── Outlook 스타일 팝업 모달 ── */
#ev-modal-bg{{position:fixed;inset:0;background:rgba(15,23,42,0.48);z-index:9999;
  display:none;align-items:center;justify-content:center;padding:12px;}}
#ev-modal-bg.show{{display:flex;}}
.ev-modal{{background:#fff;border-radius:14px;width:100%;max-width:460px;
  box-shadow:0 12px 48px rgba(30,58,138,0.22);overflow:hidden;
  max-height:calc(100vh - 24px);display:flex;flex-direction:column;}}
.ev-mhdr{{background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);
  padding:13px 18px;display:flex;align-items:center;justify-content:space-between;
  border-bottom:1.5px solid #bfdbfe;flex-shrink:0;}}
.ev-mhdr-ttl{{font-size:.95rem;font-weight:900;color:#1e3a8a;}}
.ev-mclose{{background:none;border:none;font-size:1.1rem;cursor:pointer;
  color:#64748b;padding:3px 8px;border-radius:6px;line-height:1;}}
.ev-mclose:hover{{background:#e2e8f0;color:#1e293b;}}
.ev-mbody{{padding:16px 18px;overflow-y:auto;}}
.ev-lbl{{font-size:.74rem;font-weight:700;color:#374151;display:block;margin-bottom:3px;}}
.ev-inp{{width:100%;padding:8px 10px;border:1.5px solid #dbeafe;border-radius:7px;
  font-size:.87rem;font-family:inherit;outline:none;transition:border-color .15s;background:#fff;}}
.ev-inp:focus{{border-color:#3b82f6;box-shadow:0 0 0 3px rgba(59,130,246,.12);}}
.ev-row2{{display:grid;grid-template-columns:1fr 1fr;gap:10px;}}
.ev-mfooter{{display:flex;gap:8px;padding:0 18px 16px;flex-shrink:0;}}
.ev-btn-save{{flex:1;padding:10px 0;background:linear-gradient(135deg,#1e3a8a,#2563eb);
  color:#fff;border:none;border-radius:8px;font-size:.88rem;font-weight:700;cursor:pointer;font-family:inherit;}}
.ev-btn-save:hover{{background:linear-gradient(135deg,#1d4ed8,#3b82f6);}}
.ev-btn-del{{padding:10px 14px;background:#fee2e2;color:#b91c1c;
  border:1.5px solid #fca5a5;border-radius:8px;font-size:.88rem;font-weight:700;
  cursor:pointer;font-family:inherit;display:none;}}
.ev-btn-del:hover{{background:#fecaca;}}
.ev-btn-cancel{{flex:1;padding:10px 0;background:#f1f5f9;color:#475569;
  border:1.5px solid #e2e8f0;border-radius:8px;font-size:.88rem;font-weight:700;
  cursor:pointer;font-family:inherit;}}
.ev-btn-cancel:hover{{background:#e2e8f0;}}
/* ── 탭 ── */
.ev-tab{{flex:1;padding:10px 0;background:none;border:none;
  border-bottom:2.5px solid transparent;font-size:.85rem;font-weight:700;
  color:#94a3b8;cursor:pointer;font-family:inherit;transition:all .15s;}}
.ev-tab.ev-tab-active{{color:#1e3a8a;border-bottom-color:#1e3a8a;background:#fafcff;}}
.ev-tab:hover:not(.ev-tab-active){{color:#475569;background:#f8fafc;}}
/* ── 되풀이 패널 ── */
.rtype-btn{{flex:1;padding:7px 0;background:#f8fafc;border:1.5px solid #e2e8f0;
  border-radius:6px;font-size:.78rem;font-weight:700;color:#475569;
  cursor:pointer;font-family:inherit;transition:all .12s;}}
.rtype-btn.active{{background:#dbeafe;border-color:#93c5fd;color:#1d4ed8;}}
.day-btn{{width:34px;height:34px;border-radius:50%;border:1.5px solid #e2e8f0;
  background:#f8fafc;font-size:.75rem;font-weight:700;color:#475569;
  cursor:pointer;font-family:inherit;transition:all .12s;}}
.day-btn.active{{background:#dbeafe;border-color:#93c5fd;color:#1d4ed8;}}
</style></head><body>
<!-- ── Outlook 팝업 모달 (탭2: 일정 | 되풀이) ── -->
<div id="ev-modal-bg" onclick="if(event.target===this)closeModal()">
  <div class="ev-modal">
    <div class="ev-mhdr">
      <span class="ev-mhdr-ttl" id="modal-hdr">📅 일정 추가</span>
      <button class="ev-mclose" onclick="closeModal()">✕</button>
    </div>
    <!-- 탭 버튼 -->
    <div style="display:flex;border-bottom:2px solid #e2e8f0;flex-shrink:0;">
      <button id="tab-single" class="ev-tab ev-tab-active" onclick="switchTab('single')">📅 일정</button>
      <button id="tab-recur"  class="ev-tab" onclick="switchTab('recur')">🔄 되풀이 일정</button>
    </div>
    <!-- 탭1: 단일 일정 -->
    <div id="panel-single" class="ev-mbody">
      <div id="ev-customer-box" style="display:none;margin-bottom:10px;background:#f0f7ff;border-radius:8px;padding:8px 12px;">
        <label class="ev-lbl" style="margin-bottom:4px;">👤 고객</label>
        <div id="ev-customer-name" style="font-size:.9rem;font-weight:700;color:#1e3a8a;cursor:pointer;text-decoration:underline;"
          onclick="navigateToCustomer()"></div>
        <input type="hidden" id="ev-person-id" value="">
      </div>
      <div style="margin-bottom:10px;">
        <label class="ev-lbl">제목 *</label>
        <input id="ev-title" class="ev-inp" type="text" placeholder="일정 제목을 입력하세요">
      </div>
      <div class="ev-row2" style="margin-bottom:10px;">
        <div>
          <label class="ev-lbl">날짜</label>
          <input id="ev-date" class="ev-inp" type="date">
        </div>
        <div>
          <label class="ev-lbl">분류</label>
          <select id="ev-cat" class="ev-inp">
            <option value="consult">🔴 상담일정</option>
            <option value="expiry">🟠 보험만기</option>
            <option value="upsell">🟣 업셀링</option>
            <option value="appointment">🔵 약속</option>
            <option value="todo">🟡 할 일</option>
            <option value="personal">🟢 개인일정</option>
          </select>
        </div>
      </div>
      <div class="ev-row2" style="margin-bottom:10px;">
        <div>
          <label class="ev-lbl">시작 시간</label>
          <input id="ev-stime" class="ev-inp" type="time" value="09:00">
        </div>
        <div>
          <label class="ev-lbl">종료 시간</label>
          <input id="ev-etime" class="ev-inp" type="time" value="10:00">
        </div>
      </div>
      <div style="margin-bottom:4px;">
        <label class="ev-lbl">메모 / 해시태그</label>
        <textarea id="ev-memo" class="ev-inp" rows="3"
          placeholder="#암보험 #VIP 상담 내용..." style="resize:vertical;"></textarea>
      </div>
    </div>
    <!-- 탭2: 되풀이 일정 -->
    <div id="panel-recur" class="ev-mbody" style="display:none;">
      <div style="background:#f0f7ff;border-radius:8px;padding:8px 10px;margin-bottom:12px;font-size:.76rem;color:#1e3a8a;">
        ℹ️ 제목·분류·시간은 <b>📅 일정</b> 탭에서 설정한 값이 사용됩니다.
      </div>
      <!-- 되풀이 유형 -->
      <div style="margin-bottom:12px;">
        <label class="ev-lbl">되풀이 유형</label>
        <div style="display:flex;gap:6px;margin-top:5px;">
          <button id="rtype-daily"   class="rtype-btn active" onclick="setRecurType('daily'  )"> 매일</button>
          <button id="rtype-weekly"  class="rtype-btn"        onclick="setRecurType('weekly' )"> 매주</button>
          <button id="rtype-monthly" class="rtype-btn"        onclick="setRecurType('monthly')"> 매월</button>
          <button id="rtype-yearly"  class="rtype-btn"        onclick="setRecurType('yearly' )"> 매년</button>
        </div>
        <input type="hidden" id="recur-type" value="daily">
      </div>
      <!-- 간격 -->
      <div style="margin-bottom:12px;display:flex;align-items:center;gap:8px;">
        <label class="ev-lbl" style="margin-bottom:0;white-space:nowrap;">매</label>
        <input id="recur-int" class="ev-inp" type="number" min="1" max="99" value="1"
          style="width:64px;text-align:center;padding:6px 8px;">
        <span id="recur-int-unit" style="font-size:.84rem;font-weight:700;color:#374151;">일</span>
        <span style="font-size:.78rem;color:#64748b;">마다 반복</span>
      </div>
      <!-- 요일 선택 (매주) -->
      <div id="weekday-row" style="display:none;margin-bottom:12px;">
        <label class="ev-lbl">요일 선택</label>
        <div style="display:flex;gap:5px;margin-top:5px;">
          <button class="day-btn" data-dow="0" onclick="toggleDay(0)">일</button>
          <button class="day-btn" data-dow="1" onclick="toggleDay(1)">월</button>
          <button class="day-btn" data-dow="2" onclick="toggleDay(2)">화</button>
          <button class="day-btn" data-dow="3" onclick="toggleDay(3)">수</button>
          <button class="day-btn" data-dow="4" onclick="toggleDay(4)">목</button>
          <button class="day-btn" data-dow="5" onclick="toggleDay(5)">금</button>
          <button class="day-btn" data-dow="6" onclick="toggleDay(6)">토</button>
        </div>
      </div>
      <!-- 종료 조건 -->
      <div style="margin-bottom:8px;">
        <label class="ev-lbl">종료 조건</label>
        <div style="display:flex;flex-direction:column;gap:8px;margin-top:6px;">
          <label style="display:flex;align-items:center;gap:8px;font-size:.82rem;cursor:pointer;">
            <input type="radio" name="recur-end" value="noend" checked onchange="onEndChange('noend')">
            <span>종료일 없음 (1년 생성)</span>
          </label>
          <label style="display:flex;align-items:center;gap:8px;font-size:.82rem;cursor:pointer;">
            <input type="radio" name="recur-end" value="date" onchange="onEndChange('date')">
            <span>날짜 지정</span>
            <input id="recur-end-date" class="ev-inp" type="date"
              style="width:150px;display:none;padding:5px 8px;">
          </label>
          <label style="display:flex;align-items:center;gap:8px;font-size:.82rem;cursor:pointer;">
            <input type="radio" name="recur-end" value="count" onchange="onEndChange('count')">
            <span>반복 횟수</span>
            <input id="recur-cnt" class="ev-inp" type="number" min="1" max="365" value="10"
              style="width:64px;display:none;text-align:center;padding:5px 8px;">
            <span id="recur-cnt-lbl" style="display:none;font-size:.76rem;color:#64748b;">회</span>
          </label>
        </div>
      </div>
    </div>
    <div class="ev-mfooter">
      <button class="ev-btn-save" onclick="saveEvent()">💾 저장</button>
      <button class="ev-btn-del" id="ev-del-btn" onclick="deleteEvent()">🗑️ 삭제</button>
      <button class="ev-btn-cancel" onclick="closeModal()">취소</button>
    </div>
    <input type="hidden" id="ev-sid" value="">
  </div>
</div>
<!-- ── 달력 그리드 ── -->
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
  💡 날짜 클릭 → 일정 추가 | ● 점 클릭 → 일정 수정 | 공휴일은 적색 표시
</div>
<script>
var events   = {evs_json};
var catTags  = {cat_tags_json};
var holidays = {holidays_json};
var today    = new Date();
var curYear  = {year}, curMonth = {month}-1;
function pad(n){{return n<10?'0'+n:''+n;}}
function openModal(date){{
  document.getElementById('modal-hdr').textContent='📅 일정 추가 — '+date;
  document.getElementById('ev-title').value='';
  document.getElementById('ev-date').value=date;
  document.getElementById('ev-stime').value='09:00';
  document.getElementById('ev-etime').value='10:00';
  document.getElementById('ev-cat').value='consult';
  document.getElementById('ev-memo').value='';
  document.getElementById('ev-sid').value='';
  document.getElementById('ev-del-btn').style.display='none';
  document.getElementById('ev-modal-bg').classList.add('show');
  setTimeout(function(){{document.getElementById('ev-title').focus();}},80);
}}
function openEditModal(ev){{
  document.getElementById('modal-hdr').textContent='✏️ 일정 수정 — '+ev.date;
  document.getElementById('ev-title').value=ev.title||'';
  document.getElementById('ev-date').value=ev.date||'';
  document.getElementById('ev-stime').value=ev.start_time||'09:00';
  document.getElementById('ev-etime').value=ev.end_time||'10:00';
  document.getElementById('ev-cat').value=ev.category||'consult';
  document.getElementById('ev-memo').value=ev.body||'';
  document.getElementById('ev-sid').value=ev.schedule_id||'';
  document.getElementById('ev-del-btn').style.display=ev.schedule_id?'block':'none';
  var custName=ev.customer||'';
  var custPid=ev.person_id||'';
  if(custName&&custPid){{
    document.getElementById('ev-customer-box').style.display='block';
    document.getElementById('ev-customer-name').textContent=custName;
    document.getElementById('ev-person-id').value=custPid;
  }}else{{
    document.getElementById('ev-customer-box').style.display='none';
    document.getElementById('ev-person-id').value='';
  }}
  document.getElementById('ev-modal-bg').classList.add('show');
  setTimeout(function(){{document.getElementById('ev-title').focus();}},80);
}}
function closeModal(){{
  document.getElementById('ev-modal-bg').classList.remove('show');
  document.getElementById('ev-customer-box').style.display='none';
  document.getElementById('ev-person-id').value='';
  switchTab('single');
}}
function navigateToCustomer(){{
  var pid=document.getElementById('ev-person-id').value;
  if(!pid)return;
  var p=new URLSearchParams({{
    cal_nav_customer:'1',
    cal_nav_pid:pid
  }});
  window.top.location.href=window.top.location.pathname+'?'+p.toString();
}}
function switchTab(tab){{
  var isR=(tab==='recur');
  document.getElementById('tab-single').classList.toggle('ev-tab-active',!isR);
  document.getElementById('tab-recur').classList.toggle('ev-tab-active',isR);
  document.getElementById('panel-single').style.display=isR?'none':'block';
  document.getElementById('panel-recur').style.display=isR?'block':'none';
  var sid=document.getElementById('ev-sid').value;
  document.getElementById('ev-del-btn').style.display=(!isR&&sid)?'block':'none';
}}
var _rType='daily', _rDays=[];
function setRecurType(t){{
  _rType=t;
  document.getElementById('recur-type').value=t;
  ['daily','weekly','monthly','yearly'].forEach(function(k){{
    document.getElementById('rtype-'+k).classList.toggle('active',k===t);
  }});
  document.getElementById('weekday-row').style.display=(t==='weekly')?'block':'none';
  var u={{daily:'일',weekly:'주',monthly:'개월',yearly:'년'}};
  document.getElementById('recur-int-unit').textContent=u[t]||'일';
}}
function toggleDay(d){{
  var i=_rDays.indexOf(d);
  if(i>=0)_rDays.splice(i,1); else _rDays.push(d);
  document.querySelectorAll('.day-btn').forEach(function(b){{
    b.classList.toggle('active',_rDays.indexOf(parseInt(b.dataset.dow))>=0);
  }});
}}
function onEndChange(t){{
  document.getElementById('recur-end-date').style.display=(t==='date')?'inline-block':'none';
  document.getElementById('recur-cnt').style.display=(t==='count')?'inline-block':'none';
  document.getElementById('recur-cnt-lbl').style.display=(t==='count')?'inline':'none';
}}
function saveEvent(){{
  var title=document.getElementById('ev-title').value.trim();
  if(!title){{alert('일정 제목을 입력하세요.');return;}}
  var isR=(document.getElementById('panel-recur').style.display!=='none');
  var p=new URLSearchParams({{
    cal_save:'1',
    cal_title:title,
    cal_date:document.getElementById('ev-date').value,
    cal_stime:document.getElementById('ev-stime').value,
    cal_etime:document.getElementById('ev-etime').value,
    cal_cat:document.getElementById('ev-cat').value,
    cal_memo:document.getElementById('ev-memo').value,
    cal_sid:document.getElementById('ev-sid').value
  }});
  if(isR){{
    p.set('cal_recur','1');
    p.set('cal_recur_type',document.getElementById('recur-type').value||'daily');
    p.set('cal_recur_int',document.getElementById('recur-int').value||'1');
    var et=document.querySelector('input[name="recur-end"]:checked');
    var etv=et?et.value:'noend';
    p.set('cal_recur_end_type',etv);
    p.set('cal_recur_end_date',document.getElementById('recur-end-date').value||'');
    p.set('cal_recur_cnt',document.getElementById('recur-cnt').value||'10');
    if(_rDays.length>0)p.set('cal_recur_days',_rDays.join(','));
  }}
  window.top.location.href=window.top.location.pathname+'?'+p.toString();
}}
function deleteEvent(){{
  var sid=document.getElementById('ev-sid').value;
  if(!sid)return;
  if(!confirm('이 일정을 삭제하시겠습니까?'))return;
  var p=new URLSearchParams({{cal_del:'1',cal_sid:sid}});
  window.top.location.href=window.top.location.pathname+'?'+p.toString();
}}
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
    cc.onclick=function(e){{
      if(!e.target.classList.contains('ev-dot')&&!e.target.classList.contains('ev-kw')&&!e.target.classList.contains('ev-more'))
        openModal(ds);
    }};
    var dn=document.createElement('div'); dn.className='dn'; dn.textContent=rdd; cc.appendChild(dn);
    var hname=holidays[pad(rdd)]||'';
    if(hname&&!other){{cc.classList.add('holiday');
      var hl=document.createElement('div'); hl.className='hname'; hl.textContent=hname; cc.appendChild(hl);}}
    var bw=document.createElement('div');
    var de=events.filter(function(e){{return e.date===ds;}});
    var dotColors={{consult:'#ef4444',expiry:'#f97316',upsell:'#a855f7',
      appointment:'#3b82f6',todo:'#f59e0b',personal:'#22c55e'}};
    var dotRow=document.createElement('div'); dotRow.className='ev-dots';
    de.slice(0,5).forEach(function(ev){{
      var dot=document.createElement('span'); dot.className='ev-dot';
      dot.style.background=dotColors[ev.category]||'#94a3b8';
      dot.title=ev.title;
      dot.onclick=function(e){{e.stopPropagation();openEditModal(ev);}};
      dotRow.appendChild(dot);
    }});
    if(de.length>0){{
      bw.appendChild(dotRow);
      var kw=document.createElement('span'); kw.className='ev-kw';
      kw.textContent=de[0].title.substring(0,8)+(de[0].title.length>8?'\u2026':'');
      kw.onclick=function(e){{e.stopPropagation();openEditModal(de[0]);}};
      bw.appendChild(kw);
      if(de.length>1){{
        var more=document.createElement('span'); more.className='ev-more';
        more.textContent='+'+(de.length-1)+'건';
        more.onclick=function(e){{e.stopPropagation();openModal(ds);}};
        bw.appendChild(more);
      }}
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
