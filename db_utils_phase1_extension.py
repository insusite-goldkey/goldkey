"""
db_utils_phase1_extension.py — Phase 1 다중 관계망 태깅 및 보안 확장 함수
이 파일의 함수들을 db_utils.py 하단에 추가하세요.

[GP-PHASE1] 8가지 관계망 태깅 + 보험계약 이력 + 상담일정 + 이중화 백업
"""
from __future__ import annotations
import datetime
from typing import Optional, Any


# ══════════════════════════════════════════════════════════════════════════════
# §19 [GP-PHASE1] 8가지 관계망 태깅 시스템 (gk_relationship_tags)
# ══════════════════════════════════════════════════════════════════════════════

VALID_TAG_TYPES = [
    "상담자", "계약자", "피보험자", "가족", 
    "소개자", "동일법인", "동일단체", "친인척"
]


def add_relationship_tag(
    sb: Any,
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
    except Exception as e:
        print(f"[GP-PHASE1] add_relationship_tag 오류: {e}")
        return False


def get_relationship_tags(
    sb: Any,
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
    except Exception as e:
        print(f"[GP-PHASE1] get_relationship_tags 오류: {e}")
        return []


def remove_relationship_tag(
    sb: Any,
    tag_id: str,
) -> bool:
    """
    [GP-PHASE1] 관계망 태그 비활성화 (Soft Delete).
    """
    if not sb or not tag_id:
        return False
    
    try:
        sb.table("gk_relationship_tags").update({
            "is_active": False,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }).eq("tag_id", tag_id).execute()
        return True
    except Exception as e:
        print(f"[GP-PHASE1] remove_relationship_tag 오류: {e}")
        return False


def get_network_summary(
    sb: Any,
    person_id: str,
    agent_id: str,
) -> dict:
    """
    [GP-PHASE1] 고객의 8가지 관계망 네트워크 요약.
    
    Returns:
        {
            "상담자": 3,
            "계약자": 5,
            "피보험자": 2,
            ...
        }
    """
    if not sb or not person_id:
        return {}
    
    tags = get_relationship_tags(sb, person_id=person_id, agent_id=agent_id)
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
    sb: Any,
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
    except Exception as e:
        print(f"[GP-PHASE1] add_insurance_contract 오류: {e}")
        return False


def get_insurance_contracts(
    sb: Any,
    person_id: str = "",
    agent_id: str = "",
    contract_status: str = "",
) -> list[dict]:
    """
    [GP-PHASE1] 보험계약 이력 조회 (필터링 지원).
    """
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
    except Exception as e:
        print(f"[GP-PHASE1] get_insurance_contracts 오류: {e}")
        return []


def update_insurance_contract(
    sb: Any,
    contract_id: str,
    updates: dict,
) -> bool:
    """
    [GP-PHASE1] 보험계약 정보 수정.
    """
    if not sb or not contract_id or not updates:
        return False
    
    try:
        updates["updated_at"] = datetime.datetime.utcnow().isoformat()
        sb.table("gk_insurance_contracts_detail").update(updates).eq("contract_id", contract_id).execute()
        return True
    except Exception as e:
        print(f"[GP-PHASE1] update_insurance_contract 오류: {e}")
        return False


def delete_insurance_contract(
    sb: Any,
    contract_id: str,
) -> bool:
    """
    [GP-PHASE1] 보험계약 Soft Delete.
    """
    if not sb or not contract_id:
        return False
    
    try:
        sb.table("gk_insurance_contracts_detail").update({
            "is_deleted": True,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        }).eq("contract_id", contract_id).execute()
        return True
    except Exception as e:
        print(f"[GP-PHASE1] delete_insurance_contract 오류: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §21 [GP-PHASE1] 상담 일정 및 내용 (gk_consultation_schedule)
# ══════════════════════════════════════════════════════════════════════════════

VALID_CONSULTATION_TYPES = [
    "초회상담", "보장분석", "증권점검", 
    "계약체결", "사후관리", "기타"
]


def add_consultation_schedule(
    sb: Any,
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
    except Exception as e:
        print(f"[GP-PHASE1] add_consultation_schedule 오류: {e}")
        return False


def get_consultation_schedules(
    sb: Any,
    person_id: str = "",
    agent_id: str = "",
    is_completed: Optional[bool] = None,
) -> list[dict]:
    """
    [GP-PHASE1] 상담 일정 조회.
    """
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
    except Exception as e:
        print(f"[GP-PHASE1] get_consultation_schedules 오류: {e}")
        return []


def complete_consultation(
    sb: Any,
    consultation_id: str,
    consultation_result: str = "",
    next_action: str = "",
) -> bool:
    """
    [GP-PHASE1] 상담 완료 처리.
    """
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
    except Exception as e:
        print(f"[GP-PHASE1] complete_consultation 오류: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §22 [GP-PHASE1] 이중화 백업 조회 (gk_people_backup)
# ══════════════════════════════════════════════════════════════════════════════

def get_backup_history(
    sb: Any,
    person_id: str,
    limit: int = 10,
) -> list[dict]:
    """
    [GP-PHASE1] 고객 정보 백업 이력 조회.
    
    Returns:
        최신 백업부터 limit개 반환
    """
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
    except Exception as e:
        print(f"[GP-PHASE1] get_backup_history 오류: {e}")
        return []


def restore_from_backup(
    sb: Any,
    backup_id: str,
) -> bool:
    """
    [GP-PHASE1] 백업에서 고객 정보 복원.
    
    Warning: 이 함수는 gk_people 테이블을 직접 수정합니다.
    """
    if not sb or not backup_id:
        return False
    
    try:
        # 백업 데이터 조회
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
        
        # gk_people 복원
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
        
        # None 값 제거
        restore_data = {k: v for k, v in restore_data.items() if v is not None}
        
        sb.table("gk_people").update(restore_data).eq("person_id", person_id).execute()
        return True
    except Exception as e:
        print(f"[GP-PHASE1] restore_from_backup 오류: {e}")
        return False
