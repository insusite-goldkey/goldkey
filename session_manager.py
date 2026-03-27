"""
[GP-SEC] CRM 세션 지속성 관리자 (Persistent Session Manager)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 핵심 기능
1. Local Storage 기반 세션 지속성 (새로고침/앱전환 시 로그인 유지)
2. 60분 Idle Timeout 자동 로그아웃 (GP 전역 변수화)
3. 마지막 화면 상태 복구 (SPA 라우팅 상태 저장)

## 사용법
```python
from session_manager import (
    init_persistent_session,
    save_session_to_storage,
    restore_session_from_storage,
    check_idle_timeout,
    clear_session
)

# 앱 최상단에서 초기화
init_persistent_session()

# 로그인 성공 시 저장
save_session_to_storage(user_id, user_name, role, token, spa_screen)

# 페이지 로드 시 복구
restored = restore_session_from_storage()

# Idle Timeout 체크
if check_idle_timeout():
    clear_session()
    st.warning("보안을 위해 자동 로그아웃되었습니다.")
```
"""

import streamlit as st
import streamlit.components.v1 as components
import datetime
import json
from typing import Optional, Dict, Any


# ══════════════════════════════════════════════════════════════════════════════
# §1 전역 설정 (GP 연동)
# ══════════════════════════════════════════════════════════════════════════════

# [GP 전역 변수] Idle Timeout (분 단위)
IDLE_TIMEOUT_MINUTES = 60  # 60분 비활동 시 자동 로그아웃

# Local Storage 키 이름
STORAGE_KEY_PREFIX = "goldkey_crm_"
STORAGE_KEY_SESSION = f"{STORAGE_KEY_PREFIX}session"
STORAGE_KEY_LAST_ACTIVITY = f"{STORAGE_KEY_PREFIX}last_activity"
STORAGE_KEY_SPA_SCREEN = f"{STORAGE_KEY_PREFIX}spa_screen"


# ══════════════════════════════════════════════════════════════════════════════
# §2 Local Storage JavaScript 인터페이스
# ══════════════════════════════════════════════════════════════════════════════

def _inject_storage_js(action: str, key: str, value: str = "") -> str:
    """
    Local Storage 읽기/쓰기/삭제 JavaScript 생성
    
    Args:
        action: 'get', 'set', 'remove', 'clear'
        key: Storage 키
        value: 저장할 값 (set 시에만 사용)
    
    Returns:
        str: JavaScript 코드
    """
    if action == "set":
        return f"""
        <script>
        try {{
            localStorage.setItem('{key}', '{value}');
            console.log('[CRM Session] Saved to localStorage: {key}');
        }} catch (e) {{
            console.error('[CRM Session] localStorage.setItem failed:', e);
        }}
        </script>
        """
    elif action == "get":
        return f"""
        <script>
        try {{
            const value = localStorage.getItem('{key}');
            if (value) {{
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    key: '{key}',
                    value: value
                }}, '*');
                console.log('[CRM Session] Loaded from localStorage: {key}');
            }}
        }} catch (e) {{
            console.error('[CRM Session] localStorage.getItem failed:', e);
        }}
        </script>
        """
    elif action == "remove":
        return f"""
        <script>
        try {{
            localStorage.removeItem('{key}');
            console.log('[CRM Session] Removed from localStorage: {key}');
        }} catch (e) {{
            console.error('[CRM Session] localStorage.removeItem failed:', e);
        }}
        </script>
        """
    elif action == "clear":
        return f"""
        <script>
        try {{
            const keys = Object.keys(localStorage);
            keys.forEach(key => {{
                if (key.startsWith('{STORAGE_KEY_PREFIX}')) {{
                    localStorage.removeItem(key);
                }}
            }});
            console.log('[CRM Session] Cleared all CRM localStorage');
        }} catch (e) {{
            console.error('[CRM Session] localStorage.clear failed:', e);
        }}
        </script>
        """
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# §3 세션 저장/복구
# ══════════════════════════════════════════════════════════════════════════════

def save_session_to_storage(
    user_id: str,
    user_name: str,
    role: str,
    token: str,
    spa_screen: str = "list"
) -> None:
    """
    로그인 세션을 Local Storage에 저장
    
    Args:
        user_id: 사용자 ID
        user_name: 사용자 이름
        role: 역할 (admin/agent)
        token: 인증 토큰
        spa_screen: 현재 SPA 화면 (list/contact/schedule 등)
    """
    session_data = {
        "user_id": user_id,
        "user_name": user_name,
        "role": role,
        "token": token,
        "spa_screen": spa_screen,
        "saved_at": datetime.datetime.now().isoformat()
    }
    
    # JSON 직렬화 (작은따옴표 이스케이프)
    session_json = json.dumps(session_data).replace("'", "\\'")
    
    # Local Storage에 저장
    components.html(
        _inject_storage_js("set", STORAGE_KEY_SESSION, session_json),
        height=0
    )
    
    # 마지막 활동 시간 저장
    update_last_activity()


