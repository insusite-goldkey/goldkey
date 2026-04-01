"""
hq_policy_manager.py — 에이젠틱 계약 생애주기 관리자
[GP-STEP11] Goldkey AI Masters 2026

지능형 계약 생애주기 관리:
- 상태 감시 및 자동 스케줄 생성
- 오토-클린 (해지/실효 시 미래 일정 자동 삭제)
- 자동차 보험 자동 갱신
- 만기 알림 자동 부킹
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any, List
from datetime import timedelta

# ══════════════════════════════════════════════════════════════════════════════
# [1] 계약 상태 감시 및 만기 알림 스케줄 생성
# ══════════════════════════════════════════════════════════════════════════════

def auto_schedule_expiry_reminder(
    policy_id: str,
    person_id: str,
    agent_id: str,
    customer_name: str = "",
    expiry_date: str = "",
    policy_category: str = "장기",
    status: str = "정상"
) -> List[str]:
    """
    만기 알림 스케줄 자동 생성
    
    트리거: status = '정상'인 계약 생성 시
    
    자동 액션:
        - 장기/연간소멸식/특종: 만기 1개월 전 알림
        - 자동차: 만기 4주 전, 2주 전 알림 (총 2건)
    
    Args:
        policy_id: 증권 ID
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
        expiry_date: 만기일 (YYYYMMDD 또는 ISO 8601)
        policy_category: 보험 유형 (장기, 자동차, 연간소멸식, 특종)
        status: 계약 상태 (정상만 스케줄 생성)
    
    Returns:
        List[str]: 생성된 일정 ID 리스트
    """
    # 상태가 '정상'이 아니면 스케줄 생성 안 함
    if status != "정상":
        return []
    
    if not expiry_date:
        return []
    
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return []
        
        # 만기일 파싱
        if len(expiry_date) == 8:  # YYYYMMDD
            expiry_dt = datetime.datetime.strptime(expiry_date, "%Y%m%d")
        else:  # ISO 8601
            expiry_dt = datetime.datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
        
        # 중복 체크: 동일한 증권에 대해 이미 만기 알림 일정이 있는지 확인
        existing = (
            sb.table("gk_schedules")
            .select("schedule_id")
            .eq("agent_id", agent_id)
            .contains("tags", ["#자동부킹", "#만기알림"])
            .eq("is_deleted", False)
            .execute()
        )
        
        # policy_id가 포함된 일정이 있으면 중복 생성 방지
        if existing and existing.data:
            for schedule in existing.data:
                if f"#증권_{policy_id}" in schedule.get("tags", []):
                    return []
        
        created_schedule_ids = []
        
        # 자동차 보험: 4주 전, 2주 전 (총 2건)
        if policy_category == "자동차":
            reminders = [
                {
                    "days_before": 28,  # 4주 전
                    "title": f"자동차 보험 만기 4주 전 안내 - {customer_name}",
                    "memo": f"[AI 자동 부킹] {customer_name}님 자동차 보험 만기 4주 전입니다. 갱신 안내 및 비교 견적을 제안해 주세요.",
                    "color": "#FEF3C7"  # 골드색
                },
                {
                    "days_before": 14,  # 2주 전
                    "title": f"자동차 보험 만기 2주 전 최종 안내 - {customer_name}",
                    "memo": f"[AI 자동 부킹] {customer_name}님 자동차 보험 만기 2주 전입니다. 최종 갱신 확인을 진행해 주세요.",
                    "color": "#FEE2E2"  # 코랄색
                }
            ]
        else:
            # 장기/연간소멸식/특종: 1개월 전 (1건)
            reminders = [
                {
                    "days_before": 30,  # 1개월 전
                    "title": f"{policy_category} 보험 만기 1개월 전 안내 - {customer_name}",
                    "memo": f"[AI 자동 부킹] {customer_name}님 {policy_category} 보험 만기 1개월 전입니다. 갱신 또는 재가입 안내를 진행해 주세요.",
                    "color": "#DBEAFE"  # 소프트 블루
                }
            ]
        
        for reminder in reminders:
            days_before = reminder["days_before"]
            title = reminder["title"]
            memo = reminder["memo"]
            
            # 일정 날짜 계산 (오전 10시)
            schedule_date = expiry_dt - timedelta(days=days_before)
            schedule_date = schedule_date.replace(hour=10, minute=0, second=0, microsecond=0)
            
            # 일정 데이터 생성
            schedule_data = {
                "agent_id": agent_id,
                "title": title,
                "category": "만기알림",
                "start_dt": schedule_date.isoformat(),
                "end_dt": (schedule_date + timedelta(hours=1)).isoformat(),
                "memo": memo,
                "tags": ["#자동부킹", "#만기알림", f"#고객_{person_id}", f"#증권_{policy_id}", f"#{policy_category}"],
                "is_deleted": False
            }
            
            # gk_schedules에 삽입
            result = sb.table("gk_schedules").insert(schedule_data).execute()
            
            if result and result.data:
                schedule_id = result.data[0].get("schedule_id")
                created_schedule_ids.append(schedule_id)
        
        return created_schedule_ids
    except Exception as e:
        print(f"[ERROR] auto_schedule_expiry_reminder: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# [2] 오토-클린 (Auto-Clean): 해지/실효 시 미래 일정 자동 삭제
# ══════════════════════════════════════════════════════════════════════════════

def auto_clean_future_schedules(
    policy_id: str,
    agent_id: str,
    new_status: str
) -> int:
    """
    계약 상태 변경 시 미래 일정 자동 삭제
    
    트리거: status가 '해지', '실효', '철회'로 변경될 때
    
    자동 액션:
        - 해당 증권(policy_id)과 연결된 미래의 모든 자동 스케줄 삭제
        - 설계사의 캘린더가 지저분해지는 것을 방지
    
    Args:
        policy_id: 증권 ID
        agent_id: 설계사 ID
        new_status: 변경 후 상태
    
    Returns:
        int: 삭제된 일정 개수
    """
    # 해지/실효/철회가 아니면 삭제 안 함
    if new_status not in ["해지", "실효", "철회"]:
        return 0
    
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return 0
        
        # 현재 시각
        now = datetime.datetime.now().isoformat()
        
        # 해당 증권과 연결된 미래의 자동 부킹 일정 조회
        future_schedules = (
            sb.table("gk_schedules")
            .select("schedule_id, tags, start_dt")
            .eq("agent_id", agent_id)
            .contains("tags", ["#자동부킹"])
            .gte("start_dt", now)  # 미래 일정만
            .eq("is_deleted", False)
            .execute()
        )
        
        if not future_schedules or not future_schedules.data:
            return 0
        
        # policy_id가 포함된 일정만 필터링
        target_schedule_ids = []
        for schedule in future_schedules.data:
            tags = schedule.get("tags", [])
            if f"#증권_{policy_id}" in tags:
                target_schedule_ids.append(schedule.get("schedule_id"))
        
        if not target_schedule_ids:
            return 0
        
        # 일정 삭제 (Hard Delete)
        deleted_count = 0
        for schedule_id in target_schedule_ids:
            result = (
                sb.table("gk_schedules")
                .delete()
                .eq("schedule_id", schedule_id)
                .execute()
            )
            if result:
                deleted_count += 1
        
        return deleted_count
    except Exception as e:
        print(f"[ERROR] auto_clean_future_schedules: {e}")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# [3] 자동차 보험 자동 갱신
# ══════════════════════════════════════════════════════════════════════════════

def auto_renew_policy(
    policy_id: str,
    agent_id: str,
    renewal_date: str = ""
) -> Optional[str]:
    """
    자동차 보험 자동 갱신
    
    트리거: 만기 전 갱신 입력 시
    
    자동 액션:
        - 차년도 계약 데이터 자동 생성
        - 새로운 만기 알림 스케줄 자동 배치
    
    Args:
        policy_id: 기존 증권 ID
        agent_id: 설계사 ID
        renewal_date: 갱신일 (YYYYMMDD 또는 ISO 8601)
    
    Returns:
        str: 새로 생성된 증권 ID 또는 None
    """
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return None
        
        # 기존 증권 정보 조회
        existing_policy = (
            sb.table("gk_policies")
            .select("*")
            .eq("policy_id", policy_id)
            .eq("agent_id", agent_id)
            .maybe_single()
            .execute()
        )
        
        if not existing_policy or not existing_policy.data:
            return None
        
        old_policy = existing_policy.data
        
        # 자동차 보험만 자동 갱신
        if old_policy.get("policy_category") != "자동차":
            return None
        
        # 갱신일 파싱
        if not renewal_date:
            renewal_date = datetime.datetime.now().strftime("%Y%m%d")
        
        if len(renewal_date) == 8:  # YYYYMMDD
            renewal_dt = datetime.datetime.strptime(renewal_date, "%Y%m%d")
        else:  # ISO 8601
            renewal_dt = datetime.datetime.fromisoformat(renewal_date.replace("Z", "+00:00"))
        
        # 차년도 만기일 계산 (갱신일 + 1년)
        new_expiry_dt = renewal_dt + timedelta(days=365)
        new_expiry_date = new_expiry_dt.strftime("%Y%m%d")
        
        # 새로운 증권 데이터 생성
        new_policy_data = {
            "agent_id": agent_id,
            "person_id": old_policy.get("person_id"),
            "company": old_policy.get("company"),
            "product_name": old_policy.get("product_name"),
            "part": old_policy.get("part", "A"),
            "contract_date": renewal_date if len(renewal_date) == 8 else renewal_dt.strftime("%Y%m%d"),
            "expiry_date": new_expiry_date,
            "status": "정상",
            "policy_category": "자동차",
            "is_deleted": False
        }
        
        # gk_policies에 삽입
        result = sb.table("gk_policies").insert(new_policy_data).execute()
        
        if not result or not result.data:
            return None
        
        new_policy_id = result.data[0].get("policy_id")
        
        # 기존 증권 상태를 '갱신'으로 변경
        sb.table("gk_policies").update({"status": "갱신"}).eq("policy_id", policy_id).execute()
        
        # 기존 증권의 미래 일정 삭제
        auto_clean_future_schedules(policy_id, agent_id, "갱신")
        
        # 새로운 증권에 대한 만기 알림 스케줄 생성
        person_id = old_policy.get("person_id")
        customer_name = ""  # 실제 구현 시 gk_people에서 조회
        
        auto_schedule_expiry_reminder(
            policy_id=new_policy_id,
            person_id=person_id,
            agent_id=agent_id,
            customer_name=customer_name,
            expiry_date=new_expiry_date,
            policy_category="자동차",
            status="정상"
        )
        
        return new_policy_id
    except Exception as e:
        print(f"[ERROR] auto_renew_policy: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# [4] 계약 상태 변경 통합 함수
# ══════════════════════════════════════════════════════════════════════════════

def update_policy_status(
    policy_id: str,
    agent_id: str,
    new_status: str,
    reason: str = "",
    changed_by: str = ""
) -> Dict[str, Any]:
    """
    계약 상태 변경 통합 함수
    
    Args:
        policy_id: 증권 ID
        agent_id: 설계사 ID
        new_status: 변경 후 상태 (정상, 실효, 해지, 철회, 갱신)
        reason: 변경 사유
        changed_by: 변경자 (agent_id 또는 시스템)
    
    Returns:
        dict: 실행 결과
    """
    result = {
        "success": False,
        "old_status": "",
        "new_status": new_status,
        "deleted_schedules": 0,
        "message": ""
    }
    
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            result["message"] = "데이터베이스 연결 실패"
            return result
        
        # 기존 상태 조회
        existing_policy = (
            sb.table("gk_policies")
            .select("status")
            .eq("policy_id", policy_id)
            .eq("agent_id", agent_id)
            .maybe_single()
            .execute()
        )
        
        if not existing_policy or not existing_policy.data:
            result["message"] = "증권을 찾을 수 없습니다."
            return result
        
        old_status = existing_policy.data.get("status", "")
        result["old_status"] = old_status
        
        # 상태 변경
        update_result = (
            sb.table("gk_policies")
            .update({"status": new_status})
            .eq("policy_id", policy_id)
            .eq("agent_id", agent_id)
            .execute()
        )
        
        if not update_result:
            result["message"] = "상태 변경 실패"
            return result
        
        # 상태 변경 이력 저장
        history_data = {
            "policy_id": policy_id,
            "agent_id": agent_id,
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason,
            "changed_by": changed_by or agent_id
        }
        
        sb.table("gk_policy_status_history").insert(history_data).execute()
        
        # 해지/실효/철회 시 미래 일정 자동 삭제
        if new_status in ["해지", "실효", "철회"]:
            deleted_count = auto_clean_future_schedules(policy_id, agent_id, new_status)
            result["deleted_schedules"] = deleted_count
            result["message"] = f"상태가 '{new_status}'로 변경되었습니다. 관련된 미래 일정 {deleted_count}건이 함께 삭제되었습니다."
        else:
            result["message"] = f"상태가 '{new_status}'로 변경되었습니다."
        
        result["success"] = True
        return result
    except Exception as e:
        result["message"] = f"오류 발생: {e}"
        return result


# ══════════════════════════════════════════════════════════════════════════════
# [5] 계약 생애주기 통계
# ══════════════════════════════════════════════════════════════════════════════

def get_policy_lifecycle_statistics(agent_id: str) -> Dict[str, Any]:
    """
    계약 생애주기 통계 조회
    
    Args:
        agent_id: 설계사 ID
    
    Returns:
        dict: 통계 정보
    """
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return {}
        
        # 전체 계약 조회
        all_policies = (
            sb.table("gk_policies")
            .select("status, policy_category")
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .execute()
        )
        
        if not all_policies or not all_policies.data:
            return {
                "total_policies": 0,
                "active_policies": 0,
                "expired_policies": 0,
                "cancelled_policies": 0,
                "renewed_policies": 0,
                "car_insurance_count": 0,
                "long_term_count": 0
            }
        
        # 통계 계산
        total = len(all_policies.data)
        active = sum(1 for p in all_policies.data if p.get("status") == "정상")
        expired = sum(1 for p in all_policies.data if p.get("status") == "실효")
        cancelled = sum(1 for p in all_policies.data if p.get("status") == "해지")
        renewed = sum(1 for p in all_policies.data if p.get("status") == "갱신")
        car_insurance = sum(1 for p in all_policies.data if p.get("policy_category") == "자동차")
        long_term = sum(1 for p in all_policies.data if p.get("policy_category") == "장기")
        
        return {
            "total_policies": total,
            "active_policies": active,
            "expired_policies": expired,
            "cancelled_policies": cancelled,
            "renewed_policies": renewed,
            "car_insurance_count": car_insurance,
            "long_term_count": long_term
        }
    except Exception as e:
        print(f"[ERROR] get_policy_lifecycle_statistics: {e}")
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# [6] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시

### 1. 만기 알림 스케줄 자동 생성

```python
from hq_policy_manager import auto_schedule_expiry_reminder

# 장기 보험 계약 생성 시
schedule_ids = auto_schedule_expiry_reminder(
    policy_id="policy-1234",
    person_id="uuid-5678",
    agent_id="agent-001",
    customer_name="홍길동",
    expiry_date="20270401",
    policy_category="장기",
    status="정상"
)

if schedule_ids:
    print(f"만기 1개월 전 알림 일정 {len(schedule_ids)}건이 자동으로 생성되었습니다.")

# 자동차 보험 계약 생성 시
schedule_ids = auto_schedule_expiry_reminder(
    policy_id="policy-9999",
    person_id="uuid-5678",
    agent_id="agent-001",
    customer_name="홍길동",
    expiry_date="20261201",
    policy_category="자동차",
    status="정상"
)

if schedule_ids:
    print(f"자동차 보험 만기 알림 일정 {len(schedule_ids)}건이 자동으로 생성되었습니다.")
    # 4주 전, 2주 전 총 2건
```

### 2. 계약 상태 변경 및 미래 일정 자동 삭제

```python
from hq_policy_manager import update_policy_status

# 계약 해지 처리
result = update_policy_status(
    policy_id="policy-1234",
    agent_id="agent-001",
    new_status="해지",
    reason="고객 요청",
    changed_by="agent-001"
)

if result["success"]:
    print(result["message"])
    # "상태가 '해지'로 변경되었습니다. 관련된 미래 일정 3건이 함께 삭제되었습니다."
```

### 3. 자동차 보험 자동 갱신

```python
from hq_policy_manager import auto_renew_policy

# 만기 전 갱신 입력
new_policy_id = auto_renew_policy(
    policy_id="policy-9999",
    agent_id="agent-001",
    renewal_date="20261201"
)

if new_policy_id:
    print(f"차년도 계약이 자동으로 생성되었습니다. (새 증권 ID: {new_policy_id})")
    print("기존 증권의 미래 일정이 삭제되고, 새 증권에 대한 만기 알림이 자동으로 생성되었습니다.")
```

### 4. 계약 생애주기 통계 조회

```python
from hq_policy_manager import get_policy_lifecycle_statistics

stats = get_policy_lifecycle_statistics("agent-001")

print(f"총 계약: {stats['total_policies']}건")
print(f"정상: {stats['active_policies']}건")
print(f"실효: {stats['expired_policies']}건")
print(f"해지: {stats['cancelled_policies']}건")
print(f"갱신: {stats['renewed_policies']}건")
print(f"자동차 보험: {stats['car_insurance_count']}건")
print(f"장기 보험: {stats['long_term_count']}건")
```

## 데이터 흐름

### 계약 생성 → 만기 알림 자동 부킹

```
[Step 7] 보험 3버킷에 신규 계약 입력
  ↓
gk_policies.insert({
    status: "정상",
    policy_category: "자동차",
    expiry_date: "20261201"
})
  ↓
auto_schedule_expiry_reminder()
  ↓
만기 4주 전 (2026-11-03 10:00) 일정 생성
만기 2주 전 (2026-11-17 10:00) 일정 생성
  ↓
gk_schedules.insert() × 2건
```

### 계약 해지 → 미래 일정 자동 삭제

```
[Step 7] 보험 3버킷에서 [해지] 버튼 클릭
  ↓
update_policy_status(new_status="해지")
  ↓
gk_policies.update({status: "해지"})
  ↓
auto_clean_future_schedules()
  ↓
해당 증권과 연결된 미래 일정 조회
  ↓
gk_schedules.delete() × N건
  ↓
"관련된 미래 일정 N건이 함께 삭제되었습니다" 메시지 표시
```

### 자동차 보험 갱신 → 차년도 계약 자동 생성

```
[Step 7] 보험 3버킷에서 [갱신] 버튼 클릭
  ↓
auto_renew_policy()
  ↓
기존 증권 정보 조회
  ↓
차년도 만기일 계산 (갱신일 + 1년)
  ↓
gk_policies.insert({
    expiry_date: "20271201",
    status: "정상"
})
  ↓
기존 증권 상태 변경 (status: "갱신")
  ↓
기존 증권 미래 일정 삭제
  ↓
새 증권에 대한 만기 알림 스케줄 생성
```
"""
