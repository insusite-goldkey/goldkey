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


# ══════════════════════════════════════════════════════════════════════════════
# §5 스키마 안전 고객 업데이트 — 신규 필드 무중단 확장
# ══════════════════════════════════════════════════════════════════════════════

# 한국어 입력키 → DB 컬럼 매핑 (신규 필드는 여기에만 추가)
_FIELD_MAP: dict[str, str] = {
    "직업급수":    "job_grade",
    "운전형태":    "driving_type",
    "이륜차여부":  "bike_usage",
    "주소":        "address_detail",
    "소개자":      "referrer_name",
    "이름":        "name",
    "성별":        "gender",
    "생년월일":    "birth_date",
    "직업":        "job",
    "관리등급":    "management_tier",
    "상담상태":    "status",
    "이륜차소유":  "has_motorcycle",
    "유상운송":    "is_commercial_driver",
    "해외체류":    "has_foreign_stay",
    "자동차만기월": "auto_renewal_month",
    "화재만기월":  "fire_renewal_month",
    "메모":        "memo",
}

# DB 컬럼 기본값 — 새 필드 추가 시 None이어도 시스템 안전
_COLUMN_DEFAULTS: dict[str, Any] = {
    "job_grade":       "1급",
    "driving_type":    "자가용",
    "bike_usage":      "해당없음",
    "address_detail":  "",
    "referrer_name":   "",
    "has_motorcycle":  False,
    "is_commercial_driver": False,
    "has_foreign_stay": False,
    "auto_renewal_month": None,
    "fire_renewal_month": None,
    "management_tier": 3,
    "status":          "potential",
    "memo":            "",
}


def safe_update_customer(
    person_id: str,
    new_data: dict,
    agent_id: str = "",
) -> bool:
    """
    [무중단 스키마 확장] 기존 데이터를 유지하며 신규/변경 필드만 안전하게 업데이트.

    - 한국어 키(직업급수, 운전형태 등)와 영어 DB 컬럼 키 모두 허용
    - 없는 컬럼은 dict.get() 기본값으로 방어
    - 기존 데이터 None 필드 시스템 안전 (터지지 않음)
    """
    sb = _get_sb()
    if not sb or not person_id:
        return False

    payload: dict = {"updated_at": datetime.datetime.utcnow().isoformat()}

    for raw_key, value in new_data.items():
        db_col = _FIELD_MAP.get(raw_key, raw_key)
        default = _COLUMN_DEFAULTS.get(db_col)
        payload[db_col] = value if value is not None else default

    if agent_id:
        payload["agent_id"] = agent_id

    try:
        sb.table("gk_people").update(payload).eq("person_id", person_id).execute()
        return True
    except Exception:
        return False


def get_or_create_customer(
    agent_id: str,
    name: str,
    extra: Optional[dict] = None,
) -> dict:
    """
    이름으로 고객 조회, 없으면 신규 생성 후 반환.
    스키마 안전: extra 딕셔너리는 safe_update_customer 로직 경유.
    """
    sb = _get_sb()
    if not sb:
        return {}

    try:
        rows = (
            sb.table("gk_people")
            .select("*")
            .eq("agent_id", agent_id)
            .eq("name", name)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
            .data or []
        )
        if rows:
            cust = rows[0]
        else:
            import uuid as _uuid
            now = datetime.datetime.utcnow().isoformat()
            pid = str(_uuid.uuid4())
            base: dict = {
                "person_id":  pid,
                "agent_id":   agent_id,
                "name":       name,
                "is_deleted": False,
                "created_at": now,
                "updated_at": now,
            }
            sb.table("gk_people").insert(base).execute()
            cust = base

        if extra:
            safe_update_customer(
                cust.get("person_id", ""),
                extra,
                agent_id,
            )
            cust.update(extra)

        return cust
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# §6 상담일지 (gk_consulting_logs) — AI 브리핑 JSON + 카카오 발송 로그
# ══════════════════════════════════════════════════════════════════════════════

def log_consulting(
    agent_id: str,
    person_id: str,
    log_type: str,
    content: str = "",
    ai_briefing_json: Optional[dict] = None,
) -> bool:
    """
    상담일지 기록.
    log_type: 'ai_brief' | 'kakao_sent' | 'nibo' | 'manual' | 'schedule'
    ai_briefing_json: AI 분석 결과 원본 JSONB 저장 (consulting_logs.ai_briefing_json)
    """
    sb = _get_sb()
    if not sb:
        return False
    try:
        import json as _j
        import uuid as _uuid
        now = datetime.datetime.utcnow().isoformat()
        payload: dict = {
            "log_id":    str(_uuid.uuid4()),
            "agent_id":  agent_id,
            "person_id": person_id,
            "log_type":  log_type,
            "content":   content,
            "created_at": now,
        }
        if ai_briefing_json:
            payload["ai_briefing_json"] = _j.dumps(
                ai_briefing_json, ensure_ascii=False
            )
        sb.table("gk_consulting_logs").insert(payload).execute()
        return True
    except Exception:
        return False


def log_kakao_sent(
    agent_id: str,
    person_id: str,
    customer_name: str,
    template_id: str,
    summary: str,
) -> bool:
    """카카오 알림톡 발송 기록 — 상담일지에 자동 저장."""
    content = f"[카톡 발송 완료 - {datetime.date.today().isoformat()}] {template_id}: {summary}"
    return log_consulting(
        agent_id=agent_id,
        person_id=person_id,
        log_type="kakao_sent",
        content=content,
        ai_briefing_json={
            "template_id":   template_id,
            "customer_name": customer_name,
            "summary":       summary,
        },
    )


def send_kakao_report(
    customer_name: str,
    phone_number: str,
    report_summary: str,
    agent_id: str = "",
    person_id: str = "",
    template_id: str = "GP_AI_REPORT_01",
    api_url: str = "",
    api_key: str = "",
) -> dict:
    """
    카카오 알림톡 발송 로직.
    - api_url/api_key 제공 시 실제 POST 발송 (Solapi / Aligo 등)
    - 미제공 시 dry-run 모드 (UI 미리보기만)
    - 발송 성공 시 log_kakao_sent()로 상담일지에 자동 기록

    Returns:
        {"ok": True/False, "dry_run": bool, "message": str}
    """
    payload = {
        "template_id": template_id,
        "receiver":    phone_number,
        "variables": {
            "name":    customer_name,
            "summary": report_summary,
            "link":    "https://goldkey-ai-817097913199.asia-northeast3.run.app",
        },
    }

    if not api_url or not api_key:
        if agent_id and person_id:
            log_kakao_sent(agent_id, person_id, customer_name, template_id, report_summary)
        return {
            "ok":      True,
            "dry_run": True,
            "message": f"[미리보기] {customer_name} 님 — {report_summary}",
            "payload": payload,
        }

    try:
        import urllib.request
        import json as _j
        import urllib.error

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        req = urllib.request.Request(
            api_url,
            data=_j.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = _j.loads(resp.read())

        if agent_id and person_id:
            log_kakao_sent(agent_id, person_id, customer_name, template_id, report_summary)

        return {"ok": True, "dry_run": False, "message": "발송 완료", "response": result}

    except Exception as e:
        return {"ok": False, "dry_run": False, "message": str(e)}
