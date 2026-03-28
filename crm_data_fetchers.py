"""
CRM → 데이터 소스 추상화 (향후 Head API / Cloud Run 게이트웨이로 교체 용이).
현재는 db_utils 직접 호출 — UI 블록은 이 모듈만 사용하도록 점진 이전 권장.
"""
from __future__ import annotations


def fetch_customers_for_agent(agent_id: str, query: str = "") -> list:
    try:
        from head_api_client import list_customer_records

        r = list_customer_records(user_id=agent_id, query=query, include_deleted=False)
        if isinstance(r, dict) and r.get("ok") and isinstance(r.get("items"), list):
            return r["items"]
    except Exception:
        pass
    from db_utils import load_customers

    return load_customers(agent_id, query)


def fetch_schedules_for_agent(agent_id: str) -> list:
    from db_utils import load_schedules

    return load_schedules(agent_id)


def upsert_customer_for_agent(
    *,
    user_id: str,
    person_id: str,
    patch: dict,
    expected_version: int | None = None,
    local_data: dict | None = None,  # [지시1] 충돌 감지용 로컬 데이터
) -> dict:
    """
    HEAD API 우선 저장. 실패 시 db_utils safe_update_customer 폴백.
    
    [지시1] Optimistic Concurrency Control + Richer Data Wins:
        - DB의 최신 데이터와 비교하여 충돌 감지
        - 충돌 시 저장 중단 및 에러 반환
    """
    # [지시1] 충돌 감지 (local_data 제공 시)
    if local_data:
        try:
            from modules.concurrency_guard import check_conflict
            from db_utils import load_customers
            
            # DB에서 최신 데이터 조회
            remote_customers = load_customers(user_id, "")
            remote_data = None
            for c in remote_customers:
                if c.get("person_id") == person_id or c.get("id") == person_id:
                    remote_data = c
                    break
            
            # 충돌 검사
            has_conflict, conflict_reason = check_conflict(local_data, remote_data or {})
            
            if has_conflict:
                return {
                    "ok": False,
                    "conflict": True,
                    "error": conflict_reason,
                    "remote_data": remote_data
                }
        except Exception:
            pass  # 충돌 검사 실패 시 계속 진행
    
    # 기존 로직 (HEAD API 우선)
    try:
        from head_api_client import upsert_customer_record

        r = upsert_customer_record(
            user_id=user_id,
            person_id=person_id,
            patch=patch,
            expected_version=expected_version,
        )
        if isinstance(r, dict) and r.get("ok"):
            return r
    except Exception:
        pass
    try:
        from db_utils import merge_customer_fields

        ok = merge_customer_fields(person_id, user_id, patch)
        return {"ok": bool(ok), "conflict": False, "record": patch if ok else None}
    except Exception as e:
        return {"ok": False, "conflict": False, "error": str(e)}
