"""
[GP-HQ] 중앙 통제실 일일 브리핑 엔진 (Daily Briefing Engine)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 목적
HQ(중앙 통제실)가 실시간으로 데이터를 분석하여 사용자에게 "지금 당장 해야 할 일"을
브리핑해 주는 에이젠틱 칵핏(Agentic Cockpit) 시스템

## 핵심 기능
1. gk_people, gk_policies, gk_schedules 테이블 융합 분석
2. 오늘의 우선순위 액션 TOP 3 추출
3. 정제된 JSON 형태로 CRM에 전달

## 사용법
```python
from hq_briefing import get_daily_briefing

briefing_data = get_daily_briefing(agent_id="agent_123")
# Returns:
# {
#   "priority_actions": [
#     {"type": "stuck_customer", "customer_name": "홍길동", "days_stuck": 3, ...},
#     {"type": "birthday", "customer_name": "김철수", "birth_date": "1990-04-01", ...},
#     {"type": "expiring_policy", "policy_number": "ABC123", "days_until_expiry": 30, ...}
#   ],
#   "stats": {...},
#   "generated_at": "2026-04-01T18:38:00"
# }
```
"""

import datetime
from typing import Dict, Any, List, Optional
import streamlit as st


# ══════════════════════════════════════════════════════════════════════════════
# §1 브리핑 우선순위 기준
# ══════════════════════════════════════════════════════════════════════════════

# 고객 상태 정체 기준 (일 단위)
STUCK_THRESHOLD_DAYS = 3

# 생일 알림 범위 (오늘 ± N일)
BIRTHDAY_ALERT_RANGE_DAYS = 7

# 만기 임박 알림 (일 단위)
EXPIRY_ALERT_DAYS = 30

# 최대 브리핑 항목 수
MAX_BRIEFING_ITEMS = 3


# ══════════════════════════════════════════════════════════════════════════════
# §2 데이터 융합 분석
# ══════════════════════════════════════════════════════════════════════════════

def get_daily_briefing(agent_id: str) -> Dict[str, Any]:
    """
    HQ 중앙 통제실 일일 브리핑 생성
    
    Args:
        agent_id: 설계사 ID
    
    Returns:
        Dict: 브리핑 데이터
            - priority_actions: 우선순위 액션 리스트 (TOP 3)
            - stats: 통계 요약
            - generated_at: 생성 시각
    """
    try:
        from db_utils import get_supabase_client
        
        supabase = get_supabase_client()
        today = datetime.date.today()
        
        priority_actions = []
        
        # ── [1] 정체된 고객 찾기 (4단계에서 3일째 멈춰있는 고객) ──────────────
        stuck_customers = _find_stuck_customers(supabase, agent_id, today)
        priority_actions.extend(stuck_customers)
        
        # ── [2] 생일 고객 찾기 (오늘 ± 7일) ─────────────────────────────────
        birthday_customers = _find_birthday_customers(supabase, agent_id, today)
        priority_actions.extend(birthday_customers)
        
        # ── [3] 만기 임박 계약 찾기 (30일 이내) ──────────────────────────────
        expiring_policies = _find_expiring_policies(supabase, agent_id, today)
        priority_actions.extend(expiring_policies)
        
        # ── [4] 우선순위 정렬 및 TOP 3 추출 ──────────────────────────────────
        priority_actions = _sort_by_priority(priority_actions)[:MAX_BRIEFING_ITEMS]
        
        # ── [5] 통계 요약 생성 ───────────────────────────────────────────────
        stats = _generate_stats(supabase, agent_id, today)
        
        return {
            "priority_actions": priority_actions,
            "stats": stats,
            "generated_at": datetime.datetime.now().isoformat(),
            "agent_id": agent_id,
        }
    
    except Exception as e:
        st.error(f"❌ 브리핑 생성 실패: {str(e)}")
        return {
            "priority_actions": [],
            "stats": {},
            "generated_at": datetime.datetime.now().isoformat(),
            "error": str(e),
        }


