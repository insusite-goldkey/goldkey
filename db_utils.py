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
    Supabase DB 저장 + GCS 암호화 아카이브 동시 수행.
    두 저장소 중 하나라도 성공하면 True 반환.
    """
    _db_ok  = False
    _gcs_ok = False

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
    _gcs_ok = upload_customer_profile_gcs(person_id, _gcs_data)

    return _db_ok or _gcs_ok


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
                        "customer_name": customer_name,
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
# §8 회원 (gk_members) — 인증 전용
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
    """AI 브리핑 저장 (agent_id 기준 upsert)."""
    sb = _get_sb()
    if not sb or not agent_id:
        return False
    try:
        sb.table("gk_ai_briefs").upsert({
            "agent_id":   agent_id,
            "brief_text": brief_text,
            "created_at": datetime.datetime.utcnow().isoformat(),
        }, on_conflict="agent_id").execute()
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
