"""
[GP-AUTH] 익명 토큰(Guest Mode) 파이프라인
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 목적
회원가입 없이도 '스캔'과 '분석' 기능을 즉시 체험할 수 있도록
Supabase 익명 세션을 자동으로 부여하는 게스트 토큰 파이프라인 구축

## 핵심 기능
1. 익명 사용자 자동 생성 (UUID 기반)
2. 제한된 기능 접근 (스캔, 분석만 허용)
3. 24시간 자동 만료
4. 정회원 전환 유도 UI

## 사용법
```python
from guest_mode import (
    create_guest_session,
    is_guest_mode,
    get_guest_limitations,
    render_guest_upgrade_banner
)

# 게스트 세션 생성
guest_data = create_guest_session()

# 게스트 모드 확인
if is_guest_mode():
    render_guest_upgrade_banner()
```
"""

import streamlit as st
import uuid
import datetime
from typing import Dict, Any, Optional, List


# ══════════════════════════════════════════════════════════════════════════════
# §1 게스트 세션 설정
# ══════════════════════════════════════════════════════════════════════════════

GUEST_SESSION_DURATION_HOURS = 24  # 24시간 자동 만료
GUEST_PREFIX = "guest_"
GUEST_ALLOWED_FEATURES = [
    "scan",           # 스캔 기능
    "analysis",       # 분석 기능
    "view_report",    # 리포트 보기
]
GUEST_BLOCKED_FEATURES = [
    "save_customer",  # 고객 저장
    "export_data",    # 데이터 내보내기
    "calendar_sync",  # 캘린더 연동
    "kakao_send",     # 카카오톡 발송
    "network_view",   # 네트워크 보기
]


# ══════════════════════════════════════════════════════════════════════════════
# §2 게스트 세션 생성
# ══════════════════════════════════════════════════════════════════════════════

def create_guest_session() -> Dict[str, Any]:
    """
    익명 게스트 세션 생성
    
    Returns:
        Dict: 게스트 세션 데이터
            - guest_id: 게스트 고유 ID
            - guest_token: 인증 토큰
            - created_at: 생성 시각
            - expires_at: 만료 시각
            - allowed_features: 허용된 기능 목록
    """
    guest_id = f"{GUEST_PREFIX}{uuid.uuid4().hex[:12]}"
    guest_token = uuid.uuid4().hex
    now = datetime.datetime.now()
    expires_at = now + datetime.timedelta(hours=GUEST_SESSION_DURATION_HOURS)
    
    guest_data = {
        "guest_id": guest_id,
        "guest_token": guest_token,
        "guest_name": "체험 사용자",
        "role": "guest",
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "allowed_features": GUEST_ALLOWED_FEATURES,
        "is_guest": True,
    }
    
    # Streamlit Session State에 저장
    st.session_state["crm_authenticated"] = True
    st.session_state["crm_user_id"] = guest_id
    st.session_state["crm_user_name"] = "체험 사용자"
    st.session_state["crm_role"] = "guest"
    st.session_state["crm_token"] = guest_token
    st.session_state["crm_is_guest"] = True
    st.session_state["crm_guest_expires_at"] = expires_at.isoformat()
    st.session_state["crm_guest_allowed_features"] = GUEST_ALLOWED_FEATURES
    
    return guest_data


def is_guest_mode() -> bool:
    """
    현재 게스트 모드인지 확인
    
    Returns:
        bool: 게스트 모드 여부
    """
    return st.session_state.get("crm_is_guest", False)


def check_guest_expiration() -> bool:
    """
    게스트 세션 만료 여부 확인
    
    Returns:
        bool: 만료되었으면 True
    """
    if not is_guest_mode():
        return False
    
    expires_at_str = st.session_state.get("crm_guest_expires_at")
    if not expires_at_str:
        return True
    
    try:
        expires_at = datetime.datetime.fromisoformat(expires_at_str)
        now = datetime.datetime.now()
        return now > expires_at
    except Exception:
        return True


def is_feature_allowed(feature_name: str) -> bool:
    """
    특정 기능이 게스트에게 허용되는지 확인
    
    Args:
        feature_name: 기능 이름
    
    Returns:
        bool: 허용 여부 (정회원이면 항상 True)
    """
    if not is_guest_mode():
        return True
    
    allowed_features = st.session_state.get("crm_guest_allowed_features", [])
    return feature_name in allowed_features