def _find_stuck_customers(supabase, agent_id: str, today: datetime.date) -> List[Dict[str, Any]]:
    """
    정체된 고객 찾기 (특정 단계에서 N일 이상 멈춰있는 고객)
    
    Args:
        supabase: Supabase 클라이언트
        agent_id: 설계사 ID
        today: 오늘 날짜
    
    Returns:
        List[Dict]: 정체된 고객 리스트
    """
    stuck_list = []
    
    try:
        # gk_people 테이블에서 current_stage와 last_activity_at 조회
        result = supabase.table("gk_people").select(
            "id, name, current_stage, last_activity_at"
        ).eq("agent_id", agent_id).eq("is_deleted", False).execute()
        
        if not result.data:
            return stuck_list
        
        for person in result.data:
            last_activity = person.get("last_activity_at")
            if not last_activity:
                continue
            
            try:
                last_activity_date = datetime.datetime.fromisoformat(last_activity).date()
                days_stuck = (today - last_activity_date).days
                
                if days_stuck >= STUCK_THRESHOLD_DAYS:
                    stuck_list.append({
                        "type": "stuck_customer",
                        "priority": 1,  # 최고 우선순위
                        "customer_id": person.get("id"),
                        "customer_name": person.get("name", "이름 없음"),
                        "current_stage": person.get("current_stage", "알 수 없음"),
                        "days_stuck": days_stuck,
                        "last_activity_at": last_activity,
                        "action_required": f"{person.get('current_stage', '현재 단계')}에서 {days_stuck}일째 정체 중 - 즉시 연락 필요",
                    })
            except Exception:
                continue
    
    except Exception as e:
        st.warning(f"⚠️ 정체 고객 조회 실패: {str(e)}")
    
    return stuck_list


def _find_birthday_customers(supabase, agent_id: str, today: datetime.date) -> List[Dict[str, Any]]:
    """
    생일 고객 찾기 (오늘 ± N일)
    
    Args:
        supabase: Supabase 클라이언트
        agent_id: 설계사 ID
        today: 오늘 날짜
    
    Returns:
        List[Dict]: 생일 고객 리스트
    """
    birthday_list = []
    
    try:
        # gk_people 테이블에서 birth_date 조회
        result = supabase.table("gk_people").select(
            "id, name, birth_date"
        ).eq("agent_id", agent_id).eq("is_deleted", False).execute()
        
        if not result.data:
            return birthday_list
        
        for person in result.data:
            birth_date_str = person.get("birth_date")
            if not birth_date_str:
                continue
            
            try:
                birth_date = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d").date()
                
                # 올해 생일 계산
                this_year_birthday = birth_date.replace(year=today.year)
                days_until_birthday = (this_year_birthday - today).days
                
                if abs(days_until_birthday) <= BIRTHDAY_ALERT_RANGE_DAYS:
                    birthday_list.append({
                        "type": "birthday",
                        "priority": 2,
                        "customer_id": person.get("id"),
                        "customer_name": person.get("name", "이름 없음"),
                        "birth_date": birth_date_str,
                        "days_until_birthday": days_until_birthday,
                        "action_required": f"생일 {abs(days_until_birthday)}일 {'전' if days_until_birthday > 0 else '후'} - 축하 메시지 발송 권장",
                    })
            except Exception:
                continue
    
    except Exception as e:
        st.warning(f"⚠️ 생일 고객 조회 실패: {str(e)}")
    
    return birthday_list


def _find_expiring_policies(supabase, agent_id: str, today: datetime.date) -> List[Dict[str, Any]]:
    """
    만기 임박 계약 찾기 (N일 이내)
    
    Args:
        supabase: Supabase 클라이언트
        agent_id: 설계사 ID
        today: 오늘 날짜
    
    Returns:
        List[Dict]: 만기 임박 계약 리스트
    """
    expiring_list = []
    
    try:
        # gk_policies 테이블에서 expiry_date 조회
        result = supabase.table("gk_policies").select(
            "id, policy_number, insurance_company, product_name, expiry_date"
        ).eq("agent_id", agent_id).eq("is_deleted", False).execute()
        
        if not result.data:
            return expiring_list
        
        for policy in result.data:
            expiry_date_str = policy.get("expiry_date")
            if not expiry_date_str:
                continue
            
            try:
                expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                days_until_expiry = (expiry_date - today).days
                
                if 0 <= days_until_expiry <= EXPIRY_ALERT_DAYS:
                    expiring_list.append({
                        "type": "expiring_policy",
                        "priority": 3,
                        "policy_id": policy.get("id"),
                        "policy_number": policy.get("policy_number", "번호 없음"),
                        "insurance_company": policy.get("insurance_company", "회사 없음"),
                        "product_name": policy.get("product_name", "상품명 없음"),
                        "expiry_date": expiry_date_str,
                        "days_until_expiry": days_until_expiry,
                        "action_required": f"만기 {days_until_expiry}일 전 - 갱신 상담 필요",
                    })
            except Exception:
                continue
    
    except Exception as e:
        st.warning(f"⚠️ 만기 계약 조회 실패: {str(e)}")
    
    return expiring_list


