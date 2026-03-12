"""
crm_fortress.py — 골드키 CRM 데이터 요새
GP 설계안 기반: people / relationships / policies / policy_roles / policy_coverages

사용법:
    from crm_fortress import upsert_person, upsert_policy, link_policy_role, get_person_policies
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

# ────────────────────────────────────────────────────────────────────────────
# 상수
# ────────────────────────────────────────────────────────────────────────────
T_PEOPLE    = "gk_people"
T_REL       = "gk_relationships"
T_POLICIES  = "gk_policies"
T_ROLES     = "gk_policy_roles"
T_COVERAGES = "gk_policy_coverages"

VALID_ROLES         = ("계약자", "피보험자", "수익자")
VALID_RELATIONS     = ("배우자", "자녀", "부모", "형제", "소개자", "법인직원", "기타")


# ────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ────────────────────────────────────────────────────────────────────────────
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(d: dict) -> dict:
    """None 값 제거 후 반환"""
    return {k: v for k, v in d.items() if v is not None}


# ────────────────────────────────────────────────────────────────────────────
# 1. People
# ────────────────────────────────────────────────────────────────────────────
def upsert_person(
    sb,
    name: str,
    birth_date: str = "",
    gender: str = "",
    contact: str = "",
    is_real_client: bool = False,
    agent_id: str = "",
    memo: str = "",
    person_id: str | None = None,
) -> dict:
    """
    인물 등록 또는 갱신.
    person_id 있으면 UPDATE, 없으면 name+agent_id+birth_date 기준으로 기존 검색 후 없으면 INSERT.
    반환: 저장된 행 dict (id 포함)
    """
    row = _clean({
        "name":           name.strip(),
        "birth_date":     birth_date or None,
        "gender":         gender or None,
        "contact":        contact or None,
        "is_real_client": is_real_client,
        "agent_id":       agent_id or None,
        "memo":           memo or None,
        "updated_at":     _now_iso(),
    })

    if person_id:
        res = (sb.table(T_PEOPLE)
               .update(row)
               .eq("id", person_id)
               .eq("is_deleted", False)
               .execute())
        data = res.data
        return data[0] if data else {"id": person_id}

    # 중복 검색: name + agent_id + birth_date
    q = sb.table(T_PEOPLE).select("*").eq("is_deleted", False).eq("name", name.strip())
    if agent_id:
        q = q.eq("agent_id", agent_id)
    if birth_date:
        q = q.eq("birth_date", birth_date)
    existing = q.execute().data or []
    if existing:
        ex = existing[0]
        sb.table(T_PEOPLE).update(row).eq("id", ex["id"]).execute()
        return {**ex, **row}

    row["id"] = str(uuid.uuid4())
    row["created_at"] = _now_iso()
    row["is_deleted"] = False
    res = sb.table(T_PEOPLE).insert(row).execute()
    return res.data[0] if res.data else row


def soft_delete_person(sb, person_id: str) -> bool:
    """인물 Soft Delete"""
    res = (sb.table(T_PEOPLE)
           .update({"is_deleted": True, "updated_at": _now_iso()})
           .eq("id", person_id)
           .execute())
    return bool(res.data)


def get_person(sb, person_id: str) -> dict | None:
    res = (sb.table(T_PEOPLE)
           .select("*")
           .eq("id", person_id)
           .eq("is_deleted", False)
           .execute())
    return res.data[0] if res.data else None


def search_people(sb, agent_id: str, query: str = "") -> list[dict]:
    """agent_id 기준 고객 검색 (이름 부분 일치)"""
    q = sb.table(T_PEOPLE).select("*").eq("agent_id", agent_id).eq("is_deleted", False)
    if query:
        q = q.ilike("name", f"%{query}%")
    return q.order("name").execute().data or []


# ────────────────────────────────────────────────────────────────────────────
# 2. Relationships
# ────────────────────────────────────────────────────────────────────────────
def upsert_relationship(
    sb,
    from_person_id: str,
    to_person_id: str,
    relation_type: str,
    agent_id: str = "",
    memo: str = "",
) -> dict:
    """관계 등록 (중복 시 갱신)"""
    assert relation_type in VALID_RELATIONS, f"유효하지 않은 relation_type: {relation_type}"
    row = _clean({
        "from_person_id": from_person_id,
        "to_person_id":   to_person_id,
        "relation_type":  relation_type,
        "agent_id":       agent_id or None,
        "memo":           memo or None,
        "is_deleted":     False,
    })
    res = (sb.table(T_REL)
           .upsert(row, on_conflict="from_person_id,to_person_id,relation_type")
           .execute())
    return res.data[0] if res.data else row


def get_relationships(sb, person_id: str) -> list[dict]:
    """해당 인물의 모든 관계 조회 (양방향)"""
    res_from = (sb.table(T_REL).select("*")
                .eq("from_person_id", person_id).eq("is_deleted", False).execute())
    res_to   = (sb.table(T_REL).select("*")
                .eq("to_person_id",   person_id).eq("is_deleted", False).execute())
    return (res_from.data or []) + (res_to.data or [])


# ────────────────────────────────────────────────────────────────────────────
# 3. Policies
# ────────────────────────────────────────────────────────────────────────────
def upsert_policy(
    sb,
    insurance_company: str,
    product_name: str,
    agent_id: str = "",
    policy_number: str = "",
    product_type: str = "",
    contract_date: str = "",
    expiry_date: str = "",
    premium: float | None = None,
    payment_period: str = "",
    coverage_period: str = "",
    raw_text: str = "",
    source: str = "manual",
    policy_id: str | None = None,
) -> dict:
    """
    증권 등록 또는 갱신.
    policy_id 있으면 UPDATE, 없으면 policy_number+agent_id 기준 검색 후 없으면 INSERT.
    """
    row = _clean({
        "insurance_company": insurance_company,
        "product_name":      product_name,
        "agent_id":          agent_id or None,
        "policy_number":     policy_number or None,
        "product_type":      product_type or None,
        "contract_date":     contract_date or None,
        "expiry_date":       expiry_date or None,
        "premium":           premium,
        "payment_period":    payment_period or None,
        "coverage_period":   coverage_period or None,
        "raw_text":          raw_text or None,
        "source":            source,
        "updated_at":        _now_iso(),
    })

    if policy_id:
        res = (sb.table(T_POLICIES).update(row)
               .eq("id", policy_id).eq("is_deleted", False).execute())
        return res.data[0] if res.data else {"id": policy_id}

    # 중복 검색
    if policy_number and agent_id:
        existing = (sb.table(T_POLICIES).select("*")
                    .eq("policy_number", policy_number)
                    .eq("agent_id", agent_id)
                    .eq("is_deleted", False)
                    .execute().data or [])
        if existing:
            ex = existing[0]
            sb.table(T_POLICIES).update(row).eq("id", ex["id"]).execute()
            return {**ex, **row}

    row["id"] = str(uuid.uuid4())
    row["created_at"] = _now_iso()
    row["is_deleted"] = False
    res = sb.table(T_POLICIES).insert(row).execute()
    return res.data[0] if res.data else row


def soft_delete_policy(sb, policy_id: str) -> bool:
    res = (sb.table(T_POLICIES)
           .update({"is_deleted": True, "updated_at": _now_iso()})
           .eq("id", policy_id)
           .execute())
    return bool(res.data)


# ────────────────────────────────────────────────────────────────────────────
# 4. Policy Roles (N:M 핵심 연결)
# ────────────────────────────────────────────────────────────────────────────
def link_policy_role(
    sb,
    policy_id: str,
    person_id: str,
    role: str,
    agent_id: str = "",
    memo: str = "",
) -> dict:
    """증권-인물-역할 연결 (계약자/피보험자/수익자)"""
    assert role in VALID_ROLES, f"유효하지 않은 role: {role}"
    row = _clean({
        "policy_id":  policy_id,
        "person_id":  person_id,
        "role":       role,
        "agent_id":   agent_id or None,
        "memo":       memo or None,
        "is_deleted": False,
    })
    res = (sb.table(T_ROLES)
           .upsert(row, on_conflict="policy_id,person_id,role")
           .execute())
    return res.data[0] if res.data else row


def unlink_policy_role(sb, policy_id: str, person_id: str, role: str) -> bool:
    """역할 연결 Soft Delete"""
    res = (sb.table(T_ROLES)
           .update({"is_deleted": True})
           .eq("policy_id", policy_id)
           .eq("person_id", person_id)
           .eq("role", role)
           .execute())
    return bool(res.data)


# ────────────────────────────────────────────────────────────────────────────
# 5. Policy Coverages
# ────────────────────────────────────────────────────────────────────────────
def upsert_coverage(
    sb,
    policy_id: str,
    coverage_name: str,
    coverage_amount: int | None = None,
    deductible: int | None = None,
    coverage_period: str = "",
    is_active: bool = True,
    agent_id: str = "",
) -> dict:
    row = _clean({
        "policy_id":       policy_id,
        "coverage_name":   coverage_name,
        "coverage_amount": coverage_amount,
        "deductible":      deductible,
        "coverage_period": coverage_period or None,
        "is_active":       is_active,
        "agent_id":        agent_id or None,
        "is_deleted":      False,
    })
    res = sb.table(T_COVERAGES).insert(row).execute()
    return res.data[0] if res.data else row


def bulk_upsert_coverages(sb, policy_id: str, coverages: list[dict], agent_id: str = "") -> int:
    """담보 목록 일괄 저장. 반환: 저장 건수"""
    count = 0
    for cov in coverages:
        try:
            upsert_coverage(
                sb, policy_id,
                coverage_name=cov.get("name", cov.get("coverage_name", "")),
                coverage_amount=cov.get("amount", cov.get("coverage_amount")),
                deductible=cov.get("deductible"),
                coverage_period=cov.get("period", cov.get("coverage_period", "")),
                is_active=cov.get("is_active", True),
                agent_id=agent_id,
            )
            count += 1
        except Exception:
            pass
    return count


# ────────────────────────────────────────────────────────────────────────────
# 6. 조회 — 핵심 쿼리
# ────────────────────────────────────────────────────────────────────────────
def get_person_policies(sb, person_id: str) -> dict:
    """
    특정 인물이 계약자/피보험자/수익자로 연결된 증권 전체 조회.
    반환: {"계약자": [...], "피보험자": [...], "수익자": [...]}
    """
    roles_res = (sb.table(T_ROLES).select("policy_id, role")
                 .eq("person_id", person_id)
                 .eq("is_deleted", False)
                 .execute().data or [])

    result: dict[str, list] = {"계약자": [], "피보험자": [], "수익자": []}
    for r in roles_res:
        pid = r["policy_id"]
        pol = (sb.table(T_POLICIES).select("*")
               .eq("id", pid).eq("is_deleted", False).execute().data or [])
        if pol:
            result[r["role"]].append(pol[0])
    return result


def get_policy_persons(sb, policy_id: str) -> dict:
    """
    특정 증권에 연결된 모든 인물 조회.
    반환: {"계약자": [...], "피보험자": [...], "수익자": [...]}
    """
    roles_res = (sb.table(T_ROLES).select("person_id, role")
                 .eq("policy_id", policy_id)
                 .eq("is_deleted", False)
                 .execute().data or [])

    result: dict[str, list] = {"계약자": [], "피보험자": [], "수익자": []}
    for r in roles_res:
        person = get_person(sb, r["person_id"])
        if person:
            result[r["role"]].append(person)
    return result


def get_agent_policies(sb, agent_id: str) -> list[dict]:
    """담당 FC의 전체 증권 목록"""
    return (sb.table(T_POLICIES).select("*")
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .execute().data or [])


# ────────────────────────────────────────────────────────────────────────────
# 7. 크롤링/OCR 파싱 결과 → 요새 구조로 분해 저장
# ────────────────────────────────────────────────────────────────────────────
def parse_crawled_policy(
    sb,
    raw: dict,
    agent_id: str,
) -> dict:
    """
    '내보험다보여' 크롤링 또는 OCR 파싱 결과(dict)를 받아
    people / policies / policy_roles / policy_coverages 에 분해 저장.

    raw 예시:
    {
        "policy_number": "12345678",
        "insurance_company": "삼성생명",
        "product_name": "삼성생명 통합보험",
        "contract_date": "20200101",
        "premium": 150000,
        "insured_name": "홍길동",
        "insured_birth": "19800101",
        "contractor_name": "홍길동",   # 없으면 insured_name과 동일 처리
        "beneficiary_name": "",
        "coverages": [
            {"name": "암진단비", "amount": 30000000},
            {"name": "뇌혈관질환", "amount": 20000000},
        ]
    }

    반환: {"policy_id": ..., "insured_id": ..., "contractor_id": ...}
    """
    results: dict[str, Any] = {}

    # ── 피보험자 등록 ──────────────────────────────────────
    insured_name  = raw.get("insured_name", "").strip()
    insured_birth = raw.get("insured_birth", "")
    if insured_name:
        insured = upsert_person(
            sb, insured_name, birth_date=insured_birth,
            is_real_client=True, agent_id=agent_id,
        )
        results["insured_id"] = insured["id"]

    # ── 계약자 등록 (피보험자와 다른 경우만) ──────────────
    contractor_name = raw.get("contractor_name", "").strip()
    if contractor_name and contractor_name != insured_name:
        contractor = upsert_person(
            sb, contractor_name,
            birth_date=raw.get("contractor_birth", ""),
            is_real_client=True, agent_id=agent_id,
        )
        results["contractor_id"] = contractor["id"]
    elif insured_name:
        results["contractor_id"] = results.get("insured_id")

    # ── 수익자 등록 ────────────────────────────────────────
    beneficiary_name = raw.get("beneficiary_name", "").strip()
    if beneficiary_name and beneficiary_name not in (insured_name, contractor_name):
        bene = upsert_person(
            sb, beneficiary_name,
            birth_date=raw.get("beneficiary_birth", ""),
            agent_id=agent_id,
        )
        results["beneficiary_id"] = bene["id"]

    # ── 증권 등록 ──────────────────────────────────────────
    policy = upsert_policy(
        sb,
        insurance_company=raw.get("insurance_company", ""),
        product_name=raw.get("product_name", ""),
        agent_id=agent_id,
        policy_number=raw.get("policy_number", ""),
        product_type=raw.get("product_type", ""),
        contract_date=raw.get("contract_date", ""),
        expiry_date=raw.get("expiry_date", ""),
        premium=raw.get("premium"),
        payment_period=raw.get("payment_period", ""),
        coverage_period=raw.get("coverage_period", ""),
        raw_text=raw.get("raw_text", ""),
        source=raw.get("source", "crawl"),
    )
    results["policy_id"] = policy["id"]

    # ── 역할 연결 ──────────────────────────────────────────
    pid = policy["id"]
    if results.get("contractor_id"):
        link_policy_role(sb, pid, results["contractor_id"], "계약자", agent_id)
    if results.get("insured_id"):
        link_policy_role(sb, pid, results["insured_id"], "피보험자", agent_id)
    if results.get("beneficiary_id"):
        link_policy_role(sb, pid, results["beneficiary_id"], "수익자", agent_id)

    # 추가 피보험자 복수 처리
    for extra in raw.get("extra_insureds", []):
        ex_name  = extra.get("name", "").strip()
        ex_birth = extra.get("birth", "")
        if ex_name:
            ep = upsert_person(sb, ex_name, birth_date=ex_birth, agent_id=agent_id)
            link_policy_role(sb, pid, ep["id"], "피보험자", agent_id)

    # ── 담보 저장 ──────────────────────────────────────────
    coverages = raw.get("coverages", [])
    if coverages:
        results["coverage_count"] = bulk_upsert_coverages(sb, pid, coverages, agent_id)

    return results


# ────────────────────────────────────────────────────────────────────────────
# 8. 요약 리포트 (Streamlit 표시용)
# ────────────────────────────────────────────────────────────────────────────
def get_person_summary(sb, person_id: str) -> dict:
    """
    인물 + 전체 보험 역할 + 인맥 요약 반환
    """
    person = get_person(sb, person_id)
    if not person:
        return {}
    policies = get_person_policies(sb, person_id)
    relations = get_relationships(sb, person_id)
    return {
        "person":      person,
        "policies":    policies,
        "relations":   relations,
        "total_as_contractor": len(policies.get("계약자", [])),
        "total_as_insured":    len(policies.get("피보험자", [])),
        "total_as_beneficiary":len(policies.get("수익자", [])),
    }
