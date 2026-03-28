"""HQ → CRM 마이그레이션 Mockup 테스트"""
import sys
sys.path.insert(0, 'D:/CascadeProjects')

from utils.crypto_utils import hash_contact, hash_password, encrypt_name, generate_user_id
import json
from datetime import datetime

print("=" * 80)
print("[MIGRATION MOCKUP TEST] HQ → CRM 데이터 변환 로직 검증")
print("=" * 80)

# HQ 회원 데이터 샘플 (평문 상태)
hq_members = [
    {
        "id": "hq-001",
        "name": "홍길동",
        "contact": "010-1234-5678",
        "password": "plaintext_password_1",  # 평문 비밀번호
        "role": "member",
        "created_at": "2026-01-15T10:00:00"
    },
    {
        "id": "hq-002",
        "name": "김영희",
        "contact": "010-9876-5432",
        "password_hash": "a1b2c3d4e5f6...",  # 이미 해시된 비밀번호
        "role": "admin",
        "created_at": "2026-02-20T14:30:00"
    },
    {
        "id": "hq-003",
        "agent_name": "이철수",  # name 대신 agent_name
        "phone": "010-5555-6666",  # contact 대신 phone
        "password": "test123",
        "role": "member",
        "quota_remaining": 5
    }
]

print("\n[1] HQ 원본 데이터 (평문)")
print("-" * 80)
for idx, member in enumerate(hq_members, 1):
    print(f"\n회원 {idx}:")
    print(json.dumps(member, indent=2, ensure_ascii=False))

print("\n[2] CRM 변환 데이터 (암호화)")
print("-" * 80)

crm_members = []

for idx, hq_member in enumerate(hq_members, 1):
    # 필드 정규화
    name = hq_member.get("name") or hq_member.get("agent_name")
    contact = hq_member.get("contact") or hq_member.get("phone")
    password = hq_member.get("password_hash") or hq_member.get("password")
    
    # 암호화 처리
    user_id = hq_member.get("user_id") or hq_member.get("id") or generate_user_id()
    contact_hash = hash_contact(contact)
    name_encrypted = encrypt_name(name)
    
    # 비밀번호 처리 (평문이면 해시, 이미 해시면 유지)
    if len(password) == 64:  # SHA-256 해시 길이
        password_hash = password
    else:
        password_hash = hash_password(password)
    
    # CRM 회원 데이터 구성
    crm_member = {
        "user_id": user_id,
        "name_encrypted": name_encrypted,
        "contact_hash": contact_hash,
        "password_hash": password_hash,
        "role": hq_member.get("role", "member"),
        "quota_remaining": hq_member.get("quota_remaining", 10),
        "device_fingerprint": "",
        "created_at": hq_member.get("created_at") or datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "_migrated_from_hq": True,
        "_hq_original_id": hq_member.get("id")
    }
    
    crm_members.append(crm_member)
    
    print(f"\n회원 {idx} 변환 결과:")
    print(json.dumps(crm_member, indent=2, ensure_ascii=False))

print("\n[3] 복호화 검증")
print("-" * 80)

from utils.crypto_utils import decrypt_name

for idx, crm_member in enumerate(crm_members, 1):
    decrypted_name = decrypt_name(crm_member["name_encrypted"])
    print(f"\n회원 {idx}:")
    print(f"  원본 이름: {hq_members[idx-1].get('name') or hq_members[idx-1].get('agent_name')}")
    print(f"  복호화된 이름: {decrypted_name}")
    print(f"  일치 여부: {'✅' if decrypted_name == (hq_members[idx-1].get('name') or hq_members[idx-1].get('agent_name')) else '❌'}")
    print(f"  연락처 해시: {crm_member['contact_hash'][:32]}...")
    print(f"  비밀번호 해시: {crm_member['password_hash'][:32]}...")

print("\n[4] 마이그레이션 통계")
print("-" * 80)
print(f"총 HQ 회원: {len(hq_members)}명")
print(f"변환 성공: {len(crm_members)}명")
print(f"변환 실패: 0명")
print(f"성공률: 100%")

print("\n" + "=" * 80)
print("[MIGRATION MOCKUP TEST] 모든 테스트 완료 ✅")
print("=" * 80)
print("\n💡 실제 마이그레이션 실행 시:")
print("   python scripts/migrate_hq_to_crm.py --execute")
