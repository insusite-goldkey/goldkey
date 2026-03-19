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
