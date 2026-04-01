"""
hq_reward_engine.py — 리워드 및 소개 확보 엔진
[GP-STEP9] Goldkey AI Masters 2026

리워드 및 소개 엔진:
- 리워드 시스템 (포인트/혜택 관리)
- 소개 요청 가이드 (AI 기반 최적 타이밍)
- 네트워크 확장 자동화 (소개자 라인 연결)
- 11~12단계 (사후관리/소개) 로직
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any, List
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 데이터 레이어 — 리워드 및 소개 관리
# ══════════════════════════════════════════════════════════════════════════════

def _get_sb():
    """Supabase 클라이언트 가져오기"""
    try:
        from db_utils import _get_sb as _sb
        return _sb()
    except Exception:
        return None


def create_reward(
    person_id: str,
    agent_id: str,
    reward_type: str,
    reward_amount: int,
    reason: str = ""
) -> bool:
    """
    리워드 생성
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        reward_type: 리워드 유형 ('point', 'gift', 'discount')
        reward_amount: 리워드 금액/포인트
        reason: 리워드 사유
    
    Returns:
        bool: 성공 여부
    """
    try:
        sb = _get_sb()
        if not sb:
            return False
        
        reward_record = {
            "person_id": person_id,
            "agent_id": agent_id,
            "reward_type": reward_type,
            "reward_amount": reward_amount,
            "reason": reason,
            "status": "pending",
            "created_at": datetime.datetime.now().isoformat()
        }
        
        result = sb.table("gk_rewards").insert(reward_record).execute()
        
        return bool(result.data)
    except Exception:
        return False


def get_customer_rewards(person_id: str, agent_id: str) -> List[Dict[str, Any]]:
    """
    고객 리워드 내역 조회
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        list: 리워드 목록
    """
    try:
        sb = _get_sb()
        if not sb:
            return []
        
        result = (
            sb.table("gk_rewards")
            .select("*")
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .execute()
        )
        
        return result.data or []
    except Exception:
        return []


def create_referral(
    referrer_id: str,
    referee_id: str,
    agent_id: str,
    referral_note: str = ""
) -> bool:
    """
    소개 관계 생성 (gk_relationships 활용)
    
    Args:
        referrer_id: 소개자 UUID
        referee_id: 피소개자 UUID
        agent_id: 설계사 ID
        referral_note: 소개 메모
    
    Returns:
        bool: 성공 여부
    """
    try:
        sb = _get_sb()
        if not sb:
            return False
        
        # gk_relationships 테이블에 '소개자' 관계 추가
        relationship_record = {
            "from_person_id": referrer_id,
            "to_person_id": referee_id,
            "relation_type": "소개자",
            "agent_id": agent_id,
            "memo": referral_note,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        result = sb.table("gk_relationships").insert(relationship_record).execute()
        
        # 소개자에게 리워드 부여
        if result.data:
            create_reward(
                person_id=referrer_id,
                agent_id=agent_id,
                reward_type="point",
                reward_amount=10000,
                reason="신규 고객 소개"
            )
        
        return bool(result.data)
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# [2] AI 기반 소개 요청 타이밍 분석
# ══════════════════════════════════════════════════════════════════════════════

def analyze_referral_timing(person_id: str, agent_id: str) -> Dict[str, Any]:
    """
    AI 기반 소개 요청 최적 타이밍 분석
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        dict: 타이밍 분석 결과
    """
    try:
        sb = _get_sb()
        if not sb:
            return {"ready": False, "reason": "데이터 조회 실패"}
        
        # 고객 정보 조회
        customer = (
            sb.table("gk_people")
            .select("*")
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .maybe_single()
            .execute()
        )
        
        if not customer or not customer.data:
            return {"ready": False, "reason": "고객 정보 없음"}
        
        current_stage = customer.data.get("current_stage", 0)
        last_contact = customer.data.get("last_contact", "")
        
        # 소개 요청 가능 조건
        # 1. 10단계 (체결 완료) 이상
        # 2. 마지막 접촉 후 7일 이내
        
        if current_stage < 10:
            return {
                "ready": False,
                "reason": "계약 체결 전입니다. 체결 완료 후 소개를 요청하세요.",
                "score": 0
            }
        
        # 마지막 접촉일 확인
        if last_contact:
            try:
                last_contact_dt = datetime.datetime.fromisoformat(last_contact)
                days_since_contact = (datetime.datetime.now() - last_contact_dt).days
                
                if days_since_contact > 7:
                    return {
                        "ready": False,
                        "reason": f"마지막 접촉 후 {days_since_contact}일 경과. 먼저 사후 관리를 진행하세요.",
                        "score": 30
                    }
                
                # 최적 타이밍: 체결 후 1~3일
                if 1 <= days_since_contact <= 3:
                    return {
                        "ready": True,
                        "reason": "계약 체결 직후 만족도가 높은 시기입니다. 지금이 소개 요청 최적 타이밍입니다!",
                        "score": 100,
                        "optimal": True
                    }
                
                # 양호한 타이밍: 체결 후 4~7일
                return {
                    "ready": True,
                    "reason": "소개 요청 가능한 시기입니다.",
                    "score": 70,
                    "optimal": False
                }
            except Exception:
                pass
        
        # 기본값: 소개 요청 가능
        return {
            "ready": True,
            "reason": "소개 요청 가능한 상태입니다.",
            "score": 50,
            "optimal": False
        }
    except Exception:
        return {"ready": False, "reason": "분석 중 오류 발생"}


# ══════════════════════════════════════════════════════════════════════════════
# [3] 소개 요청 멘트 생성 (3가지 톤)
# ══════════════════════════════════════════════════════════════════════════════

def generate_referral_scripts(customer_name: str, job: str = "") -> Dict[str, Dict[str, str]]:
    """
    소개 요청 멘트 생성 (3가지 톤)
    
    Args:
        customer_name: 고객 이름
        job: 직업
    
    Returns:
        dict: 3가지 톤별 소개 요청 멘트
    """
    # 1. 감사 기반 톤 (Gratitude-Based)
    gratitude = {
        "opening": f"{customer_name}님, 이번에 저희와 함께해 주셔서 정말 감사합니다. "
                   f"덕분에 {customer_name}님의 소중한 미래를 함께 준비할 수 있게 되었습니다.",
        "request": f"혹시 {customer_name}님 주변에 보험 설계가 필요하신 분이 계시다면, "
                   f"저를 소개해 주실 수 있을까요? "
                   f"{customer_name}님처럼 소중한 분들을 더 많이 도와드리고 싶습니다.",
        "incentive": "소개해 주신 분께는 감사의 마음을 담아 특별한 혜택을 드립니다. "
                     "(예: 스타벅스 기프티콘, 포인트 적립 등)"
    }
    
    # 2. 가치 제안 톤 (Value Proposition)
    value = {
        "opening": f"{customer_name}님께서 이번에 선택하신 보험 상품이 "
                   f"얼마나 합리적이고 좋은 선택이었는지 아시죠?",
        "request": f"주변 분들도 {customer_name}님처럼 현명한 선택을 하실 수 있도록, "
                   f"저를 소개해 주시면 어떨까요? "
                   f"같은 혜택과 전문적인 상담을 제공해 드리겠습니다.",
        "incentive": "소개해 주신 분과 소개받으신 분 모두에게 특별 혜택을 드립니다."
    }
    
    # 3. 직접 요청 톤 (Direct Ask)
    direct = {
        "opening": f"{customer_name}님, 제가 도움이 되셨다면 한 가지 부탁드려도 될까요?",
        "request": f"주변에 보험 상담이 필요하신 분이 있다면 저를 소개해 주세요. "
                   f"{customer_name}님께 해드린 것처럼 최선을 다해 상담해 드리겠습니다.",
        "incentive": "소개 1건당 1만 포인트를 적립해 드립니다. (현금처럼 사용 가능)"
    }
    
    # 직업별 커스터마이징
    if job:
        if "의사" in job or "간호" in job:
            gratitude["request"] += f" 특히 {job}님 동료분들께 도움이 될 것 같습니다."
        elif "교사" in job or "교수" in job:
            value["request"] += f" {job}님 동료분들께도 좋은 정보가 될 것입니다."
        elif "사업" in job or "대표" in job:
            direct["request"] += f" {job}님 네트워크에 계신 분들께도 도움이 될 것입니다."
    
    return {
        "gratitude": gratitude,
        "value": value,
        "direct": direct
    }


# ══════════════════════════════════════════════════════════════════════════════
# [4] 네트워크 확장 자동화 (마인드맵 연동)
# ══════════════════════════════════════════════════════════════════════════════

def auto_connect_referral_network(
    referrer_id: str,
    referee_name: str,
    referee_contact: str,
    agent_id: str
) -> Optional[str]:
    """
    소개받은 신규 고객 자동 등록 및 네트워크 연결
    
    Args:
        referrer_id: 소개자 UUID
        referee_name: 피소개자 이름
        referee_contact: 피소개자 연락처
        agent_id: 설계사 ID
    
    Returns:
        str: 신규 고객 UUID 또는 None
    """
    try:
        sb = _get_sb()
        if not sb:
            return None
        
        # 1. 신규 고객 생성 (gk_people)
        new_customer = {
            "name": referee_name,
            "contact": referee_contact,
            "agent_id": agent_id,
            "is_real_client": True,
            "current_stage": 1,  # 1단계: 초기 접촉
            "created_at": datetime.datetime.now().isoformat()
        }
        
        customer_result = sb.table("gk_people").insert(new_customer).execute()
        
        if not customer_result.data:
            return None
        
        referee_id = customer_result.data[0].get("person_id")
        
        # 2. 소개 관계 생성 (gk_relationships)
        create_referral(referrer_id, referee_id, agent_id, f"{referee_name}님 소개")
        
        # 3. gk_people 업데이트 (소개자 정보 추가)
        sb.table("gk_people").update({
            "memo": f"소개자: {referrer_id}"
        }).eq("person_id", referee_id).execute()
        
        return referee_id
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# [5] 리워드 통계 및 순위
# ══════════════════════════════════════════════════════════════════════════════

def get_reward_statistics(agent_id: str) -> Dict[str, Any]:
    """
    설계사의 리워드 통계 조회
    
    Args:
        agent_id: 설계사 ID
    
    Returns:
        dict: 리워드 통계
    """
    try:
        sb = _get_sb()
        if not sb:
            return {}
        
        # 전체 리워드 조회
        rewards = (
            sb.table("gk_rewards")
            .select("*")
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .execute()
        )
        
        total_points = 0
        total_gifts = 0
        total_referrals = 0
        
        for reward in (rewards.data or []):
            reward_type = reward.get("reward_type", "")
            reward_amount = reward.get("reward_amount", 0)
            
            if reward_type == "point":
                total_points += reward_amount
            elif reward_type == "gift":
                total_gifts += 1
            
            if "소개" in reward.get("reason", ""):
                total_referrals += 1
        
        return {
            "total_points": total_points,
            "total_gifts": total_gifts,
            "total_referrals": total_referrals
        }
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# [6] 에이전틱 단계 업데이트 (10단계 → 11/12단계)
# ══════════════════════════════════════════════════════════════════════════════

def update_customer_stage_to_referral(person_id: str, agent_id: str, target_stage: int = 12) -> bool:
    """
    고객 세일즈 단계 업데이트 (소개 완료)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        target_stage: 목표 단계 (11: 사후관리, 12: 소개 완료)
    
    Returns:
        bool: 성공 여부
    """
    try:
        sb = _get_sb()
        if not sb:
            return False
        
        result = (
            sb.table("gk_people")
            .update({"current_stage": target_stage})
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .execute()
        )
        
        return bool(result.data)
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# [7] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시

### 1. 소개 요청 타이밍 분석

```python
from hq_reward_engine import analyze_referral_timing

timing = analyze_referral_timing(person_id, agent_id)

if timing.get("ready"):
    print(f"소개 요청 가능: {timing.get('reason')}")
    print(f"최적 타이밍: {timing.get('optimal', False)}")
else:
    print(f"소개 요청 불가: {timing.get('reason')}")
```

### 2. 소개 요청 멘트 생성

```python
from hq_reward_engine import generate_referral_scripts

scripts = generate_referral_scripts(customer_name="홍길동", job="의사")

# 감사 기반 톤
print(scripts["gratitude"]["opening"])
print(scripts["gratitude"]["request"])
print(scripts["gratitude"]["incentive"])
```

### 3. 신규 고객 자동 등록

```python
from hq_reward_engine import auto_connect_referral_network

referee_id = auto_connect_referral_network(
    referrer_id="uuid-referrer",
    referee_name="김철수",
    referee_contact="010-1234-5678",
    agent_id="agent123"
)

if referee_id:
    print(f"신규 고객 등록 완료: {referee_id}")
    # Step 5 마인드맵에 '소개자' 라인 자동 표시
```

### 4. 리워드 부여

```python
from hq_reward_engine import create_reward

create_reward(
    person_id="uuid-customer",
    agent_id="agent123",
    reward_type="point",
    reward_amount=10000,
    reason="신규 고객 소개"
)
```

## 데이터 흐름

```
사용자: [🎁 소개 요청하기] 버튼 클릭
  ↓
analyze_referral_timing(person_id, agent_id)
  ↓
if ready:
  generate_referral_scripts(customer_name, job)
  ↓
  설계사에게 3가지 톤 멘트 제공
  ↓
  고객이 신규 고객 정보 제공
  ↓
  auto_connect_referral_network(referrer_id, referee_name, referee_contact, agent_id)
  ↓
  1. gk_people에 신규 고객 생성
  2. gk_relationships에 '소개자' 관계 추가
  3. gk_rewards에 리워드 부여
  ↓
  update_customer_stage_to_referral(person_id, agent_id, 12)
  ↓
  Step 5 마인드맵에 '소개자' 라인 자동 표시
```
"""
