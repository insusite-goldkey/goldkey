"""
nba_engine.py — 선제적 영업 제안 (Next Best Action) 엔진
+ 심리 기반 지능형 프롬프트 분기
[GP-NBA] Goldkey AI Masters 2026

Pipeline:
  [1] DB 스캔  — 만기 30일 / 휴면 3개월 / 보장 공백 고위험 고객 자동 선별
  [2] 성향 분류 — Logical / Emotional (DB personality_type + 메모 키워드)
  [3] 콘텐츠 생성 — 카톡 템플릿 + AI 가이드 텍스트 (성향별 분기)
  [4] 위젯 렌더  — "🤖 AI 비서의 오늘 영업 제안" 카드 뉴스
"""
from __future__ import annotations
import datetime, re, json
from typing import Optional
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 상수
# ══════════════════════════════════════════════════════════════════════════════
_LOGICAL_KW   = ["수익","요율","퍼센트","%","비율","투자","수익률","데이터","통계","비교","분석","금리","이율"]
_EMOTIONAL_KW = ["가족","걱정","아이","남편","아내","부모","안심","보호","사랑","미래","자녀","노후","건강"]

_NBA_TYPES = {
    "expiry":  ("🟠 보험 만기 임박", "#f97316"),
    "dormant": ("😴 휴면 고객 재접촉", "#6366f1"),
    "gap":     ("⚠️ 보장 공백 고위험", "#ef4444"),
}

# ══════════════════════════════════════════════════════════════════════════════
# [2] DB 스캔 함수
# ══════════════════════════════════════════════════════════════════════════════
def _get_sb():
    try:
        from db_utils import _get_sb as _sb
        return _sb()
    except Exception:
        return None


def scan_expiry_soon(agent_id: str, days: int = 30) -> list[dict]:
    """만기 30일 이내 고객 — gk_schedules #보험만기 태그 + 자동갱신월 임박."""
    today     = datetime.date.today()
    threshold = (today + datetime.timedelta(days=days)).isoformat()
    today_str = today.isoformat()
    results   = []
    sb = _get_sb()
    if sb:
        try:
            rows = (
                sb.table("gk_schedules").select("*, gk_people(name,memo,personality_type)")
                .eq("is_deleted", False).eq("agent_id", agent_id)
                .ilike("memo", "%#보험만기%")
                .gte("date", today_str).lte("date", threshold)
                .order("date").limit(10).execute().data or []
            )
            for r in rows:
                p = r.get("gk_people") or {}
                d_str = r.get("date","")
                try:
                    dl = (datetime.date.fromisoformat(d_str) - today).days
                except Exception:
                    dl = 0
                results.append({
                    "nba_type":    "expiry",
                    "person_id":   r.get("person_id",""),
                    "name":        p.get("name","") or r.get("customer_name",""),
                    "memo":        p.get("memo",""),
                    "personality_type": p.get("personality_type",""),
                    "detail":      f"만기 {dl}일 후 ({d_str})",
                    "schedule_id": r.get("schedule_id",""),
                })
        except Exception:
            pass
    return results


