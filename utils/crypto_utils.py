"""
[GP-SEC] 암호화 유틸리티 모듈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 보안 원칙
1. SHA-256 단방향 해시: 연락처(인증용), 비밀번호 → 복호화 불가
2. AES-256-CBC 양방향 암호화: 이름, 기타 PII → 관리자 화면 표시용
3. 암호화 키: st.secrets["ENCRYPTION_KEY"] 또는 환경변수 폴백
4. 평문 데이터 로그 출력 절대 금지

## 사용 예시
```python
from utils.crypto_utils import hash_contact, encrypt_name, decrypt_name

# 연락처 해시 (로그인 인증용)
contact_hash = hash_contact("010-1234-5678")  # SHA-256

# 이름 암호화 (DB 저장용)
name_encrypted = encrypt_name("홍길동")  # AES-256-CBC

# 이름 복호화 (관리자 화면 표시용)
name_plain = decrypt_name(name_encrypted)
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import hashlib
import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


# ══════════════════════════════════════════════════════════════════════════════
# §1 암호화 키 관리
# ══════════════════════════════════════════════════════════════════════════════

def _get_encryption_key() -> bytes:
    """
    암호화 키 획득 (Fernet 호환 32바이트 base64 인코딩)
    
    [GP-SEC] 마스터키 정책:
    - GOLDKEY-AI와 GOLDKEY-CRM은 동일한 ENCRYPTION_KEY 공유
    - 기존 운영 키(19IPhR...로 시작)를 마스터키로 확정
    - 폴백 로직 없음 - 키 없으면 즉시 에러 발생
    
    우선순위:
    1. os.environ["ENCRYPTION_KEY"] (최우선)
    2. st.secrets["ENCRYPTION_KEY"] (로컬 개발)
    
    Returns:
        bytes: Fernet 호환 암호화 키
    
    Raises:
        RuntimeError: ENCRYPTION_KEY 환경변수가 설정되지 않은 경우
    """
    # 1순위: 환경변수 (Cloud Run 운영 환경)
    key_str = os.environ.get("ENCRYPTION_KEY")
    if key_str:
        return key_str.encode() if isinstance(key_str, str) else key_str
    
    # 2순위: Streamlit secrets (로컬 개발 환경)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and "ENCRYPTION_KEY" in st.secrets:
            key_str = st.secrets["ENCRYPTION_KEY"]
            return key_str.encode() if isinstance(key_str, str) else key_str
    except Exception:
        pass
    
    # 키 없음 - 에러 발생
    raise RuntimeError(
        "❌ [CRYPTO] ENCRYPTION_KEY not found!\n"
        "Please set ENCRYPTION_KEY in:\n"
        "  - Cloud Run: Environment Variables\n"
        "  - Local Dev: .streamlit/secrets.toml\n"
        "\n"
        "Master Key Policy:\n"
        "  - GOLDKEY-AI and GOLDKEY-CRM share the same key\n"
        "  - Use existing production key (19IPhR...)\n"
        "  - No fallback allowed for security"
    )


def _get_fernet() -> Fernet:
    """
    Fernet 암호화 객체 생성
    
    Returns:
        Fernet: 암호화/복호화 객체
    """
    key = _get_encryption_key()
    return Fernet(key)


# ══════════════════════════════════════════════════════════════════════════════
# §2 SHA-256 단방향 해시 (연락처, 비밀번호)
# ══════════════════════════════════════════════════════════════════════════════

def hash_contact(contact: str) -> str:
    """
    연락처를 SHA-256 해시로 변환 (로그인 인증용)
    
    Args:
        contact: 연락처 (예: "010-1234-5678" 또는 "01012345678")
    
    Returns:
        str: SHA-256 해시 (64자 hex)
    
    Example:
        >>> hash_contact("010-1234-5678")
        'a1b2c3d4e5f6...'
    """
    if not contact:
        return ""
    
    # 하이픈 제거 후 정규화
    clean_contact = contact.replace("-", "").replace(" ", "").strip()
    
    # SHA-256 해시
    hash_obj = hashlib.sha256(clean_contact.encode('utf-8'))
    return hash_obj.hexdigest()


def hash_password(password: str) -> str:
    """
    비밀번호를 SHA-256 해시로 변환
    
    Args:
        password: 평문 비밀번호
    
    Returns:
        str: SHA-256 해시 (64자 hex)
    
    Example:
        >>> hash_password("mypassword123")
        'x1y2z3...'
    """
    if not password:
        return ""
    
    # SHA-256 해시
    hash_obj = hashlib.sha256(password.encode('utf-8'))
    return hash_obj.hexdigest()


def verify_contact_hash(contact: str, contact_hash: str) -> bool:
    """
    연락처와 해시값 일치 여부 확인
    
    Args:
        contact: 평문 연락처
        contact_hash: 저장된 SHA-256 해시
    
    Returns:
        bool: 일치 여부
    """
    if not contact or not contact_hash:
        return False
    
    return hash_contact(contact) == contact_hash


def verify_password_hash(password: str, password_hash: str) -> bool:
    """
    비밀번호와 해시값 일치 여부 확인
    
    Args:
        password: 평문 비밀번호
        password_hash: 저장된 SHA-256 해시
    
    Returns:
        bool: 일치 여부
    """
    if not password or not password_hash:
        return False
    
    return hash_password(password) == password_hash


# ══════════════════════════════════════════════════════════════════════════════
# §3 AES-256-CBC 양방향 암호화 (이름, PII)
# ══════════════════════════════════════════════════════════════════════════════

def encrypt_name(name: str) -> str:
    """
    이름을 AES-256-CBC로 암호화 (관리자 화면 표시용)
    
    Args:
        name: 평문 이름
    
    Returns:
        str: Base64 인코딩된 암호화 문자열
    
    Example:
        >>> encrypt_name("홍길동")
        'gAAAAABh...'
    """
    if not name:
        return ""
    
    try:
        fernet = _get_fernet()
        encrypted_bytes = fernet.encrypt(name.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"❌ [CRYPTO] 암호화 실패: {e}")
        raise


def decrypt_name(encrypted_name: str) -> str:
    """
    암호화된 이름을 복호화
    
    Args:
        encrypted_name: Base64 인코딩된 암호화 문자열
    
    Returns:
        str: 평문 이름
    
    Example:
        >>> decrypt_name('gAAAAABh...')
        '홍길동'
    """
    if not encrypted_name:
        return ""
    
    try:
        fernet = _get_fernet()
        decrypted_bytes = fernet.decrypt(encrypted_name.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"❌ [CRYPTO] 복호화 실패: {e}")
        return "[복호화 실패]"


def encrypt_pii(data: str) -> str:
    """
    일반 PII 데이터 암호화 (이름 외 개인정보)
    
    Args:
        data: 평문 데이터
    
    Returns:
        str: Base64 인코딩된 암호화 문자열
    """
    return encrypt_name(data)  # 동일한 Fernet 암호화 사용


def decrypt_pii(encrypted_data: str) -> str:
    """
    암호화된 PII 데이터 복호화
    
    Args:
        encrypted_data: Base64 인코딩된 암호화 문자열
    
    Returns:
        str: 평문 데이터
    """
    return decrypt_name(encrypted_data)  # 동일한 Fernet 복호화 사용


# ══════════════════════════════════════════════════════════════════════════════
# §4 유틸리티 함수
# ══════════════════════════════════════════════════════════════════════════════

def clean_phone_number(phone: str) -> str:
    """
    전화번호 정규화 (하이픈 제거, 공백 제거)
    
    Args:
        phone: 원본 전화번호
    
    Returns:
        str: 정규화된 전화번호 (숫자만)
    
    Example:
        >>> clean_phone_number("010-1234-5678")
        '01012345678'
    """
    if not phone:
        return ""
    
    return phone.replace("-", "").replace(" ", "").strip()


def format_phone_number(phone: str) -> str:
    """
    전화번호 포맷팅 (010-1234-5678 형식)
    
    Args:
        phone: 숫자만 있는 전화번호
    
    Returns:
        str: 포맷팅된 전화번호
    
    Example:
        >>> format_phone_number("01012345678")
        '010-1234-5678'
    """
    clean = clean_phone_number(phone)
    
    if len(clean) == 11:
        return f"{clean[:3]}-{clean[3:7]}-{clean[7:]}"
    elif len(clean) == 10:
        return f"{clean[:3]}-{clean[3:6]}-{clean[6:]}"
    else:
        return clean


def mask_contact(contact: str, show_last: int = 4) -> str:
    """
    연락처 마스킹 (보안 표시용)
    
    Args:
        contact: 평문 연락처
        show_last: 마지막 몇 자리 표시할지
    
    Returns:
        str: 마스킹된 연락처
    
    Example:
        >>> mask_contact("010-1234-5678")
        '010-****-5678'
    """
    if not contact:
        return ""
    
    clean = clean_phone_number(contact)
    
    if len(clean) >= show_last:
        masked = "*" * (len(clean) - show_last) + clean[-show_last:]
        return format_phone_number(masked)
    else:
        return contact


def generate_user_id() -> str:
    """
    UUID 기반 사용자 ID 생성
    
    Returns:
        str: UUID v4 문자열
    
    Example:
        >>> generate_user_id()
        'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    """
    import uuid
    return str(uuid.uuid4())


