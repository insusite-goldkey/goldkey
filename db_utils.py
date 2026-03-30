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
import threading
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

# ── [GP-SEARCH] 띄어쓰기 무시 + 복합 키워드 AND 검색 헬퍼 ───────────────────────

def _normalize_query(query: str) -> tuple[str, list[str]]:
    """
    검색어 정규화.
    Returns:
        clean_q  — 공백 제거 버전 ('치매 보험' → '치매보험')
        tokens   — 공백 분리 단어 목록 (AND 검색용: ['3월', '자동차'])
    """
    stripped = query.strip()
    clean_q  = stripped.replace(" ", "")
    tokens   = [t.strip() for t in stripped.split() if t.strip()]
    return clean_q, tokens


def _matches_query(row: dict, clean_q: str, tokens: list[str]) -> bool:
    """
    [GP-SEARCH] 띄어쓰기 무시 AND 매칭.
    검색 대상 필드: name, memo, job, address, status, auto/fire_renewal_month.
    """
    # 검색 대상 텍스트 합산 (소문자)
    parts = [
        row.get("name",    ""),
        row.get("memo",    ""),
        row.get("job",     ""),
        row.get("address", ""),
        row.get("status",  ""),
        row.get("contact", ""),
        str(row.get("auto_renewal_month", "") or ""),
        str(row.get("fire_renewal_month", "") or ""),
    ]
    full_text       = " ".join(p for p in parts if p).lower()
    full_text_clean = full_text.replace(" ", "")  # 공백 제거 버전

    if len(tokens) >= 2:
        # 복합 키워드 AND: 모든 토큰이 full_text 어딘가에 존재해야 함
        return all(t.lower() in full_text for t in tokens)
    else:
        # 단일 키워드: 공백 무시 매칭 (clean_q vs clean text)
        return clean_q.lower() in full_text_clean


def load_customers(agent_id: str, query: str = "") -> list[dict]:
    """
    gk_people 조회 (담당 설계사 + [GP-SEARCH] 띄어쓰기 무시 + 복합키워드 AND 필터).
    @st.cache_data(ttl=60) 적용 — 호출 측에서 wrapping 필요.

    검색 전략:
      1. DB: agent_id 필터 + 단일 키워드면 name ilike 프리필터 (속도 최적화)
      2. Python: 공백 제거 버전 clean_q 로 전 필드(name/memo/job/address 등) AND 매칭
    """
    sb = _get_sb()
    if not sb:
        return []
    try:
        q = sb.table("gk_people").select("*").eq("is_deleted", False)
        if agent_id:
            q = q.eq("agent_id", agent_id)

        clean_q: str    = ""
        tokens:  list   = []
        if query:
            clean_q, tokens = _normalize_query(query)
            if len(tokens) <= 1 and clean_q and " " not in query:
                # 단일/공백없는 키워드: DB 프리필터로 name 대상 빠른 선별
                # (Python 포스트필터가 memo/job 등 추가 필드도 커버)
                q = q.ilike("name", f"%{clean_q}%")
            # 복합 키워드('3월 자동차') or 공백포함 단일어: DB 필터 생략 → Python 전량 처리

        q = q.order("management_tier").order("name")
        rows = (q.execute().data or [])[:500]  # Python 포스트필터용 여유분 확보

        if query and clean_q:
            rows = [r for r in rows if _matches_query(r, clean_q, tokens)]

        return rows[:200]
    except Exception:
        return []


def get_customer(person_id: str, agent_id: str = "") -> Optional[dict]:
    """
    person_id 단건 조회.
    [GP-SEC] agent_id 제공 시 소유권 검증 — 타 설계사 고객 행 조회 차단.
    """
    sb = _get_sb()
    if not sb or not person_id:
        return None
    try:
        q = sb.table("gk_people").select("*").eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        rows = q.execute().data or []
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


def delete_customer(person_id: str, agent_id: str = "") -> bool:
    """
    고객 소프트 삭제 (is_deleted=True).
    [GP-SEC] agent_id 제공 시 소유권 검증 필수 — 타 설계사 고객 삭제 원천 차단.
    """
    sb = _get_sb()
    if not sb or not person_id:
        return False
    try:
        q = sb.table("gk_people").update({
            "is_deleted": True,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }).eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        q.execute()
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


