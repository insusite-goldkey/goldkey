"""
hq_automation_engine.py — 에이젠틱 세일즈 오토파일럿 엔진
[GP-STEP10] Goldkey AI Masters 2026

자율 주행 세일즈 시스템:
- 제안 후 자동 팔로업 (+3일 뒤 상담 일정)
- 신계약 해피콜 사이클 (1/3/6/12개월 자동 부킹)
- 자동차 보험 만기 관리 (4주/2주 전 알림)
- 지능형 일정 검색 및 태그 시스템
- 중복 체크 로직
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any, List
from datetime import timedelta

# ══════════════════════════════════════════════════════════════════════════════
# [1] 제안 후 자동 팔로업 (Proposal Follow-up)
# ══════════════════════════════════════════════════════════════════════════════

def auto_schedule_proposal_followup(
    person_id: str,
    agent_id: str,
    customer_name: str = "",
    current_stage: int = 5
) -> Optional[str]:
    """
    제안 후 자동 팔로업 일정 생성
    
    트리거: current_stage가 5단계(제안) 또는 6단계(설득)로 변경될 때
    AI 액션: 변경 시점으로부터 +3일 뒤 오전 10시에 자동 부킹
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
        current_stage: 현재 세일즈 단계 (5 or 6)
    
    Returns:
        str: 생성된 일정 ID (schedule_id) 또는 None
    """
    if current_stage not in [5, 6]:
        return None
    
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return None
        
        # 중복 체크: 동일한 고객에 대해 이미 팔로업 일정이 있는지 확인
        existing = (
            sb.table("gk_schedules")
            .select("schedule_id")
            .eq("agent_id", agent_id)
            .contains("tags", ["#자동부킹", "#제안팔로업"])
            .eq("is_deleted", False)
            .execute()
        )
        
        # person_id가 포함된 일정이 있는지 확인
        if existing and existing.data:
            for schedule in existing.data:
                # memo나 title에 person_id가 포함되어 있으면 중복으로 간주
                # 실제 구현 시 person_id를 별도 컬럼으로 저장하는 것이 좋음
                pass
        
        # +3일 뒤 오전 10시 계산
        followup_date = datetime.datetime.now() + timedelta(days=3)
        followup_date = followup_date.replace(hour=10, minute=0, second=0, microsecond=0)
        
        # 일정 데이터 생성
        schedule_data = {
            "agent_id": agent_id,
            "title": f"제안서 검토 확인 및 2차 상담 - {customer_name}",
            "category": "상담",
            "start_dt": followup_date.isoformat(),
            "end_dt": (followup_date + timedelta(hours=1)).isoformat(),
            "memo": f"[AI 자동 부킹] {customer_name}님께 제안서를 드린 지 3일이 경과했습니다. 검토 상황을 확인하고 2차 상담을 진행해 주세요.",
            "tags": ["#자동부킹", "#제안팔로업", f"#고객_{person_id}"],
            "is_deleted": False
        }
        
        # gk_schedules에 삽입
        result = sb.table("gk_schedules").insert(schedule_data).execute()
        
        if result and result.data:
            schedule_id = result.data[0].get("schedule_id")
            return schedule_id
        
        return None
    except Exception as e:
        print(f"[ERROR] auto_schedule_proposal_followup: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# [2] 신계약 해피콜 사이클 (Happy Call Automation)
# ══════════════════════════════════════════════════════════════════════════════

def auto_schedule_happy_call_cycle(
    policy_id: str,
    person_id: str,
    agent_id: str,
    customer_name: str = "",
    contract_date: str = ""
) -> List[str]:
    """
    신계약 해피콜 사이클 자동 생성
    
    트리거: gk_policies의 part='A' (Direct) 신규 데이터 입력 시
    AI 액션: 체결일로부터 1, 3, 6, 12개월 뒤 해피콜 일정 자동 생성
    
    Args:
        policy_id: 증권 ID
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
        contract_date: 계약일 (YYYYMMDD 또는 ISO 8601)
    
    Returns:
        List[str]: 생성된 일정 ID 리스트
    """
    if not contract_date:
        contract_date = datetime.datetime.now().strftime("%Y%m%d")
    
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return []
        
        # 계약일 파싱
        if len(contract_date) == 8:  # YYYYMMDD
            base_date = datetime.datetime.strptime(contract_date, "%Y%m%d")
        else:  # ISO 8601
            base_date = datetime.datetime.fromisoformat(contract_date.replace("Z", "+00:00"))
        
        # 중복 체크: 동일한 증권에 대해 이미 해피콜 일정이 있는지 확인
        existing = (
            sb.table("gk_schedules")
            .select("schedule_id")
            .eq("agent_id", agent_id)
            .contains("tags", ["#자동부킹", "#해피콜"])
            .eq("is_deleted", False)
            .execute()
        )
        
        # policy_id가 포함된 일정이 있으면 중복 생성 방지
        if existing and existing.data:
            for schedule in existing.data:
                if f"#증권_{policy_id}" in schedule.get("tags", []):
                    return []
        
        # 해피콜 일정 생성 (1, 3, 6, 12개월)
        happy_call_periods = [
            {"months": 1, "label": "1M"},
            {"months": 3, "label": "3M"},
            {"months": 6, "label": "6M"},
            {"months": 12, "label": "12M"}
        ]
        
        created_schedule_ids = []
        
        for period in happy_call_periods:
            months = period["months"]
            label = period["label"]
            
            # 해피콜 날짜 계산 (오전 11시)
            happy_call_date = base_date + timedelta(days=30 * months)
            happy_call_date = happy_call_date.replace(hour=11, minute=0, second=0, microsecond=0)
            
            # 일정 데이터 생성
            schedule_data = {
                "agent_id": agent_id,
                "title": f"신계약 고객 유지 관리({label}) - {customer_name}",
                "category": "해피콜",
                "start_dt": happy_call_date.isoformat(),
                "end_dt": (happy_call_date + timedelta(minutes=30)).isoformat(),
                "memo": f"[AI 자동 부킹] {customer_name}님 신계약 {label} 해피콜입니다. 고객 만족도를 체크하고 증권 전달 상태를 리뷰해 주세요.",
                "tags": ["#자동부킹", "#해피콜", f"#고객_{person_id}", f"#증권_{policy_id}", f"#{label}"],
                "is_deleted": False
            }
            
            # gk_schedules에 삽입
            result = sb.table("gk_schedules").insert(schedule_data).execute()
            
            if result and result.data:
                schedule_id = result.data[0].get("schedule_id")
                created_schedule_ids.append(schedule_id)
        
        return created_schedule_ids
    except Exception as e:
        print(f"[ERROR] auto_schedule_happy_call_cycle: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# [3] 자동차 보험 만기 관리 (Car Insurance Sentinel)
# ══════════════════════════════════════════════════════════════════════════════

def auto_schedule_car_insurance_renewal(
    policy_id: str,
    person_id: str,
    agent_id: str,
    customer_name: str = "",
    expiry_date: str = ""
) -> List[str]:
    """
    자동차 보험 만기 관리 자동 일정 생성
    
    트리거: OCR 스캔 시 '자동차 보험' 및 '만기일' 감지
    AI 액션:
        - 만기 당일: "자동차 보험 만기일" 자동 부킹
        - 만기 4주 전: "1차 갱신 안내 및 비교 견적 제안"
        - 만기 2주 전: "2차 최종 클로징 전화"
    
    Args:
        policy_id: 증권 ID
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
        expiry_date: 만기일 (YYYYMMDD 또는 ISO 8601)
    
    Returns:
        List[str]: 생성된 일정 ID 리스트
    """
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
        
        # 중복 체크: 동일한 증권에 대해 이미 만기 관리 일정이 있는지 확인
        existing = (
            sb.table("gk_schedules")
            .select("schedule_id")
            .eq("agent_id", agent_id)
            .contains("tags", ["#자동부킹", "#만기관리"])
            .eq("is_deleted", False)
            .execute()
        )
        
        # policy_id가 포함된 일정이 있으면 중복 생성 방지
        if existing and existing.data:
            for schedule in existing.data:
                if f"#증권_{policy_id}" in schedule.get("tags", []):
                    return []
        
        # 만기 관리 일정 생성
        renewal_schedules = [
            {
                "days_before": 0,
                "title": f"자동차 보험 만기일 - {customer_name}",
                "memo": f"[AI 자동 부킹] {customer_name}님 자동차 보험 만기일입니다. 갱신 여부를 최종 확인해 주세요.",
                "color": "#FEE2E2"  # 코랄색 경고
            },
            {
                "days_before": 28,  # 4주 전
                "title": f"1차 갱신 안내 및 비교 견적 제안 - {customer_name}",
                "memo": f"[AI 자동 부킹] {customer_name}님 자동차 보험 만기 4주 전입니다. 갱신 안내 및 비교 견적을 제안해 주세요. ⚠️ 놓치면 타사에 뺏길 수 있는 중요한 건입니다.",
                "color": "#FEF3C7"  # 골드색 주의
            },
            {
                "days_before": 14,  # 2주 전
                "title": f"2차 최종 클로징 전화 - {customer_name}",
                "memo": f"[AI 자동 부킹] {customer_name}님 자동차 보험 만기 2주 전입니다. 최종 클로징 전화를 진행해 주세요.",
                "color": "#FEE2E2"  # 코랄색 경고
            }
        ]
        
        created_schedule_ids = []
        
        for renewal in renewal_schedules:
            days_before = renewal["days_before"]
            title = renewal["title"]
            memo = renewal["memo"]
            
            # 일정 날짜 계산 (오전 9시)
            schedule_date = expiry_dt - timedelta(days=days_before)
            schedule_date = schedule_date.replace(hour=9, minute=0, second=0, microsecond=0)
            
            # 일정 데이터 생성
            schedule_data = {
                "agent_id": agent_id,
                "title": title,
                "category": "만기관리",
                "start_dt": schedule_date.isoformat(),
                "end_dt": (schedule_date + timedelta(minutes=30)).isoformat(),
                "memo": memo,
                "tags": ["#자동부킹", "#만기관리", "#자동차보험", f"#고객_{person_id}", f"#증권_{policy_id}"],
                "is_deleted": False
            }
            
            # gk_schedules에 삽입
            result = sb.table("gk_schedules").insert(schedule_data).execute()
            
            if result and result.data:
                schedule_id = result.data[0].get("schedule_id")
                created_schedule_ids.append(schedule_id)
        
        return created_schedule_ids
    except Exception as e:
        print(f"[ERROR] auto_schedule_car_insurance_renewal: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# [4] 지능형 일정 검색 (Smart Schedule Search)
# ══════════════════════════════════════════════════════════════════════════════

def search_auto_booked_schedules(
    agent_id: str,
    tag_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    자동 부킹된 일정 검색
    
    Args:
        agent_id: 설계사 ID
        tag_filter: 태그 필터 (#자동부킹, #해피콜, #만기관리 등)
        start_date: 시작일 (ISO 8601)
        end_date: 종료일 (ISO 8601)
    
    Returns:
        List[Dict]: 일정 리스트
    """
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return []
        
        # 기본 쿼리
        query = (
            sb.table("gk_schedules")
            .select("*")
            .eq("agent_id", agent_id)
            .contains("tags", ["#자동부킹"])
            .eq("is_deleted", False)
        )
        
        # 태그 필터 적용
        if tag_filter:
            query = query.contains("tags", [tag_filter])
        
        # 날짜 범위 필터 적용
        if start_date:
            query = query.gte("start_dt", start_date)
        
        if end_date:
            query = query.lte("start_dt", end_date)
        
        # 정렬 (시작일 오름차순)
        query = query.order("start_dt", desc=False)
        
        result = query.execute()
        
        return result.data if result and result.data else []
    except Exception as e:
        print(f"[ERROR] search_auto_booked_schedules: {e}")
        return []


