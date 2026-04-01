"""
session_optimizer.py — 최종 세션 및 캐시 정리 최적화
[GP-STEP9] Goldkey AI Masters 2026

세션 최적화:
- 12단계 완료 고객 임시 데이터 정리
- 불필요한 세션 상태 캐시 정리
- 메모리 최적화
- loading_skeleton 활용 동기화
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any, List
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 세션 상태 정리
# ══════════════════════════════════════════════════════════════════════════════

def cleanup_completed_customer_session(person_id: str) -> int:
    """
    12단계 완료 고객의 임시 세션 데이터 정리
    
    Args:
        person_id: 고객 UUID
    
    Returns:
        int: 정리된 세션 키 개수
    """
    if not person_id:
        return 0
    
    # 정리 대상 세션 키 패턴
    cleanup_patterns = [
        f"proposal_{person_id}",
        f"closing_completed_{person_id}",
        f"show_closing_{person_id}",
        f"referral_completed_{person_id}",
        f"show_referral_request_{person_id}",
        f"signature_confirmed",
        f"checklist_",
        f"referee_name_{person_id}",
        f"referee_contact_{person_id}",
        f"referral_note_{person_id}",
        f"referral_tone_selector",
        f"script_tone_selector"
    ]
    
    cleaned_count = 0
    
    for key in list(st.session_state.keys()):
        for pattern in cleanup_patterns:
            if pattern in key:
                try:
                    del st.session_state[key]
                    cleaned_count += 1
                except Exception:
                    pass
                break
    
    return cleaned_count


def cleanup_all_temporary_sessions() -> Dict[str, int]:
    """
    모든 임시 세션 데이터 정리 (전역 최적화)
    
    Returns:
        dict: 정리 통계
    """
    # 정리 대상 임시 키 패턴
    temp_patterns = [
        "_temp_",
        "_cache_",
        "_loading_",
        "_pending_",
        "checklist_",
        "signature_",
        "tone_selector"
    ]
    
    cleaned_keys = []
    
    for key in list(st.session_state.keys()):
        # 임시 패턴 매칭
        is_temp = any(pattern in key for pattern in temp_patterns)
        
        if is_temp:
            try:
                del st.session_state[key]
                cleaned_keys.append(key)
            except Exception:
                pass
    
    return {
        "total_cleaned": len(cleaned_keys),
        "cleaned_keys": cleaned_keys[:10]  # 최대 10개만 반환
    }


# ══════════════════════════════════════════════════════════════════════════════
# [2] 고객별 세션 상태 확인
# ══════════════════════════════════════════════════════════════════════════════

def get_customer_session_status(person_id: str, agent_id: str) -> Dict[str, Any]:
    """
    고객별 세션 상태 확인
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        dict: 세션 상태 정보
    """
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return {"stage": 0, "ready_for_cleanup": False}
        
        # 고객 정보 조회
        customer = (
            sb.table("gk_people")
            .select("current_stage, last_contact")
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .maybe_single()
            .execute()
        )
        
        if not customer or not customer.data:
            return {"stage": 0, "ready_for_cleanup": False}
        
        current_stage = customer.data.get("current_stage", 0)
        last_contact = customer.data.get("last_contact", "")
        
        # 12단계 완료 여부 확인
        ready_for_cleanup = current_stage >= 12
        
        # 마지막 접촉 후 경과 시간 계산
        days_since_contact = 0
        if last_contact:
            try:
                last_contact_dt = datetime.datetime.fromisoformat(last_contact)
                days_since_contact = (datetime.datetime.now() - last_contact_dt).days
            except Exception:
                pass
        
        return {
            "stage": current_stage,
            "ready_for_cleanup": ready_for_cleanup,
            "days_since_contact": days_since_contact,
            "last_contact": last_contact
        }
    except Exception:
        return {"stage": 0, "ready_for_cleanup": False}


# ══════════════════════════════════════════════════════════════════════════════
# [3] 자동 세션 정리 (백그라운드)
# ══════════════════════════════════════════════════════════════════════════════

def auto_cleanup_sessions(agent_id: str) -> Dict[str, Any]:
    """
    자동 세션 정리 (백그라운드 작업)
    
    Args:
        agent_id: 설계사 ID
    
    Returns:
        dict: 정리 결과
    """
    try:
        from db_utils import _get_sb
        sb = _get_sb()
        if not sb:
            return {"success": False, "cleaned_count": 0}
        
        # 12단계 완료 고객 목록 조회
        completed_customers = (
            sb.table("gk_people")
            .select("person_id")
            .eq("agent_id", agent_id)
            .gte("current_stage", 12)
            .eq("is_deleted", False)
            .execute()
        )
        
        total_cleaned = 0
        
        for customer in (completed_customers.data or []):
            person_id = customer.get("person_id")
            if person_id:
                cleaned = cleanup_completed_customer_session(person_id)
                total_cleaned += cleaned
        
        # 전역 임시 세션 정리
        temp_cleanup = cleanup_all_temporary_sessions()
        total_cleaned += temp_cleanup.get("total_cleaned", 0)
        
        return {
            "success": True,
            "cleaned_count": total_cleaned,
            "completed_customers": len(completed_customers.data or [])
        }
    except Exception:
        return {"success": False, "cleaned_count": 0}


# ══════════════════════════════════════════════════════════════════════════════
# [4] 세션 정리 UI (관리자용)
# ══════════════════════════════════════════════════════════════════════════════

def render_session_optimizer_ui(agent_id: str):
    """
    세션 최적화 UI (관리자용)
    
    Args:
        agent_id: 설계사 ID
    """
    st.markdown(
        "<div style='font-size:1.2rem;font-weight:900;color:#1E3A8A;margin-bottom:16px;'>"
        "🔧 세션 최적화</div>",
        unsafe_allow_html=True
    )
    
    # 현재 세션 상태
    total_keys = len(st.session_state.keys())
    
    st.markdown(
        f"<div style='background:#F3F4F6;border:1.5px solid #9CA3AF;border-radius:10px;padding:16px;margin-bottom:16px;'>"
        f"<div style='font-size:.88rem;font-weight:700;color:#374151;margin-bottom:8px;'>"
        f"현재 세션 상태</div>"
        f"<div style='font-size:.82rem;color:#64748B;'>"
        f"총 세션 키: {total_keys}개</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # 자동 정리 버튼
    if st.button("🧹 자동 세션 정리", key="auto_cleanup_btn", use_container_width=True):
        with st.spinner("세션을 정리하는 중..."):
            from loading_skeleton import render_loading_spinner
            render_loading_spinner("세션 최적화 진행 중...")
            
            result = auto_cleanup_sessions(agent_id)
            
            if result.get("success"):
                st.success(f"✅ {result.get('cleaned_count', 0)}개의 임시 세션이 정리되었습니다.")
                st.info(f"💡 {result.get('completed_customers', 0)}명의 완료 고객 세션이 최적화되었습니다.")
                st.rerun()
            else:
                st.error("❌ 세션 정리에 실패했습니다.")


# ══════════════════════════════════════════════════════════════════════════════
# [5] 세션 상태 모니터링
# ══════════════════════════════════════════════════════════════════════════════

def monitor_session_health() -> Dict[str, Any]:
    """
    세션 상태 건강도 모니터링
    
    Returns:
        dict: 세션 건강도 정보
    """
    total_keys = len(st.session_state.keys())
    
    # 임시 키 개수
    temp_keys = sum(1 for key in st.session_state.keys() 
                    if any(p in key for p in ["_temp_", "_cache_", "_loading_"]))
    
    # 고객 관련 키 개수
    customer_keys = sum(1 for key in st.session_state.keys() 
                        if any(p in key for p in ["proposal_", "closing_", "referral_"]))
    
    # 건강도 점수 계산 (0-100)
    health_score = 100
    
    if total_keys > 100:
        health_score -= min(50, (total_keys - 100) // 2)
    
    if temp_keys > 20:
        health_score -= min(30, (temp_keys - 20))
    
    health_score = max(0, health_score)
    
    # 상태 판정
    if health_score >= 80:
        status = "excellent"
        status_text = "우수"
        status_color = "#22C55E"
    elif health_score >= 60:
        status = "good"
        status_text = "양호"
        status_color = "#3B82F6"
    elif health_score >= 40:
        status = "fair"
        status_text = "보통"
        status_color = "#F59E0B"
    else:
        status = "poor"
        status_text = "나쁨"
        status_color = "#EF4444"
    
    return {
        "total_keys": total_keys,
        "temp_keys": temp_keys,
        "customer_keys": customer_keys,
        "health_score": health_score,
        "status": status,
        "status_text": status_text,
        "status_color": status_color,
        "needs_cleanup": health_score < 60
    }


# ══════════════════════════════════════════════════════════════════════════════
# [6] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시

### 1. 12단계 완료 시 자동 정리

```python
from session_optimizer import cleanup_completed_customer_session

# 고객이 12단계 완료 시
if current_stage >= 12:
    cleaned = cleanup_completed_customer_session(person_id)
    print(f"{cleaned}개의 임시 세션이 정리되었습니다.")
```

### 2. 앱 시작 시 자동 정리

```python
from session_optimizer import auto_cleanup_sessions

# crm_app_impl.py 진입점
if st.session_state.get("crm_user_id"):
    agent_id = st.session_state["crm_user_id"]
    
    # 1시간마다 자동 정리 (세션 상태로 관리)
    last_cleanup = st.session_state.get("last_cleanup_time", 0)
    current_time = datetime.datetime.now().timestamp()
    
    if current_time - last_cleanup > 3600:  # 1시간
        auto_cleanup_sessions(agent_id)
        st.session_state["last_cleanup_time"] = current_time
```

### 3. 세션 건강도 모니터링

```python
from session_optimizer import monitor_session_health

health = monitor_session_health()

if health.get("needs_cleanup"):
    st.warning(f"⚠️ 세션 최적화가 필요합니다. (건강도: {health.get('health_score')}/100)")
```

### 4. 관리자 UI

```python
from session_optimizer import render_session_optimizer_ui

# 관리자 화면
if st.session_state.get("crm_spa_screen") == "admin":
    agent_id = st.session_state.get("crm_user_id")
    render_session_optimizer_ui(agent_id)
```

## 정리 대상 세션 키

### 고객별 임시 키
- `proposal_{person_id}`: 제안서 데이터
- `closing_completed_{person_id}`: 체결 완료 플래그
- `show_closing_{person_id}`: 클로징 화면 표시 플래그
- `referral_completed_{person_id}`: 소개 완료 플래그
- `show_referral_request_{person_id}`: 소개 요청 화면 표시 플래그

### 전역 임시 키
- `signature_confirmed`: 전자 서명 확인
- `checklist_*`: 최종 확인 체크리스트
- `referee_name_*`: 피소개자 이름
- `referee_contact_*`: 피소개자 연락처
- `referral_note_*`: 소개 메모
- `*_tone_selector`: 톤 선택기

### 자동 정리 조건
1. 고객이 12단계 (소개 완료) 도달
2. 마지막 접촉 후 7일 경과
3. 세션 건강도 60점 미만
"""