def _sort_by_priority(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    우선순위 정렬 (priority 값이 낮을수록 우선순위 높음)
    
    Args:
        actions: 액션 리스트
    
    Returns:
        List[Dict]: 정렬된 액션 리스트
    """
    return sorted(actions, key=lambda x: (x.get("priority", 999), x.get("days_stuck", 0)), reverse=True)


def _generate_stats(supabase, agent_id: str, today: datetime.date) -> Dict[str, Any]:
    """
    통계 요약 생성
    
    Args:
        supabase: Supabase 클라이언트
        agent_id: 설계사 ID
        today: 오늘 날짜
    
    Returns:
        Dict: 통계 데이터
    """
    stats = {
        "total_customers": 0,
        "active_policies": 0,
        "today_schedules": 0,
    }
    
    try:
        # 전체 고객 수
        people_result = supabase.table("gk_people").select(
            "id", count="exact"
        ).eq("agent_id", agent_id).eq("is_deleted", False).execute()
        stats["total_customers"] = people_result.count or 0
        
        # 활성 계약 수
        policies_result = supabase.table("gk_policies").select(
            "id", count="exact"
        ).eq("agent_id", agent_id).eq("is_deleted", False).execute()
        stats["active_policies"] = policies_result.count or 0
        
        # 오늘 일정 수
        schedules_result = supabase.table("gk_schedules").select(
            "id", count="exact"
        ).eq("agent_id", agent_id).gte("scheduled_at", today.isoformat()).lt(
            "scheduled_at", (today + datetime.timedelta(days=1)).isoformat()
        ).execute()
        stats["today_schedules"] = schedules_result.count or 0
    
    except Exception as e:
        st.warning(f"⚠️ 통계 생성 실패: {str(e)}")
    
    return stats


# ══════════════════════════════════════════════════════════════════════════════
# §3 브리핑 메시지 생성 (AI 음성 스타일)
# ══════════════════════════════════════════════════════════════════════════════

def format_briefing_message(action: Dict[str, Any]) -> str:
    """
    브리핑 액션을 AI 음성 스타일 메시지로 변환
    
    Args:
        action: 브리핑 액션 데이터
    
    Returns:
        str: 포맷된 메시지
    """
    action_type = action.get("type", "")
    
    if action_type == "stuck_customer":
        return (
            f"🚨 **{action.get('customer_name')}** 고객님이 "
            f"**{action.get('current_stage')}** 단계에서 "
            f"**{action.get('days_stuck')}일째** 정체 중입니다. "
            f"즉시 연락하여 다음 단계로 진행하세요."
        )
    
    elif action_type == "birthday":
        days = action.get("days_until_birthday", 0)
        if days == 0:
            return (
                f"🎂 **{action.get('customer_name')}** 고객님의 생일이 **오늘**입니다! "
                f"축하 메시지를 발송하여 관계를 강화하세요."
            )
        elif days > 0:
            return (
                f"🎉 **{action.get('customer_name')}** 고객님의 생일이 **{days}일 후**입니다. "
                f"미리 축하 메시지를 준비하세요."
            )
        else:
            return (
                f"🎁 **{action.get('customer_name')}** 고객님의 생일이 **{abs(days)}일 전**이었습니다. "
                f"늦었지만 축하 메시지를 보내보세요."
            )
    
    elif action_type == "expiring_policy":
        return (
            f"⏰ **{action.get('insurance_company')}** "
            f"**{action.get('product_name')}** 계약이 "
            f"**{action.get('days_until_expiry')}일 후** 만기됩니다. "
            f"갱신 상담을 진행하세요."
        )
    
    else:
        return action.get("action_required", "액션이 필요합니다.")


def get_briefing_icon(action_type: str) -> str:
    """
    브리핑 타입별 아이콘 반환
    
    Args:
        action_type: 액션 타입
    
    Returns:
        str: 이모지 아이콘
    """
    icons = {
        "stuck_customer": "🚨",
        "birthday": "🎂",
        "expiring_policy": "⏰",
    }
    return icons.get(action_type, "📌")