def scan_dormant_customers(agent_id: str, months: int = 3) -> list[dict]:
    """3개월간 소통 없는 휴면 고객 자동 감지."""
    cutoff = (datetime.date.today() - datetime.timedelta(days=months * 30)).isoformat()
    results = []
    sb = _get_sb()
    if sb:
        try:
            # 고객 목록에서 최근 일정이 cutoff 이전인 고객 찾기
            # gk_people 조회 후 gk_schedules MAX(date) 로 비교
            people = (
                sb.table("gk_people").select("person_id,name,memo,personality_type,management_tier")
                .eq("is_deleted", False).eq("agent_id", agent_id)
                .in_("management_tier", [1, 2])   # 관리 등급 1·2 우선
                .limit(100).execute().data or []
            )
            for p in people:
                pid = p.get("person_id","")
                if not pid:
                    continue
                scheds = (
                    sb.table("gk_schedules").select("date")
                    .eq("is_deleted", False).eq("agent_id", agent_id)
                    .eq("person_id", pid)
                    .order("date", desc=True).limit(1)
                    .execute().data or []
                )
                last_date = scheds[0]["date"] if scheds else ""
                if last_date < cutoff:
                    dormant_days = ""
                    if last_date:
                        try:
                            dd = (datetime.date.today() - datetime.date.fromisoformat(last_date)).days
                            dormant_days = f"{dd}일 째 소통 없음"
                        except Exception:
                            dormant_days = "오래 전"
                    else:
                        dormant_days = "기록 없음"
                    results.append({
                        "nba_type":    "dormant",
                        "person_id":   pid,
                        "name":        p.get("name",""),
                        "memo":        p.get("memo",""),
                        "personality_type": p.get("personality_type",""),
                        "detail":      dormant_days,
                        "last_date":   last_date,
                    })
                if len(results) >= 5:
                    break
        except Exception:
            pass
    return results


def scan_high_risk_gap(agent_id: str) -> list[dict]:
    """보장 공백 고위험 — management_tier=1 + 상태 미완료 고객."""
    results = []
    sb = _get_sb()
    if sb:
        try:
            rows = (
                sb.table("gk_people").select("person_id,name,memo,personality_type,management_tier,status")
                .eq("is_deleted", False).eq("agent_id", agent_id)
                .eq("management_tier", 1)
                .neq("status", "contracted")
                .order("name").limit(5).execute().data or []
            )
            for r in rows:
                results.append({
                    "nba_type":    "gap",
                    "person_id":   r.get("person_id",""),
                    "name":        r.get("name",""),
                    "memo":        r.get("memo",""),
                    "personality_type": r.get("personality_type",""),
                    "detail":      "가처분 소득 대비 보장 공백 고위험",
                })
        except Exception:
            pass
    return results


def get_all_nba_actions(agent_id: str) -> list[dict]:
    """NBA 전체 스캔 — 세션 캐시(TTL 5분) 적용."""
    cache_key = f"_nba_cache_{agent_id}"
    cache_ts  = f"_nba_cache_ts_{agent_id}"
    now       = datetime.datetime.now()
    cached    = st.session_state.get(cache_key)
    cached_at = st.session_state.get(cache_ts)
    if cached and cached_at and (now - cached_at).seconds < 300:
        return cached

    actions = []
    actions += scan_expiry_soon(agent_id)
    actions += scan_dormant_customers(agent_id)
    actions += scan_high_risk_gap(agent_id)

    # 중복 제거 (동일 person_id)
    seen, unique = set(), []
    for a in actions:
        if a["person_id"] not in seen:
            seen.add(a["person_id"])
            unique.append(a)

    st.session_state[cache_key] = unique
    st.session_state[cache_ts]  = now
    return unique


# ══════════════════════════════════════════════════════════════════════════════
# [3] 성향 분류
# ══════════════════════════════════════════════════════════════════════════════
def classify_personality(customer: dict) -> str:
    """
    고객 성향 분류: 'Logical' 또는 'Emotional'.
    1순위: personality_type 컬럼값
    2순위: memo 키워드 스코어링
    """
    ptype = (customer.get("personality_type") or "").lower()
    if any(x in ptype for x in ["logical","논리","data","분석형"]):
        return "Logical"
    if any(x in ptype for x in ["emotional","감성","감정","공감형"]):
        return "Emotional"

    memo = (customer.get("memo") or "").lower()
    ls = sum(1 for kw in _LOGICAL_KW if kw in memo)
    es = sum(1 for kw in _EMOTIONAL_KW if kw in memo)
    return "Logical" if ls > es else "Emotional"


