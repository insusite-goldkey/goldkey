"""
[GP-SEC-GCS] GCS 마스터 명부 동기화 모듈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 보안 원칙 (GP-SEC-GCS 준수)
1. 애플리케이션 계층 양방향 암호화: GCS 업로드 전 Fernet(AES-128-CBC) 암호화 필수
2. 퍼블릭 액세스 전면 차단: allUsers 권한 부여 절대 금지
3. 식별자 분리 보관: 파일명/경로에 PII 절대 포함 금지

## GCS 버킷 구조
```
gs://goldkey-admin/
  └── members/
      ├── {user_id}.json  (암호화된 회원 정보)
      ├── {user_id}.json
      └── ...
```

## 파일 구조 (암호화 전 JSON)
```json
{
  "user_id": "uuid-v4",
  "name_encrypted": "AES-256 암호화된 이름",
  "contact_hash": "SHA-256 해시",
  "password_hash": "SHA-256 해시",
  "device_fingerprint": "브라우저 핑거프린트",
  "role": "member" | "admin",
  "quota_remaining": 10,
  "created_at": "2026-03-27T20:00:00",
  "updated_at": "2026-03-27T20:00:00"
}
```

## 사용 예시
```python
from utils.gcs_master_sync import save_member_to_gcs, load_member_from_gcs

# 회원 정보 저장 (DB + GCS 동시)
member_data = {
    "user_id": "abc-123",
    "name_encrypted": "...",
    "contact_hash": "...",
    ...
}
save_member_to_gcs(member_data)

# 회원 정보 로드
member = load_member_from_gcs("abc-123")
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from google.cloud import storage
from cryptography.fernet import Fernet


# ══════════════════════════════════════════════════════════════════════════════
# §1 GCS 클라이언트 및 설정
# ══════════════════════════════════════════════════════════════════════════════

# GCS 버킷 이름
GCS_BUCKET_NAME = "goldkey-admin"
GCS_MEMBERS_PREFIX = "members/"

# GCS 클라이언트 (싱글턴)
_GCS_CLIENT: Optional[storage.Client] = None


def _get_gcs_client() -> storage.Client:
    """
    GCS 클라이언트 획득 (싱글턴 패턴)
    
    Returns:
        storage.Client: GCS 클라이언트
    
    Raises:
        Exception: GCS 인증 실패 시
    """
    global _GCS_CLIENT
    
    if _GCS_CLIENT is not None:
        return _GCS_CLIENT
    
    try:
        # 환경변수에서 서비스 계정 키 경로 확인
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        if credentials_path and os.path.exists(credentials_path):
            _GCS_CLIENT = storage.Client.from_service_account_json(credentials_path)
        else:
            # Cloud Run 환경에서는 자동 인증
            _GCS_CLIENT = storage.Client()
        
        return _GCS_CLIENT
    
    except Exception as e:
        print(f"❌ [GCS] 클라이언트 초기화 실패: {e}")
        raise


def _get_gcs_encryption_key() -> bytes:
    """
    GCS 파일 암호화 키 획득
    
    [GP-SEC] 마스터키 정책:
    - GCS 암호화도 동일한 ENCRYPTION_KEY 사용 (crypto_utils와 공유)
    - GOLDKEY-AI와 GOLDKEY-CRM 간 데이터 정합성 보장
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
        "❌ [GCS] ENCRYPTION_KEY not found!\n"
        "GCS encryption uses the same master key as crypto_utils.\n"
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
# §2 GCS 파일 암호화/복호화
# ══════════════════════════════════════════════════════════════════════════════

def _encrypt_json(data: Dict[str, Any]) -> bytes:
    """
    JSON 데이터를 암호화
    
    Args:
        data: 암호화할 딕셔너리
    
    Returns:
        bytes: 암호화된 바이트
    """
    try:
        fernet = _get_fernet()
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        json_bytes = json_str.encode('utf-8')
        encrypted_bytes = fernet.encrypt(json_bytes)
        return encrypted_bytes
    except Exception as e:
        print(f"❌ [GCS] JSON 암호화 실패: {e}")
        raise


def _decrypt_json(encrypted_bytes: bytes) -> Dict[str, Any]:
    """
    암호화된 바이트를 JSON으로 복호화
    
    Args:
        encrypted_bytes: 암호화된 바이트
    
    Returns:
        Dict[str, Any]: 복호화된 딕셔너리
    """
    try:
        fernet = _get_fernet()
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        json_str = decrypted_bytes.decode('utf-8')
        data = json.loads(json_str)
        return data
    except Exception as e:
        print(f"❌ [GCS] JSON 복호화 실패: {e}")
        raise


# ══════════════════════════════════════════════════════════════════════════════
# §3 GCS 파일 업로드/다운로드
# ══════════════════════════════════════════════════════════════════════════════