def generate_followup_schedules(
    person_id: str,
    agent_id: str,
    contract_date: str,
    customer_name: str = "",
    policy_id: str = "",
) -> dict:
    """
    [STEP 12] 계약 후 관리 자동 스케줄러.
    
    계약일 기준으로 사후 관리 일정을 자동 생성:
    - 단기: 1개월, 3개월, 6개월, 12개월, 18개월, 24개월
    - 장기: 36개월(3년), 48개월(4년), 60개월(5년)
    
    Args:
        person_id: 고객 ID (gk_people.person_id)
        agent_id: 담당 설계사 ID
        contract_date: 계약일 (YYYY-MM-DD 형식)
        customer_name: 고객 이름 (선택, 일정 제목용)
        policy_id: 계약 ID (선택, STEP 4.5 중도 해지 시 일정 삭제용)
    
    Returns:
        {"success": bool, "created_count": int, "schedules": list[dict]}
    """
    sb = _get_sb()
    if not sb or not person_id or not agent_id or not contract_date:
        return {"success": False, "created_count": 0, "schedules": [], "error": "필수 파라미터 누락"}
    
    try:
        # 계약일 파싱
        base_date = datetime.datetime.fromisoformat(contract_date.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return {"success": False, "created_count": 0, "schedules": [], "error": f"잘못된 날짜 형식: {contract_date}"}
    
    # 사후 관리 기간 정의 (개월 단위)
    intervals = [
        1, 3, 6, 12, 18, 24,  # 단기 관리 (2년)
        36, 48, 60,            # 장기 관리 (3~5년)
    ]
    
    created_schedules = []
    now_iso = datetime.datetime.utcnow().isoformat()
    
    for months in intervals:
        # 날짜 계산 (relativedelta 대신 월 단위 계산)
        target_year = base_date.year + (base_date.month + months - 1) // 12
        target_month = (base_date.month + months - 1) % 12 + 1
        target_day = min(base_date.day, _last_day_of_month(target_year, target_month))
        
        followup_date = datetime.date(target_year, target_month, target_day)
        
        # 일정 제목 및 메모 생성
        if customer_name:
            title = f"[STEP 12] 🎁 {customer_name} 고객님 {months}개월차 가입 점검"
        else:
            title = f"[STEP 12] 🎁 고객 {months}개월차 가입 점검"
        
        memo = f"시스템 자동 생성 일정: 계약 후 {months}개월이 경과했습니다. 안부 인사 및 보장 유지 상태를 점검하세요."
        
        # gk_schedules 테이블에 INSERT
        schedule_payload = {
            "schedule_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "person_id": person_id,
            "title": title,
            "date": followup_date.isoformat(),
            "start_time": "10:00",  # 오전 10시 기본값
            "memo": memo,
            "category": "followup",
            "customer_name": customer_name,
            "policy_id": policy_id if policy_id else None,  # [STEP 4.5] 계약-일정 연결
            "is_deleted": False,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        
        try:
            sb.table("gk_schedules").insert(schedule_payload).execute()
            created_schedules.append({
                "months": months,
                "date": followup_date.isoformat(),
                "title": title,
            })
        except Exception as e:
            # 개별 일정 생성 실패 시 로그만 남기고 계속 진행
            import logging
            logging.warning(f"[STEP 12] {months}개월차 일정 생성 실패: {e}")
    
    return {
        "success": len(created_schedules) > 0,
        "created_count": len(created_schedules),
        "schedules": created_schedules,
    }


def _last_day_of_month(year: int, month: int) -> int:
    """해당 월의 마지막 날짜 반환 (윤년 고려)."""
    if month == 12:
        next_month = datetime.date(year + 1, 1, 1)
    else:
        next_month = datetime.date(year, month + 1, 1)
    last_day = next_month - datetime.timedelta(days=1)
    return last_day.day


def delete_schedule(schedule_id: str, agent_id: str = "") -> bool:
    """
    일정 소프트 삭제.
    [GP-SEC] agent_id 제공 시 소유권 검증 — 타 설계사 일정 삭제 차단.
    """
    sb = _get_sb()
    if not sb or not schedule_id:
        return False
    try:
        q = sb.table("gk_schedules").update({
            "is_deleted": True,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }).eq("schedule_id", schedule_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        q.execute()
        return True
    except Exception:
        return False


def cancel_future_schedules(policy_id: str, agent_id: str = "") -> dict:
    """
    [STEP 4.5] 계약 중도 해지 시 미래 스케줄 자동 삭제 (과거 이력 보존).
    
    계약이 해지/취소 상태로 변경되면 해당 계약과 연결된 미래의 사후 관리 일정만 삭제.
    과거 일정(오늘 이전)은 설계사의 활동 이력이므로 절대 삭제하지 않고 보존.
    
    Args:
        policy_id: 계약 ID (policies.id)
        agent_id: 담당 설계사 ID (선택, 소유권 검증용)
    
    Returns:
        {
            "success": bool,
            "deleted_count": int,
            "preserved_count": int,
            "deleted_schedules": list[dict],
        }
    """
    sb = _get_sb()
    if not sb or not policy_id:
        return {
            "success": False,
            "deleted_count": 0,
            "preserved_count": 0,
            "deleted_schedules": [],
            "error": "policy_id 필수",
        }
    
    try:
        # 오늘 날짜 (시점 기준)
        today = datetime.date.today().isoformat()
        
        # 해당 계약의 모든 일정 조회
        query = sb.table("gk_schedules").select("*").eq("policy_id", policy_id).eq("is_deleted", False)
        if agent_id:
            query = query.eq("agent_id", agent_id)
        
        all_schedules = query.execute().data or []
        
        if not all_schedules:
            return {
                "success": True,
                "deleted_count": 0,
                "preserved_count": 0,
                "deleted_schedules": [],
                "message": "삭제할 일정 없음",
            }
        
        # 과거/미래 일정 분류
        past_schedules = [s for s in all_schedules if s.get("date", "") < today]
        future_schedules = [s for s in all_schedules if s.get("date", "") >= today]
        
        # 미래 일정만 삭제 (소프트 삭제)
        deleted_schedules = []
        now_iso = datetime.datetime.utcnow().isoformat()
        
        for schedule in future_schedules:
            schedule_id = schedule.get("schedule_id")
            if not schedule_id:
                continue
            
            try:
                sb.table("gk_schedules").update({
                    "is_deleted": True,
                    "updated_at": now_iso,
                }).eq("schedule_id", schedule_id).execute()
                
                deleted_schedules.append({
                    "schedule_id": schedule_id,
                    "date": schedule.get("date"),
                    "title": schedule.get("title"),
                })
            except Exception as e:
                import logging
                logging.warning(f"[STEP 4.5] 일정 삭제 실패 (schedule_id={schedule_id}): {e}")
        
        return {
            "success": True,
            "deleted_count": len(deleted_schedules),
            "preserved_count": len(past_schedules),
            "deleted_schedules": deleted_schedules,
            "message": f"미래 일정 {len(deleted_schedules)}건 삭제, 과거 일정 {len(past_schedules)}건 보존",
        }
        
    except Exception as e:
        import logging
        logging.error(f"[STEP 4.5] cancel_future_schedules 실패: {e}")
        return {
            "success": False,
            "deleted_count": 0,
            "preserved_count": 0,
            "deleted_schedules": [],
            "error": str(e),
        }


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


def purge_expired_nibo_data(retention_days: int = 30) -> dict:
    """
    [GP-SEC §약관준수 — 내보험다보여 30일 자동 파기]
    생성일(created_at) 기준 retention_days 경과한 내보험다보여 크롤링 데이터를 삭제.
    - 대상1: gk_crawl_status (raw_json 포함 크롤링 전체 레코드)
    - 대상2: consulting_logs (log_type='nibo' 인 상담일지)
    Returns: {"crawl_deleted": int, "log_deleted": int, "error": str|None}
    """
    sb = _get_sb()
    if not sb:
        return {"crawl_deleted": 0, "log_deleted": 0, "error": "Supabase 미연결"}
    try:
        _cutoff = (
            datetime.datetime.utcnow() - datetime.timedelta(days=retention_days)
        ).isoformat()

        # 대상1: gk_crawl_status — created_at이 없는 테이블은 updated_at 기준 폴백
        try:
            _r1 = (
                sb.table("gk_crawl_status")
                .delete()
                .lt("updated_at", _cutoff)
                .execute()
            )
            _c1 = len(_r1.data or [])
        except Exception as _e1:
            _c1 = 0

        # 대상2: consulting_logs — log_type='nibo' AND created_at < cutoff
        try:
            _r2 = (
                sb.table("consulting_logs")
                .delete()
                .eq("log_type", "nibo")
                .lt("created_at", _cutoff)
                .execute()
            )
            _c2 = len(_r2.data or [])
        except Exception as _e2:
            _c2 = 0

        return {"crawl_deleted": _c1, "log_deleted": _c2, "error": None}
    except Exception as _e:
        return {"crawl_deleted": 0, "log_deleted": 0, "error": str(_e)}


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
    [무중단 스키마 확장 + 데이터 무결성] 기존 데이터를 유지하며 신규/변경 필드만 안전하게 업데이트.

    - 한국어 키(직업급수, 운전형태 등)와 영어 DB 컬럼 키 모두 허용
    - 없는 컬럼은 dict.get() 기본값으로 방어
    - 기존 데이터 None 필드 시스템 안전 (터지지 않음)
    - [GP-DATA-INTEGRITY] 내용이 많은 쪽 보존 원칙 적용
    """
    sb = _get_sb()
    if not sb or not person_id:
        return False

    # 기존 데이터 조회
    existing_data = get_customer(person_id, agent_id)
    
    payload: dict = {"updated_at": datetime.datetime.utcnow().isoformat()}

    for raw_key, value in new_data.items():
        db_col = _FIELD_MAP.get(raw_key, raw_key)
        default = _COLUMN_DEFAULTS.get(db_col)
        
        # [GP-DATA-INTEGRITY] 내용이 많은 쪽 보존
        if existing_data and db_col in existing_data:
            existing_value = existing_data.get(db_col)
            
            # 둘 다 문자열인 경우: 더 긴 텍스트 선택
            if isinstance(existing_value, str) and isinstance(value, str):
                existing_len = len(str(existing_value).strip())
                new_len = len(str(value).strip())
                
                # 새 값이 더 길거나 기존 값이 비어있으면 새 값 사용
                if new_len > existing_len or not existing_value:
                    payload[db_col] = value if value is not None else default
                else:
                    # 기존 값이 더 길면 유지 (payload에 추가하지 않음)
                    continue
            else:
                # 문자열이 아닌 경우: 새 값이 None이 아니면 업데이트
                payload[db_col] = value if value is not None else default
        else:
            # 기존 데이터가 없으면 새 값 사용
            payload[db_col] = value if value is not None else default

    if agent_id:
        payload["agent_id"] = agent_id

    try:
        q = sb.table("gk_people").update(payload).eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        q.execute()
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


# ══════════════════════════════════════════════════════════════════════════════
# §7 GCS 고객 프로파일 암호화 보관 파이프라인 (GCS 보안 3대 원칙 적용)
# ══════════════════════════════════════════════════════════════════════════════
# 원칙 1: 애플리케이션 계층 Fernet(AES-128-CBC) 암호화 — GCS에는 암호화 바이트만 업로드
# 원칙 2: 파일명에 PII(이름·연락처) 절대 금지 — {person_id}_profile.enc 형식만 허용
# 원칙 3: 식별 불가 난수 형태 파일명 (person_id UUID 기반)

_GCS_BUCKET_NAME = "goldkey-customer-profiles"
_GCS_PATH_PREFIX = "encrypted_profiles"
_GCS_AI_BRIEF_PREFIX = "crm_ai_briefs"


def schedule_gcs_customer_profile_async(
    person_id: str,
    agent_id: str,
    profile_data: dict,
) -> None:
    """
    [Dual Write · Body1] Supabase 저장 직후 GCS로 동일 스냅샷 백업(암호화).
    네트워크 지연으로 Streamlit이 멈추지 않도록 백그라운드 스레드에서만 업로드.
    """
    if not person_id or not profile_data:
        return
    _payload = {**profile_data, "person_id": person_id, "agent_id": agent_id or ""}

    def _run() -> None:
        try:
            upload_customer_profile_gcs(person_id, _payload)
        except Exception:
            pass

    threading.Thread(target=_run, name="gcs-profile-backup", daemon=True).start()


def upload_ai_brief_snapshot_gcs(agent_id: str, brief_text: str) -> bool:
    """
    설계사별 AI 브리핑 텍스트를 JSON으로 직렬화·Fernet 암호화 후 GCS에 저장.
    경로: crm_ai_briefs/{agent_id}/brief_latest.enc
    """
    if not agent_id:
        return False
    _fernet = _get_fernet()
    if not _fernet:
        return False
    gcs = _get_gcs_client()
    if not gcs:
        return False
    try:
        import json as _j
        _payload = {
            "agent_id":   agent_id,
            "brief_text": brief_text or "",
            "saved_at":   datetime.datetime.utcnow().isoformat(),
        }
        _bytes = _j.dumps(_payload, ensure_ascii=False).encode("utf-8")
        _enc = _fernet.encrypt(_bytes)
        _blob_path = f"{_GCS_AI_BRIEF_PREFIX}/{agent_id}/brief_latest.enc"
        _bucket = gcs.bucket(_GCS_BUCKET_NAME)
        _blob = _bucket.blob(_blob_path)
        _blob.upload_from_string(_enc, content_type="application/octet-stream")
        return True
    except Exception:
        return False


def schedule_ai_brief_gcs_async(agent_id: str, brief_text: str) -> None:
    """save_ai_brief 직후 GCS 백업 — 비동기 fire-and-forget."""

    def _run() -> None:
        try:
            upload_ai_brief_snapshot_gcs(agent_id, brief_text)
        except Exception:
            pass

    threading.Thread(target=_run, name="gcs-ai-brief-backup", daemon=True).start()


def _get_fernet():
    """ENCRYPTION_KEY 환경변수 → Fernet 인스턴스 반환."""
    try:
        from shared_components import get_env_secret
        from cryptography.fernet import Fernet
        import base64
        _raw_key = get_env_secret("ENCRYPTION_KEY", "")
        if not _raw_key:
            return None
        _key_bytes = _raw_key.encode() if isinstance(_raw_key, str) else _raw_key
        if len(_key_bytes) != 44:
            _key_bytes = base64.urlsafe_b64encode(_key_bytes[:32].ljust(32, b"\x00"))
        return Fernet(_key_bytes)
    except Exception:
        return None


def _get_gcs_client():
    """Google Cloud Storage 클라이언트 lazy init."""
    try:
        from google.cloud import storage as _gcs
        return _gcs.Client()
    except Exception:
        return None


def upload_customer_profile_gcs(person_id: str, profile_data: dict) -> bool:
    """
    고객 프로파일을 Fernet 암호화 후 GCS에 업로드.

    보안 원칙:
      - profile_data 전체를 JSON 직렬화 → Fernet 암호화 → 암호화 바이트만 업로드
      - 파일명: {person_id}_profile.enc (PII 없음)
      - 경로: {_GCS_PATH_PREFIX}/{agent_id}/{person_id}_profile.enc

    Args:
        person_id: 고객 UUID (파일명에 사용)
        profile_data: 저장할 고객 정보 dict (job_name, injury_level, name 등)

    Returns:
        True: 업로드 성공, False: 실패
    """
    if not person_id or not profile_data:
        return False

    _fernet = _get_fernet()
    if not _fernet:
        return False

    gcs = _get_gcs_client()
    if not gcs:
        return False

    try:
        import json as _j
        _agent_id = profile_data.get("agent_id", "unknown")
        _payload_bytes = _j.dumps(profile_data, ensure_ascii=False).encode("utf-8")
        _encrypted = _fernet.encrypt(_payload_bytes)
        _blob_path = f"{_GCS_PATH_PREFIX}/{_agent_id}/{person_id}_profile.enc"
        _bucket = gcs.bucket(_GCS_BUCKET_NAME)
        _blob = _bucket.blob(_blob_path)
        _blob.upload_from_string(_encrypted, content_type="application/octet-stream")
        return True
    except Exception:
        return False


def download_customer_profile_gcs(person_id: str, agent_id: str = "") -> dict | None:
    """
    GCS에서 암호화된 고객 프로파일을 다운로드 후 복호화.

    Returns:
        복호화된 고객 정보 dict, 실패 시 None
    """
    if not person_id:
        return None

    _fernet = _get_fernet()
    if not _fernet:
        return None

    gcs = _get_gcs_client()
    if not gcs:
        return None

    try:
        import json as _j
        _blob_path = f"{_GCS_PATH_PREFIX}/{agent_id}/{person_id}_profile.enc"
        _bucket = gcs.bucket(_GCS_BUCKET_NAME)
        _blob = _bucket.blob(_blob_path)
        if not _blob.exists():
            return None
        _encrypted_bytes = _blob.download_as_bytes()
        _decrypted_bytes = _fernet.decrypt(_encrypted_bytes)
        return _j.loads(_decrypted_bytes.decode("utf-8"))
    except Exception:
        return None


def save_customer_profile_with_gcs(
    person_id: str,
    agent_id: str,
    profile_data: dict,
    supabase_client=None,
) -> bool:
    """
    Supabase(gk_people) 갱신 후 동일 스냅샷을 GCS에 비동기 백업(Dual Write).
    반환 True: DB 갱신 성공. GCS는 백그라운드에서 best-effort.
    """
    _db_ok = False

    sb = supabase_client or _get_sb()
    if sb:
        try:
            import datetime as _dt
            _row = {
                "person_id":    person_id,
                "agent_id":     agent_id,
                "job":          profile_data.get("job") or profile_data.get("job_name"),
                "injury_level": profile_data.get("injury_level"),
                "updated_at":   _dt.datetime.utcnow().isoformat(),
            }
            _row = {k: v for k, v in _row.items() if v is not None}
            sb.table("gk_people").update(_row).eq("person_id", person_id).execute()
            _db_ok = True
        except Exception:
            pass

    _gcs_data = {**profile_data, "person_id": person_id, "agent_id": agent_id}
    schedule_gcs_customer_profile_async(person_id, agent_id, _gcs_data)
    return _db_ok


def bind_injury_level_to_session(person_id: str) -> dict:
    """
    HQ 앱 도킹 시 호출 — DB에서 job_name + injury_level 조회 후
    st.session_state에 바인딩.

    Returns:
        {"job_name": str, "injury_level": int}
    """
    try:
        import streamlit as _st
        _customer = get_customer(person_id)
        if not _customer:
            return {"job_name": "", "injury_level": 0}

        _job_name     = _customer.get("job", "") or ""
        _injury_level = _customer.get("injury_level") or 0
        try:
            _injury_level = int(_injury_level)
        except Exception:
            _injury_level = 0

        _st.session_state["customer_job"]           = _job_name
        _st.session_state["injury_level"]           = _injury_level
        _st.session_state["current_injury_level"]   = _injury_level
        _st.session_state["current_job_name"]       = _job_name

        return {"job_name": _job_name, "injury_level": _injury_level}
    except Exception:
        return {"job_name": "", "injury_level": 0}


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
    # ── [GP-SEC §3] 격벽 검증: 발송 전 person_id → agent_id 소유권 확인 ──────────
    # 타 설계사 고객에게 카카오 발송되는 보안사고 0% 목표
    if agent_id and person_id:
        try:
            _sb_chk = _get_sb()
            if _sb_chk:
                _own = (
                    _sb_chk.table("gk_persons")
                    .select("agent_id")
                    .eq("person_id", person_id)
                    .eq("agent_id", agent_id)
                    .limit(1)
                    .execute().data or []
                )
                if not _own:
                    return {
                        "ok":      False,
                        "dry_run": False,
                        "message": (
                            f"[보안 차단] 고객-설계사 매핑 불일치 — "
                            f"person_id={person_id[:8]}... 는 해당 설계사 소속이 아닙니다."
                        ),
                    }
        except Exception:
            pass  # DB 조회 실패 시 서비스 연속성 우선 — 발송 진행

    try:
        from shared_components import HQ_APP_URL as _hq_u
        _hq_link = (_hq_u or "").strip().rstrip("/") or "http://localhost:8501"
    except Exception:
        import os as _os_hq
        _hq_link = (_os_hq.environ.get("HQ_APP_URL") or "http://localhost:8501").strip().rstrip("/")

    # [GP-SEC §3] 이름 마스킹 — payload.variables.name은 메시지 템플릿 변수로 API 외부 전송
    try:
        from shared_components import mask_name as _mn_dku
    except Exception:
        _mn_dku = lambda x: x  # noqa: E731
    _masked_name = _mn_dku(customer_name)

    payload = {
        "template_id": template_id,
        "receiver":    phone_number,   # [GP-SEC] 라우팅용 실번호 유지 (카카오 전송 필수)
        "variables": {
            "name":    _masked_name,    # [GP-SEC] 이름 비식별화 필수 적용
            "summary": report_summary,
            "link":    _hq_link,
        },
    }

    if not api_url or not api_key:
        return {
            "ok":      True,
            "dry_run": True,
            "message": f"[미리보기] {customer_name} 님 — {report_summary}",
            "payload": payload,
        }

    # ── [K1] requests.post 실통신 — Solapi / Aligo / 팝빌 등 범용 규격 ──────────
    try:
        import requests as _rq

        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        _resp = _rq.post(api_url, json=payload, headers=headers, timeout=10)

        if _resp.status_code == 200:
            # ── [K1] HTTP 200 성공 시 log_consulting 직접 체이닝 ──────────────
            if agent_id and person_id:
                log_consulting(
                    agent_id=agent_id,
                    person_id=person_id,
                    log_type="kakao_sent",
                    content=(
                        f"[카톡 발송 완료 - {datetime.date.today().isoformat()}]"
                        f" {template_id}: {report_summary}"
                    ),
                    ai_briefing_json={
                        "template_id":   template_id,
                        "customer_name": _masked_name,  # [GP-SEC] 로그에도 마스킹된 이름 기록
                        "summary":       report_summary,
                        "http_status":   _resp.status_code,
                    },
                )
            try:
                _result = _resp.json()
            except Exception:
                _result = {"raw": _resp.text[:500]}
            return {"ok": True, "dry_run": False, "message": "발송 완료", "response": _result}
        else:
            return {
                "ok":      False,
                "dry_run": False,
                "message": f"발송 실패 (HTTP {_resp.status_code}): {_resp.text[:200]}",
            }

    except Exception as e:
        return {"ok": False, "dry_run": False, "message": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# §8 회원 (gk_members) — 인증 및 크레딧 시스템
# ══════════════════════════════════════════════════════════════════════════════

def get_member(name: str) -> Optional[dict]:
    """이름으로 설계사 회원 1건 조회 (인증 전용)."""
    sb = _get_sb()
    if not sb or not name:
        return None
    try:
        rows = (
            sb.table("gk_members").select("*")
            .eq("name", name.strip())
            .execute().data or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def get_all_members() -> list[dict]:
    """전체 설계사 회원 목록 (관리자 전용)."""
    sb = _get_sb()
    if not sb:
        return []
    try:
        return sb.table("gk_members").select("*").execute().data or []
    except Exception:
        return []


def upsert_member(member: dict) -> bool:
    """회원 upsert (name 기준)."""
    sb = _get_sb()
    if not sb or not member:
        return False
    try:
        sb.table("gk_members").upsert(member, on_conflict="name").execute()
        return True
    except Exception:
        return False


def update_member_pin_hash(name: str, pin_hash: str) -> bool:
    """회원 PIN 해시 갱신 (레거시 → SHA-256 마이그레이션용)."""
    sb = _get_sb()
    if not sb or not name:
        return False
    try:
        sb.table("gk_members").update({"pin_hash": pin_hash}).eq("name", name).execute()
        return True
    except Exception:
        return False


# ── [GP-BILLING] 크레딧 시스템 함수 ────────────────────────────────────────────

def initialize_user_billing_status(user_id: str, join_date: Optional[str] = None) -> dict:
    """
    [GP-BILLING] 신규 회원 가입 시 타임라인 기반 상태 초기화.
    
    Phase 1 (2026-08-31 이전 가입): status='BETA', 100 크레딧
    Phase 2 (2026-09-01 이후 가입): status='TRIAL', trial_end_date=가입일+30일
    
    Args:
        user_id: 회원 ID
        join_date: 가입일 (YYYY-MM-DD), None이면 오늘 날짜
    
    Returns:
        {"success": bool, "status": str, "message": str}
    """
    sb = _get_sb()
    if not sb or not user_id:
        return {"success": False, "status": "", "message": "Invalid user_id"}
    
    try:
        from datetime import datetime, timedelta
        
        # 가입일 결정
        if join_date:
            jd = datetime.strptime(join_date, "%Y-%m-%d").date()
        else:
            jd = datetime.now().date()
        
        # 타임라인 기준일: 2026-09-01
        cutoff_date = datetime(2026, 9, 1).date()
        
        if jd < cutoff_date:
            # Phase 1: BETA 사용자
            status = "BETA"
            current_credits = 100
            trial_end_date = None
            # 다음 달 1일로 갱신일 설정
            next_month = jd.replace(day=1) + timedelta(days=32)
            monthly_renewal_date = next_month.replace(day=1)
        else:
            # Phase 2: TRIAL 사용자 (30일 무료체험)
            status = "TRIAL"
            current_credits = 999  # 무제한 표시용
            trial_end_date = jd + timedelta(days=30)
            monthly_renewal_date = None
        
        # DB 업데이트
        sb.table("gk_members").update({
            "status": status,
            "plan_type": "BASIC",
            "current_credits": current_credits,
            "join_date": jd.isoformat(),
            "trial_end_date": trial_end_date.isoformat() if trial_end_date else None,
            "monthly_renewal_date": monthly_renewal_date.isoformat() if monthly_renewal_date else None,
        }).eq("user_id", user_id).execute()
        
        return {
            "success": True,
            "status": status,
            "message": f"{'베타 사용자' if status == 'BETA' else '무료체험 사용자'}로 초기화 완료",
            "credits": current_credits,
            "trial_end_date": trial_end_date.isoformat() if trial_end_date else None,
        }
    except Exception as e:
        return {"success": False, "status": "", "message": f"초기화 실패: {str(e)}"}


def check_and_deduct_credits(user_id: str, cost: int, reason: str = "AI 기능 사용") -> dict:
    """
    [GP-BILLING] AI 기능 실행 전 크레딧 체크 및 차감.
    
    Args:
        user_id: 회원 ID
        cost: 차감할 크레딧 (1=스캔, 3=에이젠틱)
        reason: 차감 사유
    
    Returns:
        {"success": bool, "message": str, "remaining": int}
    """
    sb = _get_sb()
    if not sb or not user_id:
        return {"success": False, "message": "Invalid user_id", "remaining": 0}
    
    try:
        # 사용자 정보 조회
        user_data = sb.table("gk_members").select("*").eq("user_id", user_id).execute().data
        if not user_data:
            return {"success": False, "message": "사용자를 찾을 수 없습니다.", "remaining": 0}
        
        user = user_data[0]
        status = user.get("status", "BETA")
        current_credits = user.get("current_credits", 0)
        
        # TRIAL 상태는 크레딧 무제한
        if status == "TRIAL":
            return {"success": True, "message": "무료체험 중 (크레딧 무제한)", "remaining": 999}
        
        # EXPIRED 상태는 차단
        if status == "EXPIRED":
            return {
                "success": False,
                "message": "무료체험 종료. 결제가 필요합니다.",
                "remaining": 0
            }
        
        # 크레딧 부족 체크
        if current_credits < cost:
            return {
                "success": False,
                "message": "이번 달 잔여 코인이 부족합니다. 다음 달 갱신을 기다리시거나 관리자에게 충전을 문의하세요.",
                "remaining": current_credits
            }
        
        # 크레딧 차감
        new_credits = current_credits - cost
        sb.table("gk_members").update({"current_credits": new_credits}).eq("user_id", user_id).execute()
        
        # 히스토리 기록 (선택적 - gk_credit_history 테이블 있을 경우)
        try:
            sb.table("gk_credit_history").insert({
                "user_id": user_id,
                "action_type": "DEDUCT",
                "amount": cost,
                "before_balance": current_credits,
                "after_balance": new_credits,
                "reason": reason,
            }).execute()
        except Exception:
            pass  # 히스토리 테이블 없어도 무시
        
        return {
            "success": True,
            "message": "크레딧 차감 완료",
            "remaining": new_credits
        }
    except Exception as e:
        return {"success": False, "message": f"크레딧 차감 실패: {str(e)}", "remaining": 0}


def renew_monthly_credits_if_needed(user_id: str) -> dict:
    """
    [GP-BILLING] 매월 크레딧 갱신 체크 (BETA/PAID 전용).
    로그인 시 또는 Cron Job으로 호출.
    
    Returns:
        {"success": bool, "message": str, "renewed": bool}
    """
    sb = _get_sb()
    if not sb or not user_id:
        return {"success": False, "message": "Invalid user_id", "renewed": False}
    
    try:
        from datetime import datetime
        
        # 사용자 정보 조회
        user_data = sb.table("gk_members").select("*").eq("user_id", user_id).execute().data
        if not user_data:
            return {"success": False, "message": "사용자를 찾을 수 없습니다.", "renewed": False}
        
        user = user_data[0]
        status = user.get("status", "BETA")
        plan_type = user.get("plan_type", "BASIC")
        monthly_renewal_date = user.get("monthly_renewal_date")
        current_credits = user.get("current_credits", 0)
        
        # TRIAL/EXPIRED는 갱신 대상 아님
        if status in ["TRIAL", "EXPIRED"]:
            return {"success": False, "message": "갱신 대상이 아닙니다.", "renewed": False}
        
        # 갱신일이 없으면 설정 (최초 1회)
        if not monthly_renewal_date:
            from datetime import timedelta
            today = datetime.now().date()
            next_month = today.replace(day=1) + timedelta(days=32)
            new_renewal_date = next_month.replace(day=1)
            
            sb.table("gk_members").update({
                "monthly_renewal_date": new_renewal_date.isoformat()
            }).eq("user_id", user_id).execute()
            
            return {"success": True, "message": "갱신일 설정 완료", "renewed": False}
        
        # 갱신일 도달 체크
        today = datetime.now().date()
        renewal_date = datetime.strptime(monthly_renewal_date, "%Y-%m-%d").date()
        
        if today < renewal_date:
            return {"success": False, "message": "아직 갱신일이 아닙니다.", "renewed": False}
        
        # 플랜별 크레딧 지급량
        if status == "BETA":
            new_credits = 100
        elif status == "PAID" and plan_type == "PRO":
            new_credits = 200
        elif status == "PAID" and plan_type == "BASIC":
            new_credits = 50
        else:
            new_credits = 100
        
        # 크레딧 갱신
        from datetime import timedelta
        next_renewal = renewal_date + timedelta(days=32)
        next_renewal = next_renewal.replace(day=1)
        
        sb.table("gk_members").update({
            "current_credits": new_credits,
            "monthly_renewal_date": next_renewal.isoformat()
        }).eq("user_id", user_id).execute()
        
        # 히스토리 기록
        try:
            sb.table("gk_credit_history").insert({
                "user_id": user_id,
                "action_type": "RENEW",
                "amount": new_credits,
                "before_balance": current_credits,
                "after_balance": new_credits,
                "reason": "월간 크레딧 갱신",
            }).execute()
        except Exception:
            pass
        
        return {
            "success": True,
            "message": f"크레딧 갱신 완료 ({new_credits} 코인)",
            "renewed": True,
            "new_credits": new_credits
        }
    except Exception as e:
        return {"success": False, "message": f"갱신 실패: {str(e)}", "renewed": False}


def check_trial_expiry(user_id: str) -> dict:
    """
    [GP-BILLING] 트라이얼 만료 체크 및 EXPIRED 전환.
    로그인 시 호출하여 자동 상태 전환.
    
    Returns:
        {"success": bool, "expired": bool, "days_left": int, "message": str}
    """
    sb = _get_sb()
    if not sb or not user_id:
        return {"success": False, "expired": False, "days_left": 0, "message": "Invalid user_id"}
    
    try:
        from datetime import datetime
        
        # 사용자 정보 조회
        user_data = sb.table("gk_members").select("*").eq("user_id", user_id).execute().data
        if not user_data:
            return {"success": False, "expired": False, "days_left": 0, "message": "사용자를 찾을 수 없습니다."}
        
        user = user_data[0]
        status = user.get("status", "BETA")
        trial_end_date = user.get("trial_end_date")
        
        # TRIAL 상태가 아니면 체크 불필요
        if status != "TRIAL":
            return {"success": False, "expired": False, "days_left": 0, "message": "TRIAL 상태가 아닙니다."}
        
        if not trial_end_date:
            return {"success": False, "expired": False, "days_left": 0, "message": "trial_end_date 없음"}
        
        # 만료일 도달 체크
        today = datetime.now().date()
        end_date = datetime.strptime(trial_end_date, "%Y-%m-%d").date()
        days_left = (end_date - today).days
        
        if today >= end_date:
            # EXPIRED 전환
            sb.table("gk_members").update({"status": "EXPIRED"}).eq("user_id", user_id).execute()
            
            return {
                "success": True,
                "expired": True,
                "days_left": 0,
                "message": "무료체험 종료 → EXPIRED 전환"
            }
        
        return {
            "success": True,
            "expired": False,
            "days_left": days_left,
            "message": f"무료체험 진행 중 ({days_left}일 남음)"
        }
    except Exception as e:
        return {"success": False, "expired": False, "days_left": 0, "message": f"체크 실패: {str(e)}"}


def admin_update_credits(user_id: str, delta: int, admin_id: str = "system") -> dict:
    """
    [GP-BILLING] 관리자 전용 크레딧 충전/차감.
    
    Args:
        user_id: 대상 회원 ID
        delta: 변경량 (양수=충전, 음수=차감)
        admin_id: 관리자 ID
    
    Returns:
        {"success": bool, "message": str, "new_balance": int}
    """
    sb = _get_sb()
    if not sb or not user_id:
        return {"success": False, "message": "Invalid user_id", "new_balance": 0}
    
    try:
        # 사용자 정보 조회
        user_data = sb.table("gk_members").select("*").eq("user_id", user_id).execute().data
        if not user_data:
            return {"success": False, "message": "사용자를 찾을 수 없습니다.", "new_balance": 0}
        
        user = user_data[0]
        current_credits = user.get("current_credits", 0)
        new_credits = max(0, current_credits + delta)  # 음수 방지
        
        # 크레딧 업데이트
        sb.table("gk_members").update({"current_credits": new_credits}).eq("user_id", user_id).execute()
        
        # 히스토리 기록
        action_type = "ADMIN_ADD" if delta > 0 else "ADMIN_SUBTRACT"
        try:
            sb.table("gk_credit_history").insert({
                "user_id": user_id,
                "action_type": action_type,
                "amount": abs(delta),
                "before_balance": current_credits,
                "after_balance": new_credits,
                "reason": f"관리자 {'충전' if delta > 0 else '차감'}",
                "admin_id": admin_id,
            }).execute()
        except Exception:
            pass
        
        return {
            "success": True,
            "message": f"크레딧 {'충전' if delta > 0 else '차감'} 완료",
            "new_balance": new_credits
        }
    except Exception as e:
        return {"success": False, "message": f"업데이트 실패: {str(e)}", "new_balance": 0}


def admin_update_status(user_id: str, new_status: str, admin_id: str = "system") -> dict:
    """
    [GP-BILLING] 관리자 전용 회원 상태 강제 변경.
    
    Args:
        user_id: 대상 회원 ID
        new_status: 새 상태 (BETA/TRIAL/PAID/EXPIRED)
        admin_id: 관리자 ID
    
    Returns:
        {"success": bool, "message": str}
    """
    sb = _get_sb()
    if not sb or not user_id:
        return {"success": False, "message": "Invalid user_id"}
    
    if new_status not in ["BETA", "TRIAL", "PAID", "EXPIRED"]:
        return {"success": False, "message": "Invalid status"}
    
    try:
        sb.table("gk_members").update({"status": new_status}).eq("user_id", user_id).execute()
        
        return {
            "success": True,
            "message": f"상태 변경 완료: {new_status}"
        }
    except Exception as e:
        return {"success": False, "message": f"상태 변경 실패: {str(e)}"}


# ══════════════════════════════════════════════════════════════════════════════
# §9 상담일지 조회 (gk_consulting_logs)
# ══════════════════════════════════════════════════════════════════════════════

def get_consulting_logs(
    agent_id: str,
    person_id: str = "",
    log_type: str = "",
    limit: int = 20,
) -> list[dict]:
    """
    상담일지 조회.
    agent_id: 필수 (RLS — 타 설계사 조회 차단)
    person_id: 특정 고객 필터 (옵션)
    log_type:  'ai_brief' | 'kakao_sent' | 'nibo' | 'manual' | '' (전체)
    """
    sb = _get_sb()
    if not sb or not agent_id:
        return []
    try:
        q = (sb.table("gk_consulting_logs")
             .select("content,created_at,log_type,person_id,ai_briefing_json")
             .eq("agent_id", agent_id))
        if person_id:
            q = q.eq("person_id", person_id)
        if log_type:
            q = q.eq("log_type", log_type)
        return (q.order("created_at", desc=True).limit(limit).execute().data or [])
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# §10 크롤링 상태 목록 (gk_crawl_status)
# ══════════════════════════════════════════════════════════════════════════════

def get_crawl_status_list(agent_id: str, limit: int = 5) -> list[dict]:
    """
    담당 설계사의 최근 크롤링 상태 목록 조회.
    (단건 get_crawl_status와 달리 여러 고객의 파이프라인 배지용)
    """
    sb = _get_sb()
    if not sb or not agent_id:
        return []
    try:
        return (
            sb.table("gk_crawl_status")
            .select("status,updated_at,person_id")
            .eq("agent_id", agent_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute().data or []
        )
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# §11 증권·관계망 요약 (crm_fortress 위임 래퍼)
# ══════════════════════════════════════════════════════════════════════════════

def get_person_policies_summary(person_id: str) -> list[dict]:
    """
    gk_policy_roles JOIN gk_policies — 고객의 증권 목록 요약.
    (crm_fortress.get_person_policies의 경량 버전)
    """
    sb = _get_sb()
    if not sb or not person_id:
        return []
    try:
        return (
            sb.table("gk_policy_roles")
            .select("role, policies:policy_id("
                    "product_name,insurance_company,"
                    "premium,contract_date,"
                    "policy_number,policy_id)")
            .eq("person_id", person_id)
            .eq("is_deleted", False)
            .execute().data or []
        )
    except Exception:
        return []


def get_person_relationships(person_id: str, agent_id: str = "") -> list[dict]:
    """고객의 인맥 관계망 조회 (gk_relationships)."""
    sb = _get_sb()
    if not sb or not person_id:
        return []
    try:
        rows = (
            sb.table("gk_relationships")
            .select("relation_type,"
                    "from_person:from_person_id(name),"
                    "to_person:to_person_id(name)")
            .eq("is_deleted", False)
            .or_(f"from_person_id.eq.{person_id},to_person_id.eq.{person_id}")
            .execute().data or []
        )
        if agent_id:
            rows = [r for r in rows if r.get("agent_id", agent_id) == agent_id]
        return rows
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# §12 AI 브리핑 (gk_ai_briefs)
# ══════════════════════════════════════════════════════════════════════════════

def get_ai_brief(agent_id: str, limit: int = 1) -> list[dict]:
    """최근 저장된 AI 브리핑 조회."""
    sb = _get_sb()
    if not sb or not agent_id:
        return []
    try:
        return (
            sb.table("gk_ai_briefs")
            .select("brief_text,created_at")
            .eq("agent_id", agent_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute().data or []
        )
    except Exception:
        return []


def save_ai_brief(agent_id: str, brief_text: str) -> bool:
    """AI 브리핑 저장 — Supabase(gk_ai_briefs) 동기 + GCS 실시간 백업(비동기)."""
    sb = _get_sb()
    if not sb or not agent_id:
        return False
    try:
        sb.table("gk_ai_briefs").upsert({
            "agent_id":   agent_id,
            "brief_text": brief_text,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }, on_conflict="agent_id").execute()
        schedule_ai_brief_gcs_async(agent_id, brief_text)
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §13 시스템 설정 (system_config) — HQ 앱 건강보험료율 등
# ══════════════════════════════════════════════════════════════════════════════

def get_system_config(keys: list[str]) -> dict[str, str]:
    """
    system_config 테이블에서 key/value 쌍 조회.
    반환: {"nhis_rate": "0.0709", "ltci_rate": "0.0082", ...}
    """
    sb = _get_sb()
    if not sb or not keys:
        return {}
    try:
        rows = (
            sb.table("system_config")
            .select("key,value")
            .in_("key", keys)
            .execute().data or []
        )
        return {r["key"]: r["value"] for r in rows}
    except Exception:
        return {}


def set_system_config(upserts: list[dict]) -> bool:
    """
    system_config 테이블 upsert.
    upserts: [{"key": "nhis_rate", "value": "0.0709"}, ...]
    """
    sb = _get_sb()
    if not sb or not upserts:
        return False
    try:
        sb.table("system_config").upsert(upserts, on_conflict="key").execute()
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §14 디바이스 히스토리 (gk_device_history) — HQ 인증 전용
# ══════════════════════════════════════════════════════════════════════════════

def log_device(
    user_name: str,
    fp_id: str,
    ua_hint: str = "",
    max_devices: int = 5,
) -> bool:
    """디바이스 인증 기록 + 최대 N개 초과 시 가장 오래된 항목 삭제."""
    sb = _get_sb()
    if not sb:
        return False
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        sb.table("gk_device_history").upsert({
            "user_name": user_name,
            "fp_id":     fp_id,
            "ua_hint":   ua_hint,
            "last_seen": now_str,
        }, on_conflict="user_name,fp_id").execute()
        _rows = (
            sb.table("gk_device_history")
            .select("fp_id,last_seen")
            .eq("user_name", user_name)
            .order("last_seen", desc=False)
            .execute().data or []
        )
        if len(_rows) > max_devices:
            oldest_fp = _rows[0]["fp_id"]
            sb.table("gk_device_history").delete()\
              .eq("user_name", user_name).eq("fp_id", oldest_fp).execute()
        return True
    except Exception:
        return False


def get_devices(user_name: str) -> list[dict]:
    """등록된 디바이스 목록 조회."""
    sb = _get_sb()
    if not sb or not user_name:
        return []
    try:
        return (
            sb.table("gk_device_history")
            .select("fp_id,last_seen,ua_hint")
            .eq("user_name", user_name)
            .order("last_seen", desc=True)
            .execute().data or []
        )
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# §15 게스트 방문 카운터 (gk_guest_visits) — HQ 공개 접근 제어
# ══════════════════════════════════════════════════════════════════════════════

def check_and_log_guest_visit(fp_id: str, max_daily: int = 3) -> dict:
    """
    게스트 일일 방문 횟수 확인 + 기록.
    반환: {"allowed": bool, "visits_today": int, "total_visits": int}
    """
    sb = _get_sb()
    if not sb:
        return {"allowed": True, "visits_today": 0, "total_visits": 0}
    today_str = datetime.date.today().isoformat()
    try:
        _rows = (
            sb.table("gk_guest_visits")
            .select("visit_date,visit_count")
            .eq("fp_id", fp_id)
            .execute().data or []
        )
        _total    = sum(r.get("visit_count", 0) for r in _rows)
        _today_row = next((r for r in _rows if r["visit_date"] == today_str), None)
        _today_cnt = _today_row["visit_count"] if _today_row else 0
        _allowed   = _today_cnt < max_daily

        if _allowed:
            if _today_row:
                sb.table("gk_guest_visits").update(
                    {"visit_count": _today_cnt + 1}
                ).eq("fp_id", fp_id).eq("visit_date", today_str).execute()
            else:
                sb.table("gk_guest_visits").insert(
                    {"fp_id": fp_id, "visit_date": today_str, "visit_count": 1}
                ).execute()

        return {"allowed": _allowed, "visits_today": _today_cnt, "total_visits": _total}
    except Exception:
        return {"allowed": True, "visits_today": 0, "total_visits": 0}


def get_guest_total_visits(fp_id: str) -> int:
    """게스트 fp_id의 총 방문 횟수."""
    sb = _get_sb()
    if not sb:
        return 0
    try:
        rows = (
            sb.table("gk_guest_visits")
            .select("visit_count")
            .eq("fp_id", fp_id)
            .execute().data or []
        )
        return sum(r.get("visit_count", 0) for r in rows)
    except Exception:
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# §17 컨텍스트 이전 (Context Transfer) — CRM → HQ 상담 컨텍스트 보존
# ══════════════════════════════════════════════════════════════════════════════

def save_consultation_context(
    person_id: str,
    agent_id: str,
    context_data: dict,
) -> str:
    """
    [Context Transfer] CRM → HQ 상담 컨텍스트 저장.
    gk_consultation_contexts 테이블에 INSERT 후 context_id 반환.
    Supabase 미연결 시 임시 UUID 반환 (세션 기반 폴백).
    """
    sb = _get_sb()
    now = datetime.datetime.utcnow().isoformat()
    context_id = str(uuid.uuid4())
    if not sb or not person_id or not agent_id:
        return context_id
    try:
        import json as _j
        payload: dict = {
            "context_id":   context_id,
            "person_id":    person_id,
            "agent_id":     agent_id,
            "context_data": _j.dumps(context_data, ensure_ascii=False),
            "created_at":   now,
            "expires_at":   (
                datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            ).isoformat(),
        }
        sb.table("gk_consultation_contexts").insert(payload).execute()
        return context_id
    except Exception:
        return context_id


def load_consultation_context(context_id: str, agent_id: str = "") -> dict:
    """
    [Context Transfer] HQ에서 컨텍스트 조회.
    agent_id 제공 시 소유권 검증 — 타 설계사 컨텍스트 접근 차단.
    """
    sb = _get_sb()
    if not sb or not context_id:
        return {}
    try:
        import json as _j
        q = (
            sb.table("gk_consultation_contexts")
            .select("*")
            .eq("context_id", context_id)
        )
        if agent_id:
            q = q.eq("agent_id", agent_id)
        rows = q.limit(1).execute().data or []
        if not rows:
            return {}
        r = rows[0]
        if r.get("context_data") and isinstance(r["context_data"], str):
            try:
                r["context_data"] = _j.loads(r["context_data"])
            except Exception:
                pass
        return r
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# §18 멀티디바이스 필드별 머지 (Multi-Device Field Merge)
# ══════════════════════════════════════════════════════════════════════════════

def merge_customer_fields(
    person_id: str,
    agent_id: str,
    incoming_data: dict,
    device_id: str = "",
) -> bool:
    """
    [멀티디바이스 보호] 핸드폰+태블릿 동시 사용 시 필드별 최신값 기준 머지.
    전체 row를 덮어쓰지 않고 incoming_data 각 필드를 현재 DB값과 비교:
    - DB 필드가 None/empty → incoming으로 채움
    - 둘 다 값 있음 → incoming 우선 (최신 기기 입력 존중)
    - incoming이 None/empty → 스킵 (기존 DB값 보존)
    향후 per-field updated_at 지원 시 타임스탬프 비교로 교체 가능.
    """
    sb = _get_sb()
    if not sb or not person_id or not agent_id:
        return False
    try:
        current = get_customer(person_id, agent_id) or {}
        now_iso = datetime.datetime.utcnow().isoformat()

        merged: dict = {}
        for key, val in incoming_data.items():
            if val is None or val == "":
                continue
            cur_val = current.get(key)
            if cur_val in (None, ""):
                merged[key] = val
            else:
                merged[key] = val

        if not merged:
            return True

        merged["updated_at"] = now_iso
        if device_id:
            merged["last_device_id"] = device_id

        (
            sb.table("gk_people")
            .update(merged)
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .execute()
        )
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §16 분석 원장 (analysis_reports) — 피보험자 기준 영구 보존 파이프라인
# ══════════════════════════════════════════════════════════════════════════════
# 절대 원칙: 모든 데이터는 계약자(엄마)가 아닌 피보험자(아들)의 person_id 기준 태깅
# contact_hash = sha256("pid:{person_id}") — 전화번호 해시와 충돌 없는 안정적 PK

def upsert_analysis_report(
    person_id: str,
    agent_id: str,
    analysis_data: dict,
    nhis_premium: float = 0,
    report_text: str = "",
) -> bool:
    """
    [피보험자 기준] trinity 계산 결과를 analysis_reports에 upsert.
    충돌 키: (contact_hash, agent_id) — 동일 피보험자/설계사 조합 덮어쓰기.
    """
    sb = _get_sb()
    if not sb or not person_id or not agent_id:
        return False
    try:
        import json as _j
        import hashlib as _hl
        now = datetime.datetime.utcnow().isoformat()
        _contact_hash = _hl.sha256(f"pid:{person_id}".encode()).hexdigest()
        _ad = dict(analysis_data)
        if nhis_premium:
            _ad["nhis_premium"] = nhis_premium
        _monthly = int(
            analysis_data.get("monthly")
            or analysis_data.get("monthly_income")
            or analysis_data.get("estimated_income")
            or 0
        )
        payload: dict = {
            "contact_hash":     _contact_hash,
            "person_id":        person_id,
            "agent_id":         agent_id,
            "estimated_income": _monthly,
            "analysis_data":    _j.dumps(_ad, ensure_ascii=False),
            "analyzed_at":      now,
            "updated_at":       now,
        }
        if report_text:
            payload["report_text"] = report_text
        sb.table("analysis_reports").upsert(
            payload, on_conflict="contact_hash,agent_id"
        ).execute()
        return True
    except Exception:
        return False


def load_analysis_report(person_id: str, agent_id: str = "") -> dict:
    """
    [피보험자 기준] person_id로 최신 분석 결과 조회.
    agent_id 제공 시 소유권 검증.
    """
    sb = _get_sb()
    if not sb or not person_id:
        return {}
    try:
        import json as _j
        q = (
            sb.table("analysis_reports")
            .select(
                "person_id,agent_id,estimated_income,"
                "analysis_data,report_text,analyzed_at"
            )
            .eq("person_id", person_id)
        )
        if agent_id:
            q = q.eq("agent_id", agent_id)
        rows = q.order("analyzed_at", desc=True).limit(1).execute().data or []
        if not rows:
            return {}
        r = rows[0]
        if r.get("analysis_data") and isinstance(r["analysis_data"], str):
            try:
                r["analysis_data"] = _j.loads(r["analysis_data"])
            except Exception:
                pass
        return r
    except Exception:
        return {}


def get_person_data_status(person_ids: list, agent_id: str) -> dict:
    """
    여러 person_id의 데이터 유무 배치 조회 (고객 목록 배지용).
    Returns: {person_id: {"has_nibo": bool, "has_trinity": bool}}
    """
    if not person_ids or not agent_id:
        return {}
    sb = _get_sb()
    if not sb:
        return {}
    result: dict = {
        pid: {"has_nibo": False, "has_trinity": False}
        for pid in person_ids
    }
    try:
        nibo_rows = (
            sb.table("gk_crawl_status")
            .select("person_id,status")
            .eq("agent_id", agent_id)
            .in_("person_id", list(person_ids))
            .execute().data or []
        )
        for r in nibo_rows:
            pid = r.get("person_id", "")
            if pid in result and r.get("status") == "done":
                result[pid]["has_nibo"] = True
    except Exception:
        pass
    try:
        tri_rows = (
            sb.table("analysis_reports")
            .select("person_id")
            .eq("agent_id", agent_id)
            .in_("person_id", list(person_ids))
            .execute().data or []
        )
        for r in tri_rows:
            pid = r.get("person_id", "")
            if pid in result:
                result[pid]["has_trinity"] = True
    except Exception:
        pass
    return result


# ══════════════════════════════════════════════════════════════════════════════
# §19 [GP-PHASE1] 8가지 관계망 태깅 시스템 (gk_relationship_tags)
# ══════════════════════════════════════════════════════════════════════════════

VALID_TAG_TYPES = [
    "상담자", "계약자", "피보험자", "가족", 
    "소개자", "동일법인", "동일단체", "친인척"
]


def add_relationship_tag(
    person_id: str,
    agent_id: str,
    tag_type: str,
    related_person_id: str = "",
    memo: str = "",
) -> bool:
    """
    [GP-PHASE1] 고객에게 관계망 태그 추가.
    
    Args:
        person_id: 태그 대상 고객 UUID
        agent_id: 담당 설계사
        tag_type: 8가지 중 하나 (상담자/계약자/피보험자/가족/소개자/동일법인/동일단체/친인척)
        related_person_id: 관계 대상 person_id (선택)
        memo: 관계 상세 메모
    """
    sb = _get_sb()
    if not sb or not person_id or not agent_id:
        return False
    if tag_type not in VALID_TAG_TYPES:
        raise ValueError(f"유효하지 않은 tag_type: {tag_type}. 허용값: {VALID_TAG_TYPES}")
    
    try:
        payload = {
            "person_id": person_id,
            "agent_id": agent_id,
            "tag_type": tag_type,
            "related_person_id": related_person_id or None,
            "memo": memo or None,
            "is_active": True,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }
        sb.table("gk_relationship_tags").upsert(
            payload, 
            on_conflict="person_id,tag_type,related_person_id"
        ).execute()
        return True
    except Exception:
        return False


def get_relationship_tags(
    person_id: str = "",
    agent_id: str = "",
    tag_type: str = "",
    is_active: bool = True,
) -> list[dict]:
    """
    [GP-PHASE1] 관계망 태그 조회 (필터링 지원).
    
    Args:
        person_id: 특정 고객의 태그만 조회
        agent_id: 특정 설계사의 태그만 조회
        tag_type: 특정 태그 유형만 조회
        is_active: 활성 태그만 조회 (기본 True)
    """
    sb = _get_sb()
    if not sb:
        return []
    
    try:
        q = sb.table("gk_relationship_tags").select("*")
        
        if person_id:
            q = q.eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        if tag_type:
            q = q.eq("tag_type", tag_type)
        if is_active is not None:
            q = q.eq("is_active", is_active)
        
        return q.order("created_at", desc=True).execute().data or []
    except Exception:
        return []


def remove_relationship_tag(tag_id: str) -> bool:
    """[GP-PHASE1] 관계망 태그 비활성화 (Soft Delete)."""
    sb = _get_sb()
    if not sb or not tag_id:
        return False
    
    try:
        sb.table("gk_relationship_tags").update({
            "is_active": False,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }).eq("tag_id", tag_id).execute()
        return True
    except Exception:
        return False


def get_network_summary(person_id: str, agent_id: str) -> dict:
    """
    [GP-PHASE1] 고객의 8가지 관계망 네트워크 요약.
    
    Returns:
        {"상담자": 3, "계약자": 5, "피보험자": 2, ...}
    """
    if not person_id:
        return {}
    
    tags = get_relationship_tags(person_id=person_id, agent_id=agent_id)
    summary = {tag_type: 0 for tag_type in VALID_TAG_TYPES}
    
    for tag in tags:
        tag_type = tag.get("tag_type", "")
        if tag_type in summary:
            summary[tag_type] += 1
    
    return summary


# ══════════════════════════════════════════════════════════════════════════════
# §20 [GP-PHASE1] 보험계약 상세 이력 (gk_insurance_contracts_detail)
# ══════════════════════════════════════════════════════════════════════════════

VALID_CONTRACT_STATUS = ["자사계약", "타부점계약", "해지계약"]


def add_insurance_contract(
    person_id: str,
    agent_id: str,
    contract_status: str,
    insurance_company: str = "",
    product_name: str = "",
    contract_date: str = "",
    contractor_name: str = "",
    insured_name: str = "",
    monthly_premium: float = 0,
    key_point: str = "",
    termination_date: str = "",
    termination_reason: str = "",
) -> bool:
    """
    [GP-PHASE1] 보험계약 이력 추가 (자사/타부점/해지 분류).
    
    Args:
        contract_status: '자사계약' | '타부점계약' | '해지계약'
        contractor_name, insured_name: Fernet 암호화 권장 (호출 측에서 처리)
    """
    sb = _get_sb()
    if not sb or not person_id or not agent_id:
        return False
    if contract_status not in VALID_CONTRACT_STATUS:
        raise ValueError(f"유효하지 않은 contract_status: {contract_status}")
    
    try:
        payload = {
            "person_id": person_id,
            "agent_id": agent_id,
            "contract_status": contract_status,
            "insurance_company": insurance_company or None,
            "product_name": product_name or None,
            "contract_date": contract_date or None,
            "contractor_name": contractor_name or None,
            "insured_name": insured_name or None,
            "monthly_premium": monthly_premium if monthly_premium else None,
            "key_point": key_point or None,
            "termination_date": termination_date or None,
            "termination_reason": termination_reason or None,
            "is_deleted": False,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }
        sb.table("gk_insurance_contracts_detail").insert(payload).execute()
        return True
    except Exception:
        return False


def get_insurance_contracts(
    person_id: str = "",
    agent_id: str = "",
    contract_status: str = "",
) -> list[dict]:
    """[GP-PHASE1] 보험계약 이력 조회 (필터링 지원)."""
    sb = _get_sb()
    if not sb:
        return []
    
    try:
        q = sb.table("gk_insurance_contracts_detail").select("*").eq("is_deleted", False)
        
        if person_id:
            q = q.eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        if contract_status:
            q = q.eq("contract_status", contract_status)
        
        return q.order("contract_date", desc=True).execute().data or []
    except Exception:
        return []


def update_insurance_contract(contract_id: str, updates: dict) -> bool:
    """[GP-PHASE1] 보험계약 정보 수정."""
    sb = _get_sb()
    if not sb or not contract_id or not updates:
        return False
    
    try:
        updates["updated_at"] = datetime.datetime.utcnow().isoformat()
        sb.table("gk_insurance_contracts_detail").update(updates).eq("contract_id", contract_id).execute()
        return True
    except Exception:
        return False


def delete_insurance_contract(contract_id: str) -> bool:
    """[GP-PHASE1] 보험계약 Soft Delete."""
    sb = _get_sb()
    if not sb or not contract_id:
        return False
    
    try:
        sb.table("gk_insurance_contracts_detail").update({
            "is_deleted": True,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }).eq("contract_id", contract_id).execute()
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §21 [GP-PHASE1] 상담 일정 및 내용 (gk_consultation_schedule)
# ══════════════════════════════════════════════════════════════════════════════

VALID_CONSULTATION_TYPES = [
    "초회상담", "보장분석", "증권점검", 
    "계약체결", "사후관리", "기타"
]


def add_consultation_schedule(
    person_id: str,
    agent_id: str,
    schedule_date: str = "",
    schedule_time: str = "",
    consultation_type: str = "초회상담",
    consultation_content: str = "",
    consultation_result: str = "",
    next_action: str = "",
) -> bool:
    """
    [GP-PHASE1] 상담 일정 추가.
    
    Args:
        schedule_date: YYYYMMDD
        schedule_time: HHMM
        consultation_type: 초회상담/보장분석/증권점검/계약체결/사후관리/기타
    """
    sb = _get_sb()
    if not sb or not person_id or not agent_id:
        return False
    if consultation_type not in VALID_CONSULTATION_TYPES:
        raise ValueError(f"유효하지 않은 consultation_type: {consultation_type}")
    
    try:
        payload = {
            "person_id": person_id,
            "agent_id": agent_id,
            "schedule_date": schedule_date or None,
            "schedule_time": schedule_time or None,
            "consultation_type": consultation_type,
            "consultation_content": consultation_content or None,
            "consultation_result": consultation_result or None,
            "next_action": next_action or None,
            "is_completed": False,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }
        sb.table("gk_consultation_schedule").insert(payload).execute()
        return True
    except Exception:
        return False


def get_consultation_schedules(
    person_id: str = "",
    agent_id: str = "",
    is_completed: Optional[bool] = None,
) -> list[dict]:
    """[GP-PHASE1] 상담 일정 조회."""
    sb = _get_sb()
    if not sb:
        return []
    
    try:
        q = sb.table("gk_consultation_schedule").select("*")
        
        if person_id:
            q = q.eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        if is_completed is not None:
            q = q.eq("is_completed", is_completed)
        
        return q.order("schedule_date", desc=True).execute().data or []
    except Exception:
        return []


def complete_consultation(
    consultation_id: str,
    consultation_result: str = "",
    next_action: str = "",
) -> bool:
    """[GP-PHASE1] 상담 완료 처리."""
    sb = _get_sb()
    if not sb or not consultation_id:
        return False
    
    try:
        updates = {
            "is_completed": True,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }
        if consultation_result:
            updates["consultation_result"] = consultation_result
        if next_action:
            updates["next_action"] = next_action
        
        sb.table("gk_consultation_schedule").update(updates).eq("consultation_id", consultation_id).execute()
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §22 [GP-PHASE1] 이중화 백업 조회 (gk_people_backup)
# ══════════════════════════════════════════════════════════════════════════════

def get_backup_history(person_id: str, limit: int = 10) -> list[dict]:
    """
    [GP-PHASE1] 고객 정보 백업 이력 조회.
    
    Returns:
        최신 백업부터 limit개 반환
    """
    sb = _get_sb()
    if not sb or not person_id:
        return []
    
    try:
        return (
            sb.table("gk_people_backup")
            .select("*")
            .eq("person_id", person_id)
            .order("backup_created_at", desc=True)
            .limit(limit)
            .execute().data or []
        )
    except Exception:
        return []


def restore_from_backup(backup_id: str) -> bool:
    """
    [GP-PHASE1] 백업에서 고객 정보 복원.
    
    Warning: 이 함수는 gk_people 테이블을 직접 수정합니다.
    """
    sb = _get_sb()
    if not sb or not backup_id:
        return False
    
    try:
        backup = (
            sb.table("gk_people_backup")
            .select("*")
            .eq("backup_id", backup_id)
            .execute().data or []
        )
        if not backup:
            return False
        
        b = backup[0]
        person_id = b.get("person_id")
        if not person_id:
            return False
        
        restore_data = {
            "name": b.get("name"),
            "birth_date": b.get("birth_date"),
            "gender": b.get("gender"),
            "contact": b.get("contact"),
            "address": b.get("address"),
            "job": b.get("job"),
            "injury_level": b.get("injury_level"),
            "is_real_client": b.get("is_real_client"),
            "agent_id": b.get("agent_id"),
            "memo": b.get("memo"),
            "status": b.get("status"),
            "is_favorite": b.get("is_favorite"),
            "auto_renewal_month": b.get("auto_renewal_month"),
            "fire_renewal_month": b.get("fire_renewal_month"),
            "last_auto_carrier": b.get("last_auto_carrier"),
            "management_tier": b.get("management_tier"),
            "wedding_anniversary": b.get("wedding_anniversary"),
            "driving_status": b.get("driving_status"),
            "risk_note": b.get("risk_note"),
            "lead_source": b.get("lead_source"),
            "referrer_id": b.get("referrer_id"),
            "referrer_relation": b.get("referrer_relation"),
            "community_tags": b.get("community_tags"),
            "prospecting_stage": b.get("prospecting_stage"),
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }
        
        restore_data = {k: v for k, v in restore_data.items() if v is not None}
        
        sb.table("gk_people").update(restore_data).eq("person_id", person_id).execute()
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §23 [GP-PHASE2] 트리니티 분석 결과 영구 저장 (gk_trinity_analysis)
# ══════════════════════════════════════════════════════════════════════════════

def save_trinity_analysis(
    person_id: str,
    agent_id: str,
    nhis_premium: float,
    analysis_data: dict,
    monthly_required: float,
    gross_monthly: float = 0,
    gross_annual: float = 0,
    net_annual: float = 0,
    deduction_rate: float = 0,
    income_breakdown: dict = None,
    coverage_needs: dict = None,
    kb7_metadata: list = None,
    report_summary: str = "",
    ai_closing_comment: str = "",
    employment_type: str = "직장",
    ltc_included: bool = False,
) -> str:
    """
    [GP-PHASE2] 트리니티 분석 결과를 gk_trinity_analysis 테이블에 저장.
    
    Returns:
        analysis_id (UUID) — 저장된 분석 ID
    """
    sb = _get_sb()
    if not sb or not person_id or not agent_id:
        return ""
    
    try:
        import json as _j
        now = datetime.datetime.utcnow().isoformat()
        
        payload = {
            "person_id": person_id,
            "agent_id": agent_id,
            "analyzed_at": now,
            "analysis_version": "v1.0",
            "nhis_premium": float(nhis_premium) if nhis_premium else None,
            "gross_monthly": float(gross_monthly) if gross_monthly else None,
            "gross_annual": float(gross_annual) if gross_annual else None,
            "net_annual": float(net_annual) if net_annual else None,
            "monthly_required": float(monthly_required) if monthly_required else None,
            "deduction_rate": float(deduction_rate) if deduction_rate else None,
            "analysis_data": _j.dumps(analysis_data, ensure_ascii=False) if analysis_data else "{}",
            "income_breakdown": _j.dumps(income_breakdown, ensure_ascii=False) if income_breakdown else None,
            "coverage_needs": _j.dumps(coverage_needs, ensure_ascii=False) if coverage_needs else None,
            "kb7_metadata": _j.dumps(kb7_metadata, ensure_ascii=False) if kb7_metadata else None,
            "report_summary": report_summary or None,
            "ai_closing_comment": ai_closing_comment or None,
            "employment_type": employment_type or "직장",
            "ltc_included": ltc_included,
            "created_at": now,
            "updated_at": now,
        }
        
        result = sb.table("gk_trinity_analysis").insert(payload).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("analysis_id", "")
        return ""
    except Exception:
        return ""


def get_trinity_analysis_history(
    person_id: str = "",
    agent_id: str = "",
    limit: int = 10,
) -> list[dict]:
    """
    [GP-PHASE2] 트리니티 분석 이력 조회.
    
    Returns:
        최신 분석부터 limit개 반환
    """
    sb = _get_sb()
    if not sb:
        return []
    
    try:
        import json as _j
        q = sb.table("gk_trinity_analysis").select("*")
        
        if person_id:
            q = q.eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        
        rows = q.order("analyzed_at", desc=True).limit(limit).execute().data or []
        
        for r in rows:
            for json_field in ["analysis_data", "income_breakdown", "coverage_needs", "kb7_metadata"]:
                if r.get(json_field) and isinstance(r[json_field], str):
                    try:
                        r[json_field] = _j.loads(r[json_field])
                    except Exception:
                        pass
        
        return rows
    except Exception:
        return []


def get_latest_trinity_analysis(person_id: str, agent_id: str = "") -> dict:
    """
    [GP-PHASE2] 최신 트리니티 분석 결과 조회.
    
    Returns:
        최신 분석 결과 1건 (없으면 빈 dict)
    """
    history = get_trinity_analysis_history(person_id=person_id, agent_id=agent_id, limit=1)
    return history[0] if history else {}


# ══════════════════════════════════════════════════════════════════════════════
# §24 [GP-PHASE2] KB 분석 결과 영구 저장 (gk_kb_analysis)
# ══════════════════════════════════════════════════════════════════════════════

def save_kb_analysis(
    person_id: str,
    agent_id: str,
    analysis_data: dict,
    kb_total_score: float,
    kb_grade: str,
    customer_age: int = None,
    customer_gender: str = "",
    category_scores: list = None,
    gap_analysis: dict = None,
    kosis_weights: dict = None,
    report_summary: str = "",
    ai_summary: str = "",
    recommendations: str = "",
    raw_coverages: list = None,
) -> str:
    """
    [GP-PHASE2] KB 분석 결과를 gk_kb_analysis 테이블에 저장.
    
    Returns:
        analysis_id (UUID) — 저장된 분석 ID
    """
    sb = _get_sb()
    if not sb or not person_id or not agent_id:
        return ""
    
    try:
        import json as _j
        now = datetime.datetime.utcnow().isoformat()
        
        payload = {
            "person_id": person_id,
            "agent_id": agent_id,
            "analyzed_at": now,
            "analysis_version": "v1.0",
            "customer_age": int(customer_age) if customer_age else None,
            "customer_gender": customer_gender or None,
            "kb_total_score": float(kb_total_score) if kb_total_score else None,
            "kb_grade": kb_grade or None,
            "analysis_data": _j.dumps(analysis_data, ensure_ascii=False) if analysis_data else "{}",
            "category_scores": _j.dumps(category_scores, ensure_ascii=False) if category_scores else None,
            "gap_analysis": _j.dumps(gap_analysis, ensure_ascii=False) if gap_analysis else None,
            "kosis_weights": _j.dumps(kosis_weights, ensure_ascii=False) if kosis_weights else None,
            "report_summary": report_summary or None,
            "ai_summary": ai_summary or None,
            "recommendations": recommendations or None,
            "raw_coverages": _j.dumps(raw_coverages, ensure_ascii=False) if raw_coverages else None,
            "created_at": now,
            "updated_at": now,
        }
        
        result = sb.table("gk_kb_analysis").insert(payload).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("analysis_id", "")
        return ""
    except Exception:
        return ""


def get_kb_analysis_history(
    person_id: str = "",
    agent_id: str = "",
    limit: int = 10,
) -> list[dict]:
    """
    [GP-PHASE2] KB 분석 이력 조회.
    
    Returns:
        최신 분석부터 limit개 반환
    """
    sb = _get_sb()
    if not sb:
        return []
    
    try:
        import json as _j
        q = sb.table("gk_kb_analysis").select("*")
        
        if person_id:
            q = q.eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        
        rows = q.order("analyzed_at", desc=True).limit(limit).execute().data or []
        
        for r in rows:
            for json_field in ["analysis_data", "category_scores", "gap_analysis", "kosis_weights", "raw_coverages"]:
                if r.get(json_field) and isinstance(r[json_field], str):
                    try:
                        r[json_field] = _j.loads(r[json_field])
                    except Exception:
                        pass
        
        return rows
    except Exception:
        return []


def get_latest_kb_analysis(person_id: str, agent_id: str = "") -> dict:
    """
    [GP-PHASE2] 최신 KB 분석 결과 조회.
    
    Returns:
        최신 분석 결과 1건 (없으면 빈 dict)
    """
    history = get_kb_analysis_history(person_id=person_id, agent_id=agent_id, limit=1)
    return history[0] if history else {}


# ══════════════════════════════════════════════════════════════════════════════
# §25 [GP-PHASE2] 통합 분석 결과 저장 (gk_integrated_analysis)
# ══════════════════════════════════════════════════════════════════════════════

def save_integrated_analysis(
    person_id: str,
    agent_id: str,
    analysis_type: str,
    trinity_analysis_id: str = "",
    kb_analysis_id: str = "",
    integrated_score: float = 0,
    integrated_grade: str = "",
    integrated_report: dict = None,
    bridge_packet: dict = None,
    nibo_status: str = "pending",
    nibo_data: dict = None,
) -> str:
    """
    [GP-PHASE2] 통합 분석 결과를 gk_integrated_analysis 테이블에 저장.
    
    Args:
        analysis_type: 'full' | 'trinity_only' | 'kb_only'
    
    Returns:
        analysis_id (UUID) — 저장된 분석 ID
    """
    sb = _get_sb()
    if not sb or not person_id or not agent_id:
        return ""
    
    try:
        import json as _j
        now = datetime.datetime.utcnow().isoformat()
        
        payload = {
            "person_id": person_id,
            "agent_id": agent_id,
            "analyzed_at": now,
            "analysis_type": analysis_type,
            "trinity_analysis_id": trinity_analysis_id or None,
            "kb_analysis_id": kb_analysis_id or None,
            "integrated_score": float(integrated_score) if integrated_score else None,
            "integrated_grade": integrated_grade or None,
            "integrated_report": _j.dumps(integrated_report, ensure_ascii=False) if integrated_report else None,
            "bridge_packet": _j.dumps(bridge_packet, ensure_ascii=False) if bridge_packet else None,
            "nibo_status": nibo_status or "pending",
            "nibo_data": _j.dumps(nibo_data, ensure_ascii=False) if nibo_data else None,
            "created_at": now,
            "updated_at": now,
        }
        
        result = sb.table("gk_integrated_analysis").insert(payload).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("analysis_id", "")
        return ""
    except Exception:
        return ""


def get_integrated_analysis_history(
    person_id: str = "",
    agent_id: str = "",
    limit: int = 10,
) -> list[dict]:
    """
    [GP-PHASE2] 통합 분석 이력 조회.
    
    Returns:
        최신 분석부터 limit개 반환
    """
    sb = _get_sb()
    if not sb:
        return []
    
    try:
        import json as _j
        q = sb.table("gk_integrated_analysis").select("*")
        
        if person_id:
            q = q.eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        
        rows = q.order("analyzed_at", desc=True).limit(limit).execute().data or []
        
        for r in rows:
            for json_field in ["integrated_report", "bridge_packet", "nibo_data"]:
                if r.get(json_field) and isinstance(r[json_field], str):
                    try:
                        r[json_field] = _j.loads(r[json_field])
                    except Exception:
                        pass
        
        return rows
    except Exception:
        return []


def get_latest_integrated_analysis(person_id: str, agent_id: str = "") -> dict:
    """
    [GP-PHASE2] 최신 통합 분석 결과 조회.
    
    Returns:
        최신 분석 결과 1건 (없으면 빈 dict)
    """
    history = get_integrated_analysis_history(person_id=person_id, agent_id=agent_id, limit=1)
    return history[0] if history else {}


# ══════════════════════════════════════════════════════════════════════════════
# §PHASE3 스캔 파일 및 의무기록 관리
# ══════════════════════════════════════════════════════════════════════════════

def save_scan_file(
    person_id: str,
    agent_id: str,
    file_type: str,
    gcs_path: str,
    file_name: str = "",
    gcs_bucket: str = "",
    file_size_bytes: int = 0,
    mime_type: str = "",
    tags: list = None,
    category: str = "",
    extracted_text: str = "",
    extracted_fields: dict = None,
) -> str:
    """
    [GP-PHASE3] 스캔 파일 메타데이터를 gk_scan_files 테이블에 저장.
    
    Args:
        person_id: 고객 ID (SHA-256 해시)
        agent_id: 설계사 ID
        file_type: 'policy', 'medical', 'receipt', 'claim', 'other'
        gcs_path: GCS 전체 경로 (gs://bucket/path/to/file.pdf)
        file_name: 원본 파일명
        gcs_bucket: GCS 버킷명
        file_size_bytes: 파일 크기
        mime_type: MIME 타입
        tags: 검색용 태그 배열
        category: 세부 카테고리
        extracted_text: OCR 추출 텍스트
        extracted_fields: 파싱된 필드 (dict)
    
    Returns:
        scan_id (UUID string) 또는 빈 문자열
    """
    sb = _get_sb()
    if not sb:
        return ""
    
    try:
        import json as _j
        from datetime import datetime as _dt
        
        now = _dt.utcnow().isoformat()
        
        payload = {
            "person_id": person_id,
            "agent_id": agent_id,
            "file_type": file_type,
            "file_name": file_name or "",
            "gcs_path": gcs_path,
            "gcs_bucket": gcs_bucket or "",
            "file_size_bytes": file_size_bytes,
            "mime_type": mime_type or "",
            "ocr_status": "completed" if extracted_text else "pending",
            "extracted_text": extracted_text or "",
            "extracted_fields": _j.dumps(extracted_fields, ensure_ascii=False) if extracted_fields else None,
            "tags": tags or [],
            "category": category or "",
            "is_encrypted": True,
            "uploaded_at": now,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
        }
        
        result = sb.table("gk_scan_files").insert(payload).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("scan_id", "")
        return ""
    except Exception:
        return ""


def save_medical_record(
    scan_id: str,
    person_id: str,
    agent_id: str,
    record_type: str = "",
    hospital_name: str = "",
    doctor_name: str = "",
    visit_date: str = "",
    diagnosis_codes: list = None,
    diagnosis_names: list = None,
    prescriptions: dict = None,
    lab_results: dict = None,
    ocr_raw_text: str = "",
    ocr_confidence: float = 0.0,
    structured_data: dict = None,
    ai_summary: str = "",
    risk_flags: list = None,
    insurance_relevance_score: float = 0.0,
) -> str:
    """
    [GP-PHASE3] 의무기록 OCR 분석 결과를 gk_medical_records 테이블에 저장.
    
    Args:
        scan_id: 원본 스캔 파일 ID (gk_scan_files.scan_id)
        person_id: 고객 ID
        agent_id: 설계사 ID
        record_type: 'diagnosis', 'prescription', 'lab_result', 'surgery', 'consultation'
        hospital_name: 병원명
        doctor_name: 의사명
        visit_date: 진료 날짜 (YYYY-MM-DD)
        diagnosis_codes: ICD-10 코드 배열
        diagnosis_names: 진단명 배열
        prescriptions: 처방 내역 (dict)
        lab_results: 검사 결과 (dict)
        ocr_raw_text: OCR 추출 원문
        ocr_confidence: OCR 신뢰도 (0.0 ~ 1.0)
        structured_data: 파싱된 전체 데이터
        ai_summary: AI 요약
        risk_flags: 위험 플래그 배열
        insurance_relevance_score: 보험 관련성 점수
    
    Returns:
        record_id (UUID string) 또는 빈 문자열
    """
    sb = _get_sb()
    if not sb:
        return ""
    
    try:
        import json as _j
        from datetime import datetime as _dt
        
        now = _dt.utcnow().isoformat()
        
        payload = {
            "scan_id": scan_id,
            "person_id": person_id,
            "agent_id": agent_id,
            "record_type": record_type or "other",
            "hospital_name": hospital_name or "",
            "doctor_name": doctor_name or "",
            "visit_date": visit_date or None,
            "diagnosis_codes": diagnosis_codes or [],
            "diagnosis_names": diagnosis_names or [],
            "prescriptions": _j.dumps(prescriptions, ensure_ascii=False) if prescriptions else None,
            "lab_results": _j.dumps(lab_results, ensure_ascii=False) if lab_results else None,
            "ocr_raw_text": ocr_raw_text or "",
            "ocr_confidence": float(ocr_confidence) if ocr_confidence else 0.0,
            "structured_data": _j.dumps(structured_data, ensure_ascii=False) if structured_data else None,
            "ai_summary": ai_summary or "",
            "risk_flags": risk_flags or [],
            "insurance_relevance_score": float(insurance_relevance_score) if insurance_relevance_score else 0.0,
            "is_encrypted": True,
            "processed_at": now,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
        }
        
        result = sb.table("gk_medical_records").insert(payload).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get("record_id", "")
        return ""
    except Exception:
        return ""


def get_scan_files(
    person_id: str = "",
    agent_id: str = "",
    file_type: str = "",
    limit: int = 50,
) -> list[dict]:
    """
    [GP-PHASE3] 스캔 파일 메타데이터 조회.
    
    Args:
        person_id: 고객 ID 필터
        agent_id: 설계사 ID 필터
        file_type: 파일 타입 필터 ('policy', 'medical', 'receipt', 'claim')
        limit: 최대 조회 건수
    
    Returns:
        스캔 파일 목록 (최신순)
    """
    sb = _get_sb()
    if not sb:
        return []
    
    try:
        import json as _j
        q = sb.table("gk_scan_files").select("*")
        
        if person_id:
            q = q.eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        if file_type:
            q = q.eq("file_type", file_type)
        
        q = q.eq("is_active", True)
        rows = q.order("uploaded_at", desc=True).limit(limit).execute().data or []
        
        for r in rows:
            if r.get("extracted_fields") and isinstance(r["extracted_fields"], str):
                try:
                    r["extracted_fields"] = _j.loads(r["extracted_fields"])
                except Exception:
                    pass
        
        return rows
    except Exception:
        return []


def get_medical_records(
    person_id: str = "",
    agent_id: str = "",
    scan_id: str = "",
    limit: int = 50,
) -> list[dict]:
    """
    [GP-PHASE3] 의무기록 분석 결과 조회.
    
    Args:
        person_id: 고객 ID 필터
        agent_id: 설계사 ID 필터
        scan_id: 스캔 파일 ID 필터
        limit: 최대 조회 건수
    
    Returns:
        의무기록 목록 (최신순)
    """
    sb = _get_sb()
    if not sb:
        return []
    
    try:
        import json as _j
        q = sb.table("gk_medical_records").select("*")
        
        if person_id:
            q = q.eq("person_id", person_id)
        if agent_id:
            q = q.eq("agent_id", agent_id)
        if scan_id:
            q = q.eq("scan_id", scan_id)
        
        q = q.eq("is_active", True)
        rows = q.order("processed_at", desc=True).limit(limit).execute().data or []
        
        for r in rows:
            for json_field in ["prescriptions", "lab_results", "structured_data"]:
                if r.get(json_field) and isinstance(r[json_field], str):
                    try:
                        r[json_field] = _j.loads(r[json_field])
                    except Exception:
                        pass
        
        return rows
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# §13 보험 만기 자동 관리 (Insurance Expiry Automation)
# ══════════════════════════════════════════════════════════════════════════════

def get_expiry_alerts(
    agent_id: str,
    days_range: int = 30,
    priority_only: bool = True,
) -> list[dict]:
    """
    [GP-EXPIRY] 보험 만기 알림 대상자 조회.
    
    D-28일(4주전), D-14일(2주전) 만기 대상 고객을 조회하여
    STEP 2. 영업일정 점검 화면에 표시합니다.
    
    Args:
        agent_id: 설계사 ID
        days_range: 조회 범위 (기본 30일, 만기일 30일 전부터)
        priority_only: True이면 D-28, D-14 우선순위만 조회
    
    Returns:
        만기 대상자 리스트 [
            {
                "schedule_id": str,
                "person_id": str,
                "policy_id": str,
                "customer_name": str,
                "title": str,
                "expiry_date": str,
                "tags": list[str],
                "memo": str,
                "sub_type": str,
                "product_name": str,
                "insurance_company": str,
                "days_until_expiry": int,
                "alert_priority": int,  # 1=D-28, 2=D-14, 0=기타
            }
        ]
    """
    sb = _get_sb()
    if not sb or not agent_id:
        return []
    
    try:
        # v_expiry_alerts 뷰 조회
        query = sb.table("v_expiry_alerts").select("*").eq("agent_id", agent_id)
        
        # 우선순위 필터링 (D-28, D-14만)
        if priority_only:
            query = query.in_("alert_priority", [1, 2])
        
        # 날짜 범위 필터링
        query = query.lte("days_until_expiry", days_range).gte("days_until_expiry", 0)
        
        # 만기일 가까운 순으로 정렬
        alerts = query.order("expiry_date", desc=False).execute().data or []
        
        return alerts
    except Exception as e:
        import logging
        logging.warning(f"[GP-EXPIRY] 만기 알림 조회 실패: {e}")
        return []


def generate_expiry_renewal_message(
    customer_name: str,
    sub_type: str,
    expiry_date: str,
    days_until: int,
    insurance_company: str = "",
    product_name: str = "",
) -> str:
    """
    [GP-EXPIRY] 만기 재가입 안내용 감성 멘트 생성.
    
    Args:
        customer_name: 고객명
        sub_type: 보험 세부 유형 (자동차, 화재 등)
        expiry_date: 만기일 (YYYY-MM-DD)
        days_until: 만기까지 남은 일수
        insurance_company: 보험사명 (선택)
        product_name: 상품명 (선택)
    
    Returns:
        카카오톡 발송용 감성 메시지
    """
    # 만기일 포맷팅
    try:
        exp_date = datetime.datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
        exp_date_kr = exp_date.strftime("%Y년 %m월 %d일")
    except Exception:
        exp_date_kr = expiry_date
    
    # 보험 유형별 맞춤 멘트
    if "자동차" in (sub_type or ""):
        insurance_type = "자동차보험"
        renewal_tip = "운전 습관과 주행거리에 따라 보험료가 달라질 수 있으니, 갱신 전 꼭 비교 견적을 받아보세요!"
    elif "화재" in (sub_type or ""):
        insurance_type = "화재보험"
        renewal_tip = "건물 가치 변동과 보장 범위를 재점검하여 최적의 보장을 유지하세요."
    elif "배상" in (sub_type or ""):
        insurance_type = "배상책임보험"
        renewal_tip = "사업장 규모나 매출 변화에 따라 보장 한도를 조정하시는 것이 좋습니다."
    else:
        insurance_type = sub_type or "보험"
        renewal_tip = "보장 내용을 재점검하고 필요한 부분을 보완하세요."
    
    # D-Day 표현
    if days_until <= 7:
        urgency = "⚠️ 만기가 임박했습니다!"
    elif days_until <= 14:
        urgency = "🔔 만기 2주 전입니다."
    elif days_until <= 28:
        urgency = "📅 만기 4주 전 안내드립니다."
    else:
        urgency = "📋 만기 예정 안내"
    
    # 메시지 생성
    message = f"""안녕하세요, {customer_name} 고객님! 😊

{urgency}

현재 가입하신 {insurance_type}이 곧 만기됩니다.

📌 만기일: {exp_date_kr} (D-{days_until})
"""
    
    if insurance_company:
        message += f"📌 보험사: {insurance_company}\n"
    if product_name:
        message += f"📌 상품명: {product_name}\n"
    
    message += f"""
💡 {renewal_tip}

보장 공백이 생기지 않도록 미리 재가입 상담을 도와드리겠습니다.
편하신 시간에 연락 주시면 최적의 조건으로 안내해드리겠습니다!

감사합니다. 🙏
"""
    
    return message