# ══════════════════════════════════════════════════════════════════════════════
# [4] 콘텐츠 생성
# ══════════════════════════════════════════════════════════════════════════════
_KAKAO_TMPL = {
    "expiry": {
        "Logical": (
            "[{name}님 보험 만기 사전 안내]\n\n"
            "안녕하세요, Goldkey 설계사입니다.\n"
            "{name}님의 보험 계약이 {detail}에 예정되어 있습니다.\n\n"
            "📊 현재 보장 vs. 2026 트리니티 기준 필요 보장을 정밀 비교해 드릴게요.\n"
            "• 건강보험료 기반 가처분 소득 역산 완료\n"
            "• 만기 후 공백 구간 최소화 설계 준비됨\n\n"
            "⏰ 만기 전 반드시 상담을 권드립니다. 편하신 시간 알려 주세요."
        ),
        "Emotional": (
            "[{name}님께 드리는 소중한 알림 💙]\n\n"
            "안녕하세요, {name}님! Goldkey 설계사입니다.\n"
            "{name}님의 소중한 보험이 {detail}에 만기를 맞이합니다.\n\n"
            "💛 보험은 가족을 지키는 든든한 약속이잖아요.\n"
            "만기 후 공백 없이 {name}님 가족의 미래를 이어갈 수 있도록\n"
            "함께 준비해 드리고 싶습니다.\n\n"
            "잠깐만 시간 내주시면 제가 모두 챙겨 드릴게요 🙏"
        ),
    },
    "dormant": {
        "Logical": (
            "[{name}님, 보장 점검 안내]\n\n"
            "안녕하세요, Goldkey 설계사입니다.\n"
            "최근 {detail}으로 연락이 뜸했던 점 양해 부탁드립니다.\n\n"
            "📈 2026년 건강보험료율 개정(7.19%)으로 기존 설계 대비\n"
            "약 8~12% 보장 공백이 발생할 수 있습니다.\n"
            "무료 정밀 진단 한 번 받아 보시겠어요?"
        ),
        "Emotional": (
            "[{name}님, 오랜만이에요 😊]\n\n"
            "안녕하세요, {name}님! 잘 지내고 계셨나요?\n"
            "{detail}이라 제가 더 자주 연락드렸어야 했는데 미안해요.\n\n"
            "❤️ 항상 {name}님과 가족분들이 건강하고 행복하길 바라고 있어요.\n"
            "잠깐 근황도 나누고, 혹시 필요한 게 있는지 여쭤봐도 될까요?"
        ),
    },
    "gap": {
        "Logical": (
            "[{name}님 보장 공백 정밀 진단 안내]\n\n"
            "안녕하세요, Goldkey 설계사입니다.\n\n"
            "🔍 AI 분석 결과: {name}님의 현재 가입 보장이\n"
            "2026 트리니티 기준 필요 자금 대비 3배 이상 공백이 감지되었습니다.\n\n"
            "📊 암 진단 필요 자금 / 후유장해 소득 대체액 / 일당 분석 완료.\n"
            "상세 리포트 공유해 드릴게요 — 10분이면 충분합니다."
        ),
        "Emotional": (
            "[{name}님을 위한 맞춤 상담 안내 💝]\n\n"
            "안녕하세요, {name}님!\n\n"
            "❤️ 혹시 '내 보험이 충분한가?' 걱정되신 적 있으신가요?\n"
            "{name}님처럼 소중한 분일수록 만약을 대비한 준비가 필요해요.\n\n"
            "AI가 {name}님만을 위한 보장 분석을 마쳤습니다.\n"
            "가족을 위한 10분 투자, 함께해 주시겠어요? 🙏"
        ),
    },
}


def generate_kakao_template(action: dict) -> str:
    """성향에 맞는 카카오톡 전송 템플릿 생성."""
    nba_type = action.get("nba_type","gap")
    ptype    = classify_personality(action)
    tmpl     = _KAKAO_TMPL.get(nba_type, _KAKAO_TMPL["gap"]).get(ptype, "")
    return tmpl.format(
        name   = action.get("name","고객"),
        detail = action.get("detail",""),
    )