def _upload_to_gcs(blob_name: str, encrypted_data: bytes) -> bool:
    """
    GCS에 암호화된 데이터 업로드
    
    Args:
        blob_name: GCS 파일 경로 (예: "members/abc-123.json")
        encrypted_data: 암호화된 바이트
    
    Returns:
        bool: 성공 여부
    """
    try:
        client = _get_gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        # 암호화된 데이터 업로드
        blob.upload_from_string(
            encrypted_data,
            content_type='application/octet-stream'
        )
        
        print(f"✅ [GCS] 업로드 성공: gs://{GCS_BUCKET_NAME}/{blob_name}")
        return True
    
    except Exception as e:
        print(f"❌ [GCS] 업로드 실패: {e}")
        return False


def _download_from_gcs(blob_name: str) -> Optional[bytes]:
    """
    GCS에서 암호화된 데이터 다운로드
    
    Args:
        blob_name: GCS 파일 경로
    
    Returns:
        Optional[bytes]: 암호화된 바이트 (실패 시 None)
    """
    try:
        client = _get_gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            print(f"⚠️ [GCS] 파일 없음: gs://{GCS_BUCKET_NAME}/{blob_name}")
            return None
        
        encrypted_data = blob.download_as_bytes()
        print(f"✅ [GCS] 다운로드 성공: gs://{GCS_BUCKET_NAME}/{blob_name}")
        return encrypted_data
    
    except Exception as e:
        print(f"❌ [GCS] 다운로드 실패: {e}")
        return None