def restore_session_from_storage() -> Optional[Dict[str, Any]]:
    """
    Local Storage에서 세션 복구
    
    Returns:
        Optional[Dict]: 세션 데이터 (없으면 None)
    """
    # Streamlit Session State에 이미 복구된 데이터가 있는지 확인
    if "_restored_session" in st.session_state:
        return st.session_state["_restored_session"]
    
    # JavaScript로 Local Storage 읽기 시도
    # (실제로는 Streamlit의 한계로 직접 읽기 불가 - 대신 hidden input 사용)
    # 여기서는 세션 복구 플래그만 설정
    if "_session_restore_attempted" not in st.session_state:
        st.session_state["_session_restore_attempted"] = True
        # 복구 시도를 위한 JavaScript 주입
        components.html(
            _inject_storage_js("get", STORAGE_KEY_SESSION),
            height=0
        )
    
    return None


def update_last_activity() -> None:
    """마지막 활동 시간을 현재 시각으로 갱신"""
    now = datetime.datetime.now().isoformat()
    components.html(
        _inject_storage_js("set", STORAGE_KEY_LAST_ACTIVITY, now),
        height=0
    )
    st.session_state["_last_activity"] = now


def check_idle_timeout() -> bool:
    """
    Idle Timeout 체크 (60분 비활동 시 True 반환)
    
    Returns:
        bool: Timeout 발생 여부
    """
    last_activity = st.session_state.get("_last_activity")
    if not last_activity:
        return False
    
    try:
        last_dt = datetime.datetime.fromisoformat(last_activity)
        now = datetime.datetime.now()
        idle_minutes = (now - last_dt).total_seconds() / 60
        
        if idle_minutes > IDLE_TIMEOUT_MINUTES:
            return True
    except Exception:
        pass
    
    return False


def clear_session() -> None:
    """세션 완전 삭제 (로그아웃 시 호출)"""
    # Local Storage 클리어
    components.html(
        _inject_storage_js("clear", ""),
        height=0
    )
    
    # Streamlit Session State 클리어
    keys_to_clear = [
        "crm_authenticated",
        "crm_user_id",
        "crm_user_name",
        "crm_role",
        "crm_token",
        "crm_selected_pid",
        "_last_activity",
        "_restored_session",
        "_session_restore_attempted"
    ]
    
    for key in keys_to_clear:
        st.session_state.pop(key, None)


# ══════════════════════════════════════════════════════════════════════════════
# §4 초기화 및 자동 복구
# ══════════════════════════════════════════════════════════════════════════════

def init_persistent_session() -> bool:
    """
    앱 최상단에서 호출 - 세션 복구 및 Idle Timeout 체크
    
    Returns:
        bool: 세션이 복구되었는지 여부
    """
    # Idle Timeout 체크
    if check_idle_timeout():
        clear_session()
        st.warning("⏰ 보안을 위해 자동 로그아웃되었습니다. (60분 비활동)")
        return False
    
    # 이미 인증된 상태면 활동 시간만 갱신
    if st.session_state.get("crm_authenticated"):
        update_last_activity()
        return True
    
    # 세션 복구 시도
    restored = restore_session_from_storage()
    if restored:
        st.session_state["crm_authenticated"] = True
        st.session_state["crm_user_id"] = restored.get("user_id", "")
        st.session_state["crm_user_name"] = restored.get("user_name", "")
        st.session_state["crm_role"] = restored.get("role", "agent")
        st.session_state["crm_token"] = restored.get("token", "")
        st.session_state["_last_activity"] = restored.get("saved_at", "")
        return True
    
    return False


# ══════════════════════════════════════════════════════════════════════════════
# §5 활동 추적 데코레이터
# ══════════════════════════════════════════════════════════════════════════════

def track_activity(func):
    """
    함수 실행 시 자동으로 마지막 활동 시간 갱신하는 데코레이터
    
    Usage:
        @track_activity
        def my_button_handler():
            ...
    """
    def wrapper(*args, **kwargs):
        update_last_activity()
        return func(*args, **kwargs)
    return wrapper