def generate_ai_guide_text(action: dict, personality_type: str) -> str:
    """
    성향별 AI 브리핑 가이드 텍스트.
    Logical  → 데이터·수치 중심 보고서형
    Emotional → 가치·안심 중심 다정한 편지형
    """
    name     = action.get("name","고객")
    nba_type = action.get("nba_type","gap")
    detail   = action.get("detail","")
    today    = datetime.date.today().strftime("%Y년 %m월 %d일")

    if personality_type == "Logical":
        return (
            f"## [{today}] {name}님 — 논리형 영업 가이드\n\n"
            f"**판단 근거**: {_NBA_TYPES.get(nba_type,('분석',''))[0]} — {detail}\n\n"
            f"**접근 전략**: 수치와 데이터 제시 → 트리니티 역산 → 보장 공백 시각화\n"
            f"- 건강보험료 기반 가처분 소득 역산 (2026 개정 요율 7.19% 적용)\n"
            f"- 암 진단 필요 자금 / 후유장해 소득대체 / 일당 환산 수치 제시\n"
            f"- '데이터가 말해주는 결론'으로 클로징\n\n"
            f"**추천 오프닝 멘트**:\n"
            f"> \"{name}님, 제가 건강보험료를 기반으로 정밀 역산한 결과,\n"
            f"  현재 보장 대비 필요 자금의 약 {_gap_pct(nba_type)}%가 비어 있습니다.\n"
            f"  수치로 보여드릴게요.\"\n\n"
            f"**추천 클로징**:\n"
            f"> \"데이터는 명확합니다. 지금 결정하시면 {name}님의 리스크 지수가\n"
            f"  즉시 최적화됩니다.\""
        )
    else:
        return (
            f"## [{today}] {name}님 — 감성형 영업 가이드\n\n"
            f"**판단 근거**: {_NBA_TYPES.get(nba_type,('분석',''))[0]} — {detail}\n\n"
            f"**접근 전략**: 공감 → 가족의 미래 스토리 → 안심과 사랑의 언어로 클로징\n"
            f"- 고객의 걱정에 먼저 공감하는 오프닝\n"
            f"- 보험을 '가족을 위한 사랑의 약속'으로 프레이밍\n"
            f"- '선물'과 '안심'의 언어로 마무리\n\n"
            f"**추천 오프닝 멘트**:\n"
            f"> \"{name}님, 혹시 밤에 '내 가족에게 무슨 일이 생기면 어쩌지?' 하고\n"
            f"  걱정해본 적 있으세요? 저도 그래서 이 일을 합니다.\"\n\n"
            f"**추천 클로징**:\n"
            f"> \"{name}님이 오늘 결정해 주시면, 그 마음이 가족에게\n"
            f"  가장 든든한 선물이 됩니다. 제가 끝까지 함께할게요.\""
        )


def _gap_pct(nba_type: str) -> int:
    return {"expiry": 45, "dormant": 38, "gap": 67}.get(nba_type, 50)