def _delete_from_gcs(blob_name: str) -> bool:
    """
    GCS에서 파일 삭제
    
    Args:
        blob_name: GCS 파일 경로
    
    Returns:
        bool: 성공 여부
    """
    try:
        client = _get_gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(blob_name)
        
        if blob.exists():
            blob.delete()
            print(f"✅ [GCS] 삭제 성공: gs://{GCS_BUCKET_NAME}/{blob_name}")
            return True
        else:
            print(f"⚠️ [GCS] 파일 없음 (삭제 스킵): gs://{GCS_BUCKET_NAME}/{blob_name}")
            return True
    
    except Exception as e:
        print(f"❌ [GCS] 삭제 실패: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §4 회원 정보 저장/로드 (Public API)
# ══════════════════════════════════════════════════════════════════════════════

def save_member_to_gcs(member_data: Dict[str, Any]) -> bool:
    """
    회원 정보를 GCS 마스터 명부에 저장
    
    Args:
        member_data: 회원 정보 딕셔너리
            - user_id (필수)
            - name_encrypted
            - contact_hash
            - password_hash
            - device_fingerprint
            - role
            - quota_remaining
            - created_at
            - updated_at
    
    Returns:
        bool: 성공 여부
    
    Example:
        >>> member = {
        ...     "user_id": "abc-123",
        ...     "name_encrypted": "...",
        ...     "contact_hash": "...",
        ...     "password_hash": "...",
        ...     "role": "member",
        ...     "quota_remaining": 10
        ... }
        >>> save_member_to_gcs(member)
        True
    """
    try:
        user_id = member_data.get("user_id")
        if not user_id:
            print("❌ [GCS] user_id 누락")
            return False
        
        # 타임스탬프 자동 추가
        if "created_at" not in member_data:
            member_data["created_at"] = datetime.now().isoformat()
        member_data["updated_at"] = datetime.now().isoformat()
        
        # JSON 암호화
        encrypted_data = _encrypt_json(member_data)
        
        # GCS 업로드
        blob_name = f"{GCS_MEMBERS_PREFIX}{user_id}.json"
        return _upload_to_gcs(blob_name, encrypted_data)
    
    except Exception as e:
        print(f"❌ [GCS] 회원 정보 저장 실패: {e}")
        return False


def load_member_from_gcs(user_id: str) -> Optional[Dict[str, Any]]:
    """
    GCS 마스터 명부에서 회원 정보 로드
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        Optional[Dict[str, Any]]: 회원 정보 (실패 시 None)
    
    Example:
        >>> member = load_member_from_gcs("abc-123")
        >>> print(member["name_encrypted"])
    """
    try:
        blob_name = f"{GCS_MEMBERS_PREFIX}{user_id}.json"
        
        # GCS 다운로드
        encrypted_data = _download_from_gcs(blob_name)
        if not encrypted_data:
            return None
        
        # JSON 복호화
        member_data = _decrypt_json(encrypted_data)
        return member_data
    
    except Exception as e:
        print(f"❌ [GCS] 회원 정보 로드 실패: {e}")
        return None


def delete_member_from_gcs(user_id: str) -> bool:
    """
    GCS 마스터 명부에서 회원 정보 삭제
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        bool: 성공 여부
    """
    try:
        blob_name = f"{GCS_MEMBERS_PREFIX}{user_id}.json"
        return _delete_from_gcs(blob_name)
    
    except Exception as e:
        print(f"❌ [GCS] 회원 정보 삭제 실패: {e}")
        return False


def list_all_members_from_gcs() -> List[Dict[str, Any]]:
    """
    GCS 마스터 명부에서 모든 회원 정보 로드
    
    Returns:
        List[Dict[str, Any]]: 회원 정보 리스트
    
    Example:
        >>> members = list_all_members_from_gcs()
        >>> print(f"총 {len(members)}명")
    """
    try:
        client = _get_gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # members/ 폴더의 모든 파일 조회
        blobs = bucket.list_blobs(prefix=GCS_MEMBERS_PREFIX)
        
        members = []
        for blob in blobs:
            # 폴더 자체는 스킵
            if blob.name.endswith('/'):
                continue
            
            try:
                encrypted_data = blob.download_as_bytes()
                member_data = _decrypt_json(encrypted_data)
                members.append(member_data)
            except Exception as e:
                print(f"⚠️ [GCS] 파일 복호화 실패 (스킵): {blob.name} - {e}")
                continue
        
        print(f"✅ [GCS] 총 {len(members)}명 회원 정보 로드 완료")
        return members
    
    except Exception as e:
        print(f"❌ [GCS] 회원 목록 조회 실패: {e}")
        return []


def verify_member_by_contact_hash(contact_hash: str) -> Optional[Dict[str, Any]]:
    """
    연락처 해시로 회원 검색 (비밀번호 재설정용)
    
    Args:
        contact_hash: SHA-256 해시된 연락처
    
    Returns:
        Optional[Dict[str, Any]]: 일치하는 회원 정보 (없으면 None)
    
    Example:
        >>> from utils.crypto_utils import hash_contact
        >>> contact_hash = hash_contact("010-1234-5678")
        >>> member = verify_member_by_contact_hash(contact_hash)
    """
    try:
        members = list_all_members_from_gcs()
        
        for member in members:
            if member.get("contact_hash") == contact_hash:
                print(f"✅ [GCS] 회원 발견: {member.get('user_id')}")
                return member
        
        print(f"⚠️ [GCS] 일치하는 회원 없음")
        return None
    
    except Exception as e:
        print(f"❌ [GCS] 회원 검색 실패: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# §5 Dual Write (DB + GCS 동시 저장)
# ══════════════════════════════════════════════════════════════════════════════

def dual_write_member(member_data: Dict[str, Any], db_save_func=None) -> bool:
    """
    DB + GCS 동시 저장 (Dual Write)
    
    Args:
        member_data: 회원 정보
        db_save_func: DB 저장 함수 (Optional, 예: db_utils.upsert_member)
    
    Returns:
        bool: 성공 여부 (둘 중 하나라도 실패 시 False)
    
    Example:
        >>> from db_utils import upsert_member
        >>> dual_write_member(member_data, upsert_member)
    """
    try:
        # 1. GCS 저장
        gcs_success = save_member_to_gcs(member_data)
        
        # 2. DB 저장 (함수 제공 시)
        db_success = True
        if db_save_func:
            try:
                db_save_func(member_data)
                print("✅ [DUAL-WRITE] DB 저장 성공")
            except Exception as e:
                print(f"❌ [DUAL-WRITE] DB 저장 실패: {e}")
                db_success = False
        
        # 3. 결과 확인
        if gcs_success and db_success:
            print("✅ [DUAL-WRITE] DB + GCS 동시 저장 성공")
            return True
        else:
            print(f"⚠️ [DUAL-WRITE] 부분 실패 - GCS: {gcs_success}, DB: {db_success}")
            return False
    
    except Exception as e:
        print(f"❌ [DUAL-WRITE] 동시 저장 실패: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# §6 테스트 함수 (개발용)
# ══════════════════════════════════════════════════════════════════════════════

def _test_gcs_sync():
    """
    GCS 동기화 테스트 함수 (개발 환경 전용)
    """
    print("=" * 80)
    print("[GCS TEST] GCS 마스터 동기화 테스트 시작")
    print("=" * 80)
    
    # 테스트 회원 데이터
    test_member = {
        "user_id": "test-user-12345",
        "name_encrypted": "gAAAAABh_test_encrypted_name",
        "contact_hash": "a1b2c3d4e5f6...",
        "password_hash": "x1y2z3...",
        "device_fingerprint": "fp-12345",
        "role": "member",
        "quota_remaining": 10
    }
    
    # 1. 저장 테스트
    print("\n[1] 회원 정보 저장 테스트")
    save_success = save_member_to_gcs(test_member)
    print(f"  결과: {'성공 ✅' if save_success else '실패 ❌'}")
    
    # 2. 로드 테스트
    print("\n[2] 회원 정보 로드 테스트")
    loaded_member = load_member_from_gcs(test_member["user_id"])
    if loaded_member:
        print(f"  User ID: {loaded_member.get('user_id')}")
        print(f"  Role: {loaded_member.get('role')}")
        print(f"  Quota: {loaded_member.get('quota_remaining')}")
    else:
        print("  실패 ❌")
    
    # 3. 목록 조회 테스트
    print("\n[3] 전체 회원 목록 조회 테스트")
    all_members = list_all_members_from_gcs()
    print(f"  총 {len(all_members)}명")
    
    # 4. 삭제 테스트
    print("\n[4] 회원 정보 삭제 테스트")
    delete_success = delete_member_from_gcs(test_member["user_id"])
    print(f"  결과: {'성공 ✅' if delete_success else '실패 ❌'}")
    
    print("\n" + "=" * 80)
    print("[GCS TEST] 모든 테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    _test_gcs_sync()