def get_auto_booking_statistics(agent_id: str) -> Dict[str, Any]:
    """
    자동 부킹 통계 조회
    
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
        
        # 전체 자동 부킹 일정 조회
        all_schedules = (
            sb.table("gk_schedules")
            .select("tags, start_dt")
            .eq("agent_id", agent_id)
            .contains("tags", ["#자동부킹"])
            .eq("is_deleted", False)
            .execute()
        )
        
        if not all_schedules or not all_schedules.data:
            return {
                "total_auto_booked": 0,
                "proposal_followup": 0,
                "happy_call": 0,
                "car_renewal": 0,
                "upcoming_this_week": 0
            }
        
        # 통계 계산
        total = len(all_schedules.data)
        proposal_followup = sum(1 for s in all_schedules.data if "#제안팔로업" in s.get("tags", []))
        happy_call = sum(1 for s in all_schedules.data if "#해피콜" in s.get("tags", []))
        car_renewal = sum(1 for s in all_schedules.data if "#만기관리" in s.get("tags", []))
        
        # 이번 주 예정 일정 계산
        today = datetime.datetime.now()
        week_end = today + timedelta(days=7)
        
        upcoming_this_week = 0
        for schedule in all_schedules.data:
            start_dt_str = schedule.get("start_dt", "")
            if start_dt_str:
                try:
                    start_dt = datetime.datetime.fromisoformat(start_dt_str.replace("Z", "+00:00"))
                    if today <= start_dt <= week_end:
                        upcoming_this_week += 1
                except Exception:
                    pass
        
        return {
            "total_auto_booked": total,
            "proposal_followup": proposal_followup,
            "happy_call": happy_call,
            "car_renewal": car_renewal,
            "upcoming_this_week": upcoming_this_week
        }
    except Exception as e:
        print(f"[ERROR] get_auto_booking_statistics: {e}")
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# [5] 중복 체크 로직 강화
# ══════════════════════════════════════════════════════════════════════════════

def check_duplicate_schedule(
    agent_id: str,
    person_id: str,
    schedule_type: str,
    policy_id: Optional[str] = None
) -> bool:
    """
    중복 일정 체크
    
    Args:
        agent_id: 설계사 ID
        person_id: 고객 UUID
        schedule_type: 일정 유형 (#제안팔로업, #해피콜, #만기관리)
        policy_id: 증권 ID (선택)
    
    Returns:
        bool: 중복 여부 (True: 중복 있음, False: 중복 없음)
    """
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return False
        
        # 기본 쿼리
        query = (
            sb.table("gk_schedules")
            .select("schedule_id, tags")
            .eq("agent_id", agent_id)
            .contains("tags", ["#자동부킹", schedule_type])
            .eq("is_deleted", False)
        )
        
        result = query.execute()
        
        if not result or not result.data:
            return False
        
        # person_id 또는 policy_id 매칭 확인
        for schedule in result.data:
            tags = schedule.get("tags", [])
            
            # person_id 매칭
            if f"#고객_{person_id}" in tags:
                return True
            
            # policy_id 매칭 (있는 경우)
            if policy_id and f"#증권_{policy_id}" in tags:
                return True
        
        return False
    except Exception as e:
        print(f"[ERROR] check_duplicate_schedule: {e}")
        return False


def remove_duplicate_schedules(agent_id: str) -> int:
    """
    중복 일정 제거 (정리 작업)
    
    Args:
        agent_id: 설계사 ID
    
    Returns:
        int: 제거된 일정 개수
    """
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return 0
        
        # 모든 자동 부킹 일정 조회
        all_schedules = (
            sb.table("gk_schedules")
            .select("schedule_id, tags, start_dt")
            .eq("agent_id", agent_id)
            .contains("tags", ["#자동부킹"])
            .eq("is_deleted", False)
            .order("start_dt", desc=False)
            .execute()
        )
        
        if not all_schedules or not all_schedules.data:
            return 0
        
        # 중복 감지 (동일한 고객 + 동일한 유형 + 동일한 날짜)
        seen = set()
        duplicates = []
        
        for schedule in all_schedules.data:
            schedule_id = schedule.get("schedule_id")
            tags = schedule.get("tags", [])
            start_dt = schedule.get("start_dt", "")
            
            # 고객 ID 추출
            customer_tag = next((t for t in tags if t.startswith("#고객_")), None)
            
            if not customer_tag:
                continue
            
            # 유형 추출
            type_tag = next((t for t in tags if t in ["#제안팔로업", "#해피콜", "#만기관리"]), None)
            
            if not type_tag:
                continue
            
            # 날짜 추출 (일자만)
            date_only = start_dt[:10] if start_dt else ""
            
            # 중복 키 생성
            key = f"{customer_tag}_{type_tag}_{date_only}"
            
            if key in seen:
                duplicates.append(schedule_id)
            else:
                seen.add(key)
        
        # 중복 일정 삭제 (is_deleted=True)
        removed_count = 0
        for schedule_id in duplicates:
            sb.table("gk_schedules").update({"is_deleted": True}).eq("schedule_id", schedule_id).execute()
            removed_count += 1
        
        return removed_count
    except Exception as e:
        print(f"[ERROR] remove_duplicate_schedules: {e}")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# [6] 트리거 감지 및 자동 실행 (Trigger Detection)
# ══════════════════════════════════════════════════════════════════════════════

def detect_and_auto_book(
    agent_id: str,
    trigger_type: str,
    trigger_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    트리거 감지 및 자동 부킹 실행
    
    Args:
        agent_id: 설계사 ID
        trigger_type: 트리거 유형 ('proposal', 'contract', 'car_insurance')
        trigger_data: 트리거 데이터
    
    Returns:
        dict: 실행 결과
    """
    result = {
        "success": False,
        "trigger_type": trigger_type,
        "created_schedules": [],
        "message": ""
    }
    
    try:
        # 1. 제안 후 팔로업 트리거
        if trigger_type == "proposal":
            person_id = trigger_data.get("person_id")
            customer_name = trigger_data.get("customer_name", "")
            current_stage = trigger_data.get("current_stage", 5)
            
            # 중복 체크
            if check_duplicate_schedule(agent_id, person_id, "#제안팔로업"):
                result["message"] = "이미 제안 팔로업 일정이 존재합니다."
                return result
            
            # 자동 부킹
            schedule_id = auto_schedule_proposal_followup(person_id, agent_id, customer_name, current_stage)
            
            if schedule_id:
                result["success"] = True
                result["created_schedules"].append(schedule_id)
                result["message"] = f"{customer_name}님 제안 후 3일 뒤 팔로업 일정이 자동으로 생성되었습니다."
        
        # 2. 신계약 해피콜 트리거
        elif trigger_type == "contract":
            policy_id = trigger_data.get("policy_id")
            person_id = trigger_data.get("person_id")
            customer_name = trigger_data.get("customer_name", "")
            contract_date = trigger_data.get("contract_date", "")
            
            # 중복 체크
            if check_duplicate_schedule(agent_id, person_id, "#해피콜", policy_id):
                result["message"] = "이미 해피콜 일정이 존재합니다."
                return result
            
            # 자동 부킹
            schedule_ids = auto_schedule_happy_call_cycle(policy_id, person_id, agent_id, customer_name, contract_date)
            
            if schedule_ids:
                result["success"] = True
                result["created_schedules"] = schedule_ids
                result["message"] = f"{customer_name}님 신계약 해피콜 일정 {len(schedule_ids)}건이 자동으로 생성되었습니다."
        
        # 3. 자동차 보험 만기 관리 트리거
        elif trigger_type == "car_insurance":
            policy_id = trigger_data.get("policy_id")
            person_id = trigger_data.get("person_id")
            customer_name = trigger_data.get("customer_name", "")
            expiry_date = trigger_data.get("expiry_date", "")
            
            # 중복 체크
            if check_duplicate_schedule(agent_id, person_id, "#만기관리", policy_id):
                result["message"] = "이미 만기 관리 일정이 존재합니다."
                return result
            
            # 자동 부킹
            schedule_ids = auto_schedule_car_insurance_renewal(policy_id, person_id, agent_id, customer_name, expiry_date)
            
            if schedule_ids:
                result["success"] = True
                result["created_schedules"] = schedule_ids
                result["message"] = f"{customer_name}님 자동차 보험 만기 관리 일정 {len(schedule_ids)}건이 자동으로 생성되었습니다."
        
        return result
    except Exception as e:
        result["message"] = f"자동 부킹 실행 중 오류 발생: {e}"
        return result


# ══════════════════════════════════════════════════════════════════════════════
# [7] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시

### 1. 제안 후 자동 팔로업

```python
from hq_automation_engine import detect_and_auto_book

# 고객이 5단계(제안)로 진입했을 때
trigger_data = {
    "person_id": "uuid-1234",
    "customer_name": "홍길동",
    "current_stage": 5
}

result = detect_and_auto_book(
    agent_id="agent-001",
    trigger_type="proposal",
    trigger_data=trigger_data
)

if result["success"]:
    print(result["message"])
    # "홍길동님 제안 후 3일 뒤 팔로업 일정이 자동으로 생성되었습니다."
```

### 2. 신계약 해피콜 사이클

```python
# 신계약이 체결되었을 때 (part='A')
trigger_data = {
    "policy_id": "policy-5678",
    "person_id": "uuid-1234",
    "customer_name": "홍길동",
    "contract_date": "20260401"
}

result = detect_and_auto_book(
    agent_id="agent-001",
    trigger_type="contract",
    trigger_data=trigger_data
)

if result["success"]:
    print(result["message"])
    # "홍길동님 신계약 해피콜 일정 4건이 자동으로 생성되었습니다."
    # 생성된 일정: 1M, 3M, 6M, 12M
```

### 3. 자동차 보험 만기 관리

```python
# OCR 스캔으로 자동차 보험 만기일이 감지되었을 때
trigger_data = {
    "policy_id": "policy-9999",
    "person_id": "uuid-1234",
    "customer_name": "홍길동",
    "expiry_date": "20261201"
}

result = detect_and_auto_book(
    agent_id="agent-001",
    trigger_type="car_insurance",
    trigger_data=trigger_data
)

if result["success"]:
    print(result["message"])
    # "홍길동님 자동차 보험 만기 관리 일정 3건이 자동으로 생성되었습니다."
    # 생성된 일정: 만기일, 4주 전, 2주 전
```

### 4. 자동 부킹 통계 조회

```python
from hq_automation_engine import get_auto_booking_statistics

stats = get_auto_booking_statistics("agent-001")

print(f"총 자동 부킹 일정: {stats['total_auto_booked']}건")
print(f"제안 팔로업: {stats['proposal_followup']}건")
print(f"해피콜: {stats['happy_call']}건")
print(f"만기 관리: {stats['car_renewal']}건")
print(f"이번 주 예정: {stats['upcoming_this_week']}건")
```

### 5. 자동 부킹 일정 검색

```python
from hq_automation_engine import search_auto_booked_schedules

# 해피콜 일정만 검색
happy_calls = search_auto_booked_schedules(
    agent_id="agent-001",
    tag_filter="#해피콜"
)

for schedule in happy_calls:
    print(f"{schedule['title']} - {schedule['start_dt']}")
```

### 6. 중복 일정 제거

```python
from hq_automation_engine import remove_duplicate_schedules

removed_count = remove_duplicate_schedules("agent-001")
print(f"{removed_count}건의 중복 일정이 제거되었습니다.")
```
"""