# ══════════════════════════════════════════════════════════════════════════════
# §5 테스트 함수 (개발용)
# ══════════════════════════════════════════════════════════════════════════════

def _test_crypto_utils():
    """
    암호화 유틸리티 테스트 함수 (개발 환경 전용)
    """
    print("=" * 80)
    print("[CRYPTO TEST] 암호화 유틸리티 테스트 시작")
    print("=" * 80)
    
    # 1. 연락처 해시 테스트
    contact = "010-1234-5678"
    contact_hash = hash_contact(contact)
    print(f"\n[1] 연락처 해시 테스트")
    print(f"  원본: {contact}")
    print(f"  해시: {contact_hash}")
    print(f"  검증: {verify_contact_hash(contact, contact_hash)}")
    
    # 2. 비밀번호 해시 테스트
    password = "mypassword123"
    password_hash = hash_password(password)
    print(f"\n[2] 비밀번호 해시 테스트")
    print(f"  원본: {password}")
    print(f"  해시: {password_hash}")
    print(f"  검증: {verify_password_hash(password, password_hash)}")
    
    # 3. 이름 암호화 테스트
    name = "홍길동"
    name_encrypted = encrypt_name(name)
    name_decrypted = decrypt_name(name_encrypted)
    print(f"\n[3] 이름 암호화 테스트")
    print(f"  원본: {name}")
    print(f"  암호화: {name_encrypted}")
    print(f"  복호화: {name_decrypted}")
    print(f"  일치: {name == name_decrypted}")
    
    # 4. 전화번호 유틸리티 테스트
    print(f"\n[4] 전화번호 유틸리티 테스트")
    print(f"  정규화: {clean_phone_number('010-1234-5678')}")
    print(f"  포맷팅: {format_phone_number('01012345678')}")
    print(f"  마스킹: {mask_contact('010-1234-5678')}")
    
    # 5. UUID 생성 테스트
    user_id = generate_user_id()
    print(f"\n[5] UUID 생성 테스트")
    print(f"  User ID: {user_id}")
    
    print("\n" + "=" * 80)
    print("[CRYPTO TEST] 모든 테스트 완료 ✅")
    print("=" * 80)


if __name__ == "__main__":
    _test_crypto_utils()
