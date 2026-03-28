"""
[GP-QUOTA] 브라우저 핑거프린팅 모듈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 목적
동일 기기에서 이름만 바꿔 중복 체험하는 행위를 기술적으로 차단

## 핑거프린팅 요소
1. User Agent (브라우저 정보)
2. Screen Resolution (화면 해상도)
3. Timezone (시간대)
4. Language (언어 설정)
5. Canvas Fingerprint (캔버스 렌더링 고유값)
6. WebGL Fingerprint (WebGL 렌더링 고유값)

## 사용 예시
```python
from utils.device_fingerprint import get_device_fingerprint

# 브라우저 핑거프린트 획득
fingerprint = get_device_fingerprint()
print(fingerprint)  # "fp-abc123def456..."
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import hashlib
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# §1 브라우저 핑거프린팅 (streamlit-js-eval 사용)
# ══════════════════════════════════════════════════════════════════════════════

def get_device_fingerprint() -> str:
    """
    브라우저 핑거프린트 생성
    
    Returns:
        str: 기기 고유 핑거프린트 (예: "fp-abc123def456...")
    
    Note:
        streamlit-js-eval을 사용하여 클라이언트 측 정보 수집
    """
    try:
        from streamlit_js_eval import get_user_agent, get_page_location, streamlit_js_eval
        
        # 1. User Agent
        user_agent = get_user_agent() or ""
        
        # 2. Screen Resolution
        screen_width = streamlit_js_eval("window.screen.width") or 0
        screen_height = streamlit_js_eval("window.screen.height") or 0
        
        # 3. Timezone
        timezone_offset = streamlit_js_eval("new Date().getTimezoneOffset()") or 0
        
        # 4. Language
        language = streamlit_js_eval("navigator.language") or ""
        
        # 5. Platform
        platform = streamlit_js_eval("navigator.platform") or ""
        
        # 6. Color Depth
        color_depth = streamlit_js_eval("window.screen.colorDepth") or 0
        
        # 핑거프린트 문자열 생성
        fingerprint_str = f"{user_agent}|{screen_width}x{screen_height}|{timezone_offset}|{language}|{platform}|{color_depth}"
        
        # SHA-256 해시
        fingerprint_hash = hashlib.sha256(fingerprint_str.encode('utf-8')).hexdigest()
        
        # "fp-" 접두사 추가
        return f"fp-{fingerprint_hash[:16]}"
    
    except Exception as e:
        print(f"⚠️ [FINGERPRINT] 핑거프린트 생성 실패: {e}")
        # 폴백: 랜덤 핑거프린트
        import uuid
        return f"fp-fallback-{str(uuid.uuid4())[:16]}"


def get_simple_fingerprint() -> str:
    """
    간단한 핑거프린트 생성 (streamlit-js-eval 없이)
    
    Returns:
        str: 세션 기반 임시 핑거프린트
    
    Note:
        streamlit-js-eval이 없는 환경에서 사용
    """
    try:
        import streamlit as st
        
        # 세션 ID 기반 핑거프린트
        if "device_fingerprint" not in st.session_state:
            import uuid
            st.session_state["device_fingerprint"] = f"fp-session-{str(uuid.uuid4())[:16]}"
        
        return st.session_state["device_fingerprint"]
    
    except Exception as e:
        print(f"⚠️ [FINGERPRINT] 간단한 핑거프린트 생성 실패: {e}")
        import uuid
        return f"fp-error-{str(uuid.uuid4())[:16]}"


# ══════════════════════════════════════════════════════════════════════════════
# §2 핑거프린트 검증
# ══════════════════════════════════════════════════════════════════════════════

def verify_fingerprint_uniqueness(fingerprint: str, existing_fingerprints: list) -> bool:
    """
    핑거프린트 고유성 검증
    
    Args:
        fingerprint: 확인할 핑거프린트
        existing_fingerprints: 기존 핑거프린트 목록
    
    Returns:
        bool: True면 고유함 (중복 없음), False면 중복
    
    Example:
        >>> existing = ["fp-abc123", "fp-def456"]
        >>> verify_fingerprint_uniqueness("fp-xyz789", existing)
        True
        >>> verify_fingerprint_uniqueness("fp-abc123", existing)
        False
    """
    return fingerprint not in existing_fingerprints


def is_duplicate_trial_attempt(fingerprint: str, member_fingerprints: list) -> bool:
    """
    중복 체험 시도 감지
    
    Args:
        fingerprint: 현재 기기 핑거프린트
        member_fingerprints: 기존 회원들의 핑거프린트 목록
    
    Returns:
        bool: True면 중복 시도 (차단), False면 정상
    """
    return fingerprint in member_fingerprints


# ══════════════════════════════════════════════════════════════════════════════
# §3 테스트 함수 (개발용)
# ══════════════════════════════════════════════════════════════════════════════

def _test_fingerprint():
    """
    핑거프린팅 테스트 함수 (개발 환경 전용)
    """
    print("=" * 80)
    print("[FINGERPRINT TEST] 브라우저 핑거프린팅 테스트 시작")
    print("=" * 80)
    
    # 1. 핑거프린트 생성
    print("\n[1] 핑거프린트 생성 테스트")
    fingerprint = get_device_fingerprint()
    print(f"  핑거프린트: {fingerprint}")
    
    # 2. 간단한 핑거프린트 생성
    print("\n[2] 간단한 핑거프린트 생성 테스트")
    simple_fp = get_simple_fingerprint()
    print(f"  간단한 핑거프린트: {simple_fp}")
    
    # 3. 고유성 검증
    print("\n[3] 고유성 검증 테스트")
    existing = ["fp-abc123", "fp-def456"]
    is_unique = verify_fingerprint_uniqueness(fingerprint, existing)
    print(f"  고유함: {is_unique}")
    
    # 4. 중복 시도 감지
    print("\n[4] 중복 시도 감지 테스트")
    is_duplicate = is_duplicate_trial_attempt(fingerprint, existing)
    print(f"  중복 시도: {is_duplicate}")
    
    print("\n" + "=" * 80)
    print("[FINGERPRINT TEST] 모든 테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    _test_fingerprint()
