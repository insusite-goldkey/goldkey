"""
db_utils.py — Goldkey AI CRM/HQ 공통 데이터 레이어
HQ(app.py) 와 CRM(crm_app.py) 양쪽에서 동일하게 호출하는 데이터 통신 모듈.

Tables:
  gk_people       — 고객 마스터
  gk_schedules    — 일정
  gk_members      — 설계사 회원
  gk_crawl_status — 내보험다보여 크롤링 상태 (실시간 파이프라인)

캐싱: @st.cache_data(ttl=60) — Supabase 60초 캐시 적용
동기화: set_crawl_status()로 HQ↔CRM 실시간 파이프라인 상태 공유
"""
from __future__ import annotations

import uuid
import datetime
from typing import Optional, Any

# ── Supabase 클라이언트 (프로세스 내 싱글턴) ──────────────────────────────────
_SB_CLIENT: Any = None


def _get_sb() -> Any:
    """Supabase 클라이언트 lazy init (환경변수 자동 탐지)."""
    global _SB_CLIENT
    if _SB_CLIENT is not None:
        return _SB_CLIENT
    try:
        from shared_components import get_env_secret
        from supabase import create_client
        _url = get_env_secret("SUPABASE_URL", "")
        _key = get_env_secret(
            "SUPABASE_SERVICE_ROLE_KEY",
            get_env_secret("SUPABASE_KEY", ""),
        )
        if _url and _key:
            _SB_CLIENT = create_client(_url, _key)
    except Exception:
        pass
    return _SB_CLIENT


# ══════════════════════════════════════════════════════════════════════════════
# §1 고객 (gk_people)
# ══════════════════════════════════════════════════════════════════════════════

def load_customers(agent_id: str, query: str = "") -> list[dict]:
    """
    gk_people 조회 (담당 설계사 + 검색어 필터).
    @st.cache_data(ttl=60) 적용 — 호출 측에서 wrapping 필요.
    """
    sb = _get_sb()
    if not sb:
        return []
    try:
        q = sb.table("gk_people").select("*").eq("is_deleted", False)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        if query:
            q = q.ilike("name", f"%{query}%")
        q = q.order("management_tier").order("name")
        return (q.execute().data or [])[:200]
    except Exception:
        return []


def get_customer(person_id: str) -> Optional[dict]:
    """person_id 단건 조회."""
    sb = _get_sb()
    if not sb or not person_id:
        return None
    try:
        rows = (
            sb.table("gk_people")
            .select("*")
            .eq("person_id", person_id)
            .execute()
            .data or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def save_customer(data: dict, agent_id: str) -> bool:
    """고객 upsert — shared_components.customer_input_form() 위임."""
    try:
        from shared_components import customer_input_form
        customer_input_form(data, agent_id, _get_sb())
        return True
    except Exception:
        return False


def delete_customer(person_id: str) -> bool:
    """고객 소프트 삭제 (is_deleted=True)."""
    sb = _get_sb()
    if not sb:
        return False
    try:
        sb.table("gk_people").update({
            "is_deleted": True,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }).eq("person_id", person_id).execute()
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §2 일정 (gk_schedules)
# ══════════════════════════════════════════════════════════════════════════════

def load_schedules(agent_id: str, date: str) -> list[dict]:
    """특정 날짜 일정 조회 (JOIN gk_people.name)."""
    sb = _get_sb()
    if not sb:
        return []
    try:
        return (
            sb.table("gk_schedules")
            .select("*, gk_people(name)")
            .eq("is_deleted", False)
            .eq("agent_id", agent_id)
            .eq("date", date)
            .order("start_time")
            .execute()
            .data or []
        )
    except Exception:
        return []


def load_schedules_today(agent_id: str) -> list[dict]:
    """오늘 일정 조회."""
    return load_schedules(agent_id, datetime.date.today().isoformat())


def load_schedules_range(agent_id: str, start: str, end: str) -> list[dict]:
    """날짜 범위 일정 조회 (캘린더 월간 뷰용)."""
    sb = _get_sb()
    if not sb:
        return []
    try:
        return (
            sb.table("gk_schedules")
            .select("*, gk_people(name)")
            .eq("is_deleted", False)
            .eq("agent_id", agent_id)
            .gte("date", start)
            .lte("date", end)
            .order("date")
            .order("start_time")
            .execute()
            .data or []
        )
    except Exception:
        return []


def save_schedule(
    agent_id: str,
    title: str,
    date: str,
    start_time: str,
    memo: str = "",
    category: str = "consult",
    person_id: str = "",
    schedule_id: str = "",
) -> bool:
    """일정 INSERT 또는 UPDATE (schedule_id 있으면 upsert)."""
    sb = _get_sb()
    if not sb:
        return False
    now = datetime.datetime.utcnow().isoformat()
    payload: dict = {
        "agent_id":   agent_id,
        "title":      title,
        "date":       date,
        "start_time": start_time,
        "memo":       memo,
        "category":   category,
        "is_deleted": False,
        "updated_at": now,
    }
    if person_id:
        payload["person_id"] = person_id
    try:
        if schedule_id:
            payload["schedule_id"] = schedule_id
            sb.table("gk_schedules").upsert(payload).execute()
        else:
            payload["schedule_id"] = str(uuid.uuid4())
            payload["created_at"]  = now
            sb.table("gk_schedules").insert(payload).execute()
        return True
    except Exception:
        return False


def delete_schedule(schedule_id: str) -> bool:
    """일정 소프트 삭제."""
    sb = _get_sb()
    if not sb:
        return False
    try:
        sb.table("gk_schedules").update({
            "is_deleted": True,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }).eq("schedule_id", schedule_id).execute()
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §3 크롤링 상태 (gk_crawl_status) — HQ ↔ CRM 실시간 파이프라인
# ══════════════════════════════════════════════════════════════════════════════

def get_crawl_status(person_id: str) -> dict:
    """내보험다보여 크롤링 상태 최신 1건 조회."""
    sb = _get_sb()
    if not sb or not person_id:
        return {}
    try:
        rows = (
            sb.table("gk_crawl_status")
            .select("*")
            .eq("person_id", person_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data or []
        )
        return rows[0] if rows else {}
    except Exception:
        return {}


def set_crawl_status(
    person_id: str,
    agent_id: str,
    status: str,
    data: Optional[dict] = None,
) -> bool:
    """
    크롤링 상태 upsert.
    status: 'pending' | 'running' | 'done' | 'error'
    HQ에서 크롤링 시작 → CRM에서 상태 모니터링 가능.
    """
    sb = _get_sb()
    if not sb:
        return False
    try:
        payload: dict = {
            "person_id":  person_id,
            "agent_id":   agent_id,
            "status":     status,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }
        if data:
            import json as _j
            payload["raw_json"] = _j.dumps(data, ensure_ascii=False)
        sb.table("gk_crawl_status").upsert(
            payload, on_conflict="person_id"
        ).execute()
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §4 유연한 업데이트 (스키마 확장 방어)
# ══════════════════════════════════════════════════════════════════════════════

def flexible_upsert(table: str, data: dict, conflict_col: str = "id") -> bool:
    """
    [스키마 확장 방어] 새 필드가 들어와도 에러 없이 upsert.
    없는 컬럼은 Supabase PostgREST가 무시함.
    """
    sb = _get_sb()
    if not sb or not data:
        return False
    try:
        sb.table(table).upsert(data, on_conflict=conflict_col).execute()
        return True
    except Exception:
        return False