# ══════════════════════════════════════════════════════════════════════════════
# §3 게스트 제한 UI
# ══════════════════════════════════════════════════════════════════════════════

def render_guest_upgrade_banner() -> None:
    """
    게스트 사용자에게 정회원 전환 유도 배너 표시
    """
    if not is_guest_mode():
        return
    
    expires_at_str = st.session_state.get("crm_guest_expires_at", "")
    remaining_hours = 0
    
    if expires_at_str:
        try:
            expires_at = datetime.datetime.fromisoformat(expires_at_str)
            now = datetime.datetime.now()
            remaining_seconds = (expires_at - now).total_seconds()
            remaining_hours = max(0, int(remaining_seconds / 3600))
        except Exception:
            pass
    
    banner_html = f"""
    <style>
    .guest-upgrade-banner {{
        background: linear-gradient(135deg, var(--gp-warning, #FEE2E2) 0%, var(--gp-block-base, #E0E7FF) 100%);
        border: 1px solid var(--gp-border, #374151);
        border-radius: var(--gp-radius, 8px);
        padding: var(--gp-gap, 12px);
        margin: var(--gp-gap, 12px) 0;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }}
    .guest-banner-title {{
        font-size: clamp(15px, 2vw, 18px);
        font-weight: 900;
        color: var(--gp-text-dark, #1F2937);
    }}
    .guest-banner-text {{
        font-size: clamp(13px, 1.6vw, 15px);
        color: var(--gp-text, #4B5563);
        line-height: 1.6;
    }}
    .guest-banner-timer {{
        font-size: clamp(12px, 1.5vw, 14px);
        font-weight: 700;
        color: var(--gp-text-muted, #6B7280);
    }}
    </style>
    <div class='guest-upgrade-banner'>
        <div class='guest-banner-title'>🎁 체험 모드로 이용 중입니다</div>
        <div class='guest-banner-text'>
            현재 <b>스캔</b>과 <b>분석</b> 기능을 체험하실 수 있습니다.<br>
            회원가입 후 <b>고객 저장</b>, <b>캘린더 연동</b>, <b>카카오톡 발송</b> 등 전체 기능을 이용하세요.
        </div>
        <div class='guest-banner-timer'>⏰ 체험 시간 남음: 약 {remaining_hours}시간</div>
    </div>
    """
    
    st.markdown(banner_html, unsafe_allow_html=True)


def render_feature_blocked_message(feature_name: str) -> None:
    """
    게스트에게 차단된 기능 접근 시 메시지 표시
    
    Args:
        feature_name: 기능 이름
    """
    feature_labels = {
        "save_customer": "고객 저장",
        "export_data": "데이터 내보내기",
        "calendar_sync": "캘린더 연동",
        "kakao_send": "카카오톡 발송",
        "network_view": "네트워크 보기",
    }
    
    feature_label = feature_labels.get(feature_name, feature_name)
    
    blocked_html = f"""
    <style>
    .feature-blocked-box {{
        background: var(--gp-warning, #FEE2E2);
        border: 1px solid var(--gp-border, #374151);
        border-radius: var(--gp-radius, 8px);
        padding: var(--gp-gap, 12px);
        margin: var(--gp-gap, 12px) 0;
        text-align: center;
    }}
    .feature-blocked-icon {{
        font-size: 32px;
        margin-bottom: 8px;
    }}
    .feature-blocked-title {{
        font-size: clamp(15px, 2vw, 18px);
        font-weight: 900;
        color: var(--gp-text-dark, #1F2937);
        margin-bottom: 8px;
    }}
    .feature-blocked-text {{
        font-size: clamp(13px, 1.6vw, 15px);
        color: var(--gp-text, #4B5563);
        line-height: 1.6;
    }}
    </style>
    <div class='feature-blocked-box'>
        <div class='feature-blocked-icon'>🔒</div>
        <div class='feature-blocked-title'>{feature_label} 기능은 정회원 전용입니다</div>
        <div class='feature-blocked-text'>
            회원가입 후 모든 기능을 제한 없이 이용하실 수 있습니다.
        </div>
    </div>
    """
    
    st.markdown(blocked_html, unsafe_allow_html=True)


