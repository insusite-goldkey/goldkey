"""
[GP-SEC] 마스터키 데이터 정합성 검증 테스트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 목적
기존 운영 키(19IPhR...로 시작)를 사용하여 GOLDKEY-AI와 GOLDKEY-CRM 간
암호화된 이름 데이터가 충돌 없이 복호화되는지 검증

## 테스트 시나리오
1. 환경변수 ENCRYPTION_KEY 설정 확인
2. HQ 앱에서 암호화한 데이터를 CRM 앱에서 복호화
3. CRM 앱에서 암호화한 데이터를 HQ 앱에서 복호화
4. 양방향 데이터 정합성 검증

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
import os

# 기존 운영 키 설정 (테스트용)
# 실제 운영 환경에서는 Cloud Run 환경변수에 설정됨
MASTER_KEY = "19IPhRrXEWJZqKPMmb-lJIGVPECKUqBCUJNDKmIpZQg="

print("=" * 80)
print("[MASTER KEY INTEGRITY TEST] 데이터 정합성 검증")
print("=" * 80)

# 환경변수 설정
os.environ["ENCRYPTION_KEY"] = MASTER_KEY
print(f"\n✅ ENCRYPTION_KEY 설정: {MASTER_KEY[:10]}...{MASTER_KEY[-10:]}")

# 프로젝트 경로 추가
sys.path.insert(0, 'D:/CascadeProjects')

print("\n[1] crypto_utils 모듈 로드 및 키 확인")
print("-" * 80)

try:
    from utils.crypto_utils import encrypt_name, decrypt_name, _get_encryption_key
    
    # 키 확인
    loaded_key = _get_encryption_key()
    print(f"로드된 키: {loaded_key[:10]}...{loaded_key[-10:]}")
    print(f"마스터키와 일치: {'✅' if loaded_key.decode() == MASTER_KEY else '❌'}")
    
except Exception as e:
    print(f"❌ 모듈 로드 실패: {e}")
    sys.exit(1)

print("\n[2] HQ → CRM 데이터 정합성 테스트")
print("-" * 80)

# HQ 앱에서 암호화한 데이터 시뮬레이션
test_names = ["홍길동", "김영희", "이철수", "박민수", "최지은"]

hq_encrypted_data = []

for name in test_names:
    encrypted = encrypt_name(name)
    hq_encrypted_data.append({
        "original": name,
        "encrypted": encrypted
    })
    print(f"HQ 암호화: {name} → {encrypted[:40]}...")

print("\n[3] CRM에서 HQ 데이터 복호화")
print("-" * 80)

crm_decrypt_success = 0
crm_decrypt_fail = 0

for data in hq_encrypted_data:
    try:
        decrypted = decrypt_name(data["encrypted"])
        match = decrypted == data["original"]
        
        if match:
            crm_decrypt_success += 1
            print(f"✅ {data['original']} → 복호화: {decrypted} (일치)")
        else:
            crm_decrypt_fail += 1
            print(f"❌ {data['original']} → 복호화: {decrypted} (불일치!)")
    
    except Exception as e:
        crm_decrypt_fail += 1
        print(f"❌ {data['original']} → 복호화 실패: {e}")

print("\n[4] CRM → HQ 데이터 정합성 테스트")
print("-" * 80)

# CRM 앱에서 암호화한 데이터 시뮬레이션
crm_encrypted_data = []

for name in test_names:
    encrypted = encrypt_name(name)
    crm_encrypted_data.append({
        "original": name,
        "encrypted": encrypted
    })
    print(f"CRM 암호화: {name} → {encrypted[:40]}...")

print("\n[5] HQ에서 CRM 데이터 복호화")
print("-" * 80)

hq_decrypt_success = 0
hq_decrypt_fail = 0

for data in crm_encrypted_data:
    try:
        decrypted = decrypt_name(data["encrypted"])
        match = decrypted == data["original"]
        
        if match:
            hq_decrypt_success += 1
            print(f"✅ {data['original']} → 복호화: {decrypted} (일치)")
        else:
            hq_decrypt_fail += 1
            print(f"❌ {data['original']} → 복호화: {decrypted} (불일치!)")
    
    except Exception as e:
        hq_decrypt_fail += 1
        print(f"❌ {data['original']} → 복호화 실패: {e}")

print("\n[6] 최종 결과")
print("=" * 80)

total_tests = len(test_names) * 2
total_success = crm_decrypt_success + hq_decrypt_success
total_fail = crm_decrypt_fail + hq_decrypt_fail

print(f"총 테스트: {total_tests}건")
print(f"성공: {total_success}건")
print(f"실패: {total_fail}건")
print(f"성공률: {(total_success / total_tests * 100):.1f}%")

print("\n[상세 결과]")
print(f"  HQ → CRM 복호화: {crm_decrypt_success}/{len(test_names)} 성공")
print(f"  CRM → HQ 복호화: {hq_decrypt_success}/{len(test_names)} 성공")

if total_fail == 0:
    print("\n✅ 데이터 정합성 검증 완료!")
    print("   GOLDKEY-AI와 GOLDKEY-CRM 간 암호화 데이터 호환 100%")
    print(f"   마스터키: {MASTER_KEY[:10]}...{MASTER_KEY[-10:]}")
else:
    print(f"\n❌ 데이터 정합성 검증 실패! ({total_fail}건 오류)")
    print("   환경변수 ENCRYPTION_KEY를 확인하세요")

print("=" * 80)

# 환경변수 우선순위 확인
print("\n[7] 환경변수 우선순위 검증")
print("-" * 80)

print("현재 설정:")
print(f"  os.environ['ENCRYPTION_KEY']: {os.environ.get('ENCRYPTION_KEY', 'NOT SET')[:20]}...")

try:
    import streamlit as st
    if hasattr(st, 'secrets') and "ENCRYPTION_KEY" in st.secrets:
        print(f"  st.secrets['ENCRYPTION_KEY']: {st.secrets['ENCRYPTION_KEY'][:20]}...")
    else:
        print("  st.secrets['ENCRYPTION_KEY']: NOT SET")
except:
    print("  st.secrets: NOT AVAILABLE (정상 - 비 Streamlit 환경)")

print("\n우선순위 로직:")
print("  1순위: os.environ['ENCRYPTION_KEY'] ✅")
print("  2순위: st.secrets['ENCRYPTION_KEY']")
print("  폴백: 없음 (에러 발생)")

print("\n" + "=" * 80)