# ══════════════════════════════════════════════════════════════════════════════
# [5] NBA 위젯 렌더러
# ══════════════════════════════════════════════════════════════════════════════
def render_nba_widget(agent_id: str) -> None:
    """
    대시보드 최상단 — 🤖 AI 비서의 오늘 영업 제안 카드 뉴스.
    데이터 없으면 렌더링 생략.
    """
    if not agent_id:
        return

    actions = get_all_nba_actions(agent_id)
    if not actions:
        return

    st.markdown(
        "<div style='background:linear-gradient(135deg,#1e3a5c,#1e5ba4);border-radius:14px;"
        "padding:14px 20px 10px;margin-bottom:12px;'>"
        "<div style='color:#fff;font-size:1.0rem;font-weight:900;letter-spacing:0.04em;'>"
        "🤖 AI 비서의 오늘 영업 제안</div>"
        "<div style='color:#94c4f5;font-size:0.76rem;margin-top:2px;'>"
        "만기 임박 · 휴면 재접촉 · 보장 공백 고위험 고객 자동 선별</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    for idx, action in enumerate(actions[:5]):
        nba_type  = action.get("nba_type","gap")
        name      = action.get("name","고객")
        detail    = action.get("detail","")
        label, color = _NBA_TYPES.get(nba_type, ("분석", "#64748b"))
        ptype     = classify_personality(action)
        picon     = "⚖️" if ptype == "Logical" else "❤️"
        p_label   = "논리형" if ptype == "Logical" else "감성형"

        with st.container():
            st.markdown(
                f"<div style='background:#fff;border:1.5px solid #e2e8f0;border-left:4px solid {color};"
                f"border-radius:10px;padding:12px 16px;margin-bottom:8px;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<div>"
                f"<span style='background:{color};color:#fff;padding:2px 8px;border-radius:6px;"
                f"font-size:0.72rem;font-weight:700;'>{label}</span>"
                f"<span style='font-size:0.88rem;font-weight:900;color:#1e293b;margin-left:8px;'>{name}</span>"
                f"<span style='font-size:0.75rem;color:#64748b;margin-left:6px;'>{detail}</span>"
                f"</div>"
                f"<span style='background:#f1f5f9;padding:2px 8px;border-radius:8px;"
                f"font-size:0.72rem;color:#475569;font-weight:700;'>{picon} {p_label}</span>"
                f"</div></div>",
                unsafe_allow_html=True,
            )

            _c1, _c2, _c3 = st.columns([2, 2, 1])
            with _c1:
                if st.button(
                    "📋 AI 가이드", key=f"nba_guide_{idx}",
                    use_container_width=True, help="성향별 영업 가이드 생성",
                ):
                    st.session_state[f"_nba_guide_{idx}"] = True

            with _c2:
                if st.button(
                    "📤 카톡 템플릿", key=f"nba_kakao_{idx}",
                    use_container_width=True, help="카카오톡 전송 템플릿 복사",
                ):
                    st.session_state[f"_nba_kakao_{idx}"] = True

            with _c3:
                if action.get("person_id"):
                    if st.button("🔍 고객", key=f"nba_cust_{idx}", use_container_width=True):
                        st.session_state["_customer_detail_id"] = action["person_id"]

            # AI 가이드 팝업
            if st.session_state.get(f"_nba_guide_{idx}"):
                guide = generate_ai_guide_text(action, ptype)
                st.markdown(guide)
                # 보이스 엔진 연동
                try:
                    from voice_engine import render_voice_player as _rvp
                    _rvp(guide, ptype, key=f"nba_voice_{idx}")
                except Exception:
                    pass
                if st.button("닫기", key=f"nba_guide_close_{idx}"):
                    del st.session_state[f"_nba_guide_{idx}"]
                    st.rerun()

            # 카톡 템플릿 팝업
            if st.session_state.get(f"_nba_kakao_{idx}"):
                tmpl = generate_kakao_template(action)
                st.text_area(
                    "카카오톡 전송용 메시지 (전체 선택 후 복사)",
                    value=tmpl, height=180,
                    key=f"nba_tmpl_ta_{idx}",
                )
                import urllib.parse as _up
                _kurl = "kakaotalk://send?text=" + _up.quote(tmpl)
                st.markdown(
                    f'<a href="{_kurl}" target="_blank" style="text-decoration:none;">'
                    f'<div style="background:#FEE500;color:#000;padding:9px;border-radius:8px;'
                    f'text-align:center;font-weight:900;font-size:.88rem;">'
                    f'📤 카카오톡으로 전송</div></a>',
                    unsafe_allow_html=True,
                )
                if st.button("닫기", key=f"nba_kakao_close_{idx}"):
                    del st.session_state[f"_nba_kakao_{idx}"]
                    st.rerun()

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
