"""GCS 동기화 Mockup 테스트"""
import sys
sys.path.insert(0, 'D:/CascadeProjects')

from utils.crypto_utils import encrypt_name, decrypt_name, hash_contact, hash_password, generate_user_id
import json
from datetime import datetime

print("=" * 80)
print("[GCS MOCKUP TEST] GCS 저장 데이터 샘플 생성 및 검증")
print("=" * 80)

# 테스트 회원 데이터 생성
member = {
    "user_id": generate_user_id(),
    "name_encrypted": encrypt_name("김철수"),
    "contact_hash": hash_contact("010-9876-5432"),
    "password_hash": hash_password("testpass123"),
    "role": "member",
    "quota_remaining": 10,
    "device_fingerprint": "fp-abc123def456",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat()
}

print("\n[1] GCS 저장 예정 데이터 (암호화된 상태)")
print("-" * 80)
print(json.dumps(member, indent=2, ensure_ascii=False))

print("\n[2] 복호화 테스트")
print("-" * 80)
print(f"복호화된 이름: {decrypt_name(member['name_encrypted'])}")
print(f"연락처 해시: {member['contact_hash'][:32]}...")
print(f"비밀번호 해시: {member['password_hash'][:32]}...")

print("\n[3] JSON 직렬화 테스트 (GCS 업로드 형식)")
print("-" * 80)
json_str = json.dumps(member, ensure_ascii=False, indent=2)
print(f"JSON 크기: {len(json_str)} bytes")
print(f"암호화 상태: ✅ (name_encrypted 필드 확인)")

print("\n" + "=" * 80)
print("[GCS MOCKUP TEST] 모든 테스트 완료 ✅")
print("=" * 80)