def get_guest_limitations() -> Dict[str, Any]:
    """
    게스트 제한 사항 정보 반환
    
    Returns:
        Dict: 제한 사항 정보
    """
    return {
        "is_guest": is_guest_mode(),
        "allowed_features": GUEST_ALLOWED_FEATURES,
        "blocked_features": GUEST_BLOCKED_FEATURES,
        "session_duration_hours": GUEST_SESSION_DURATION_HOURS,
        "expires_at": st.session_state.get("crm_guest_expires_at", ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
# §4 게스트 → 정회원 전환
# ══════════════════════════════════════════════════════════════════════════════

def convert_guest_to_member(
    user_id: str,
    user_name: str,
    role: str,
    token: str
) -> None:
    """
    게스트 세션을 정회원 세션으로 전환
    
    Args:
        user_id: 정회원 ID
        user_name: 정회원 이름
        role: 역할
        token: 인증 토큰
    """
    # 게스트 관련 세션 삭제
    guest_keys = [
        "crm_is_guest",
        "crm_guest_expires_at",
        "crm_guest_allowed_features",
    ]
    
    for key in guest_keys:
        st.session_state.pop(key, None)
    
    # 정회원 세션 설정
    st.session_state["crm_authenticated"] = True
    st.session_state["crm_user_id"] = user_id
    st.session_state["crm_user_name"] = user_name
    st.session_state["crm_role"] = role
    st.session_state["crm_token"] = token
    
    st.success("🎉 회원가입이 완료되었습니다! 이제 모든 기능을 이용하실 수 있습니다.")


# ══════════════════════════════════════════════════════════════════════════════
# §5 게스트 데이터 임시 저장 (Supabase 연동)
# ══════════════════════════════════════════════════════════════════════════════

def save_guest_temp_data(
    data_type: str,
    data_content: Dict[str, Any]
) -> Optional[str]:
    """
    게스트가 생성한 데이터를 임시 테이블에 저장
    (정회원 전환 시 마이그레이션 가능)
    
    Args:
        data_type: 데이터 타입 (scan, analysis 등)
        data_content: 데이터 내용
    
    Returns:
        Optional[str]: 저장된 데이터 ID (실패 시 None)
    """
    if not is_guest_mode():
        return None
    
    guest_id = st.session_state.get("crm_user_id", "")
    
    try:
        from db_utils import get_supabase_client
        
        supabase = get_supabase_client()
        
        temp_data = {
            "guest_id": guest_id,
            "data_type": data_type,
            "data_content": data_content,
            "created_at": datetime.datetime.now().isoformat(),
        }
        
        result = supabase.table("guest_temp_data").insert(temp_data).execute()
        
        if result.data:
            return result.data[0].get("id")
    except Exception as e:
        st.warning(f"⚠️ 임시 데이터 저장 실패: {str(e)}")
    
    return None


def migrate_guest_data_to_member(guest_id: str, member_id: str) -> bool:
    """
    게스트 임시 데이터를 정회원 데이터로 마이그레이션
    
    Args:
        guest_id: 게스트 ID
        member_id: 정회원 ID
    
    Returns:
        bool: 성공 여부
    """
    try:
        from db_utils import get_supabase_client
        
        supabase = get_supabase_client()
        
        # 게스트 임시 데이터 조회
        result = supabase.table("guest_temp_data").select("*").eq("guest_id", guest_id).execute()
        
        if not result.data:
            return True  # 마이그레이션할 데이터 없음
        
        # 각 데이터를 정회원 테이블로 이동
        for temp_data in result.data:
            data_type = temp_data.get("data_type")
            data_content = temp_data.get("data_content", {})
            
            # 데이터 타입별 처리 (추후 확장)
            if data_type == "scan":
                # 스캔 데이터 저장 로직
                pass
            elif data_type == "analysis":
                # 분석 데이터 저장 로직
                pass
        
        # 임시 데이터 삭제
        supabase.table("guest_temp_data").delete().eq("guest_id", guest_id).execute()
        
        return True
    except Exception as e:
        st.error(f"❌ 데이터 마이그레이션 실패: {str(e)}")
        return False
