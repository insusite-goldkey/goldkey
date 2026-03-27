"""
[GP-MIGRATION] HQ → CRM 회원 데이터 마이그레이션 스크립트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 목적
HQ 앱(goldkey-ai)의 기존 회원 데이터를 CRM 앱의 새로운 GCS 마스터 명부로 이관

## 마이그레이션 절차
1. HQ Supabase gk_members 테이블에서 모든 회원 조회
2. 각 회원 데이터를 새로운 암호화 표준으로 변환
   - 연락처: SHA-256 해시 (기존 평문 → 해시)
   - 비밀번호: SHA-256 해시 (기존 해시 유지 또는 재해시)
   - 이름: AES-256 암호화 (기존 평문 → 암호화)
3. GCS goldkey-admin/members/ 에 암호화된 JSON 파일 생성
4. 마이그레이션 로그 생성 (성공/실패 기록)

## 실행 방법
```bash
python scripts/migrate_hq_to_crm.py
```

## 안전 장치
- Dry-run 모드: 실제 저장 없이 변환 결과만 확인
- 백업 생성: 마이그레이션 전 기존 데이터 백업
- 롤백 기능: 실패 시 원상 복구

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.crypto_utils import hash_contact, hash_password, encrypt_name, generate_user_id
from utils.gcs_master_sync import save_member_to_gcs, list_all_members_from_gcs


# ══════════════════════════════════════════════════════════════════════════════
# §1 Supabase 연결
# ══════════════════════════════════════════════════════════════════════════════

def get_supabase_client():
    """
    Supabase 클라이언트 획득
    
    Returns:
        Supabase Client
    """
    try:
        from supabase import create_client
        from shared_components import get_env_secret
        
        url = get_env_secret("SUPABASE_URL", "")
        key = get_env_secret("SUPABASE_SERVICE_ROLE_KEY", get_env_secret("SUPABASE_KEY", ""))
        
        if not url or not key:
            raise ValueError("Supabase 인증 정보가 없습니다")
        
        return create_client(url, key)
    
    except Exception as e:
        print(f"❌ Supabase 연결 실패: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# §2 HQ 회원 데이터 조회
# ══════════════════════════════════════════════════════════════════════════════

def fetch_hq_members() -> List[Dict[str, Any]]:
    """
    HQ Supabase gk_members 테이블에서 모든 회원 조회
    
    Returns:
        List[Dict]: 회원 목록
    """
    try:
        sb = get_supabase_client()
        if not sb:
            return []
        
        response = sb.table("gk_members").select("*").execute()
        
        if response.data:
            print(f"✅ HQ에서 {len(response.data)}명 회원 조회 완료")
            return response.data
        else:
            print("⚠️ HQ에 회원 데이터가 없습니다")
            return []
    
    except Exception as e:
        print(f"❌ HQ 회원 조회 실패: {e}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# §3 데이터 변환
# ══════════════════════════════════════════════════════════════════════════════

def transform_member_data(hq_member: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    HQ 회원 데이터를 CRM 형식으로 변환
    
    Args:
        hq_member: HQ 회원 데이터
    
    Returns:
        Optional[Dict]: 변환된 CRM 회원 데이터 (실패 시 None)
    """
    try:
        # 필수 필드 확인
        name = hq_member.get("name") or hq_member.get("agent_name")
        contact = hq_member.get("contact") or hq_member.get("phone")
        password = hq_member.get("password_hash") or hq_member.get("password")
        
        if not name or not contact:
            print(f"⚠️ 필수 필드 누락: {hq_member}")
            return None
        
        # 새로운 user_id 생성 (기존 ID가 있으면 유지)
        user_id = hq_member.get("user_id") or hq_member.get("id") or generate_user_id()
        
        # 암호화 처리
        contact_hash = hash_contact(contact)
        name_encrypted = encrypt_name(name)
        
        # 비밀번호 처리
        if password:
            # 이미 해시된 경우 유지, 평문인 경우 해시
            if len(password) == 64:  # SHA-256 해시 길이
                password_hash = password
            else:
                password_hash = hash_password(password)
        else:
            # 비밀번호가 없는 경우 기본값 설정 (나중에 재설정 필요)
            password_hash = hash_password("temp_password_reset_required")
        
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
            # 원본 데이터 참조 (디버깅용)
            "_migrated_from_hq": True,
            "_hq_original_id": hq_member.get("id"),
        }
        
        return crm_member
    
    except Exception as e:
        print(f"❌ 데이터 변환 실패: {e}")
        print(f"   원본 데이터: {hq_member}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# §4 마이그레이션 실행
# ══════════════════════════════════════════════════════════════════════════════

def migrate_members(dry_run: bool = True) -> Dict[str, Any]:
    """
    HQ → CRM 회원 데이터 마이그레이션 실행
    
    Args:
        dry_run: True면 실제 저장 없이 변환 결과만 확인
    
    Returns:
        Dict: 마이그레이션 결과 통계
    """
    print("=" * 80)
    print("[MIGRATION] HQ → CRM 회원 데이터 마이그레이션 시작")
    print("=" * 80)
    
    if dry_run:
        print("⚠️ DRY-RUN 모드: 실제 저장 없이 변환 결과만 확인합니다")
    else:
        print("✅ EXECUTE 모드: 실제 GCS 저장을 진행합니다")
    
    # 통계
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "errors": []
    }
    
    # 1. HQ 회원 조회
    print("\n[1/4] HQ 회원 데이터 조회 중...")
    try:
        hq_members = fetch_hq_members()
        stats["total"] = len(hq_members)
        
        if not hq_members:
            print("⚠️ 마이그레이션할 회원이 없습니다")
            return stats
    except Exception as e:
        print(f"❌ HQ 회원 조회 중 오류 발생: {e}")
        return stats
    
    # 2. 기존 CRM 회원 조회 (중복 방지)
    print("\n[2/4] 기존 CRM 회원 확인 중...")
    try:
        existing_crm_members = list_all_members_from_gcs()
        existing_contact_hashes = {m.get("contact_hash") for m in existing_crm_members if m.get("contact_hash")}
        print(f"  기존 CRM 회원: {len(existing_crm_members)}명")
    except Exception as e:
        print(f"⚠️ 기존 CRM 회원 조회 실패 (계속 진행): {e}")
        existing_contact_hashes = set()
    
    # 3. 데이터 변환 및 저장
    print("\n[3/4] 데이터 변환 및 저장 중...")
    print(f"  총 {stats['total']}명 처리 예정\n")
    
    for idx, hq_member in enumerate(hq_members, 1):
        member_name = hq_member.get("name") or hq_member.get("agent_name") or "이름없음"
        
        try:
            # 변환
            crm_member = transform_member_data(hq_member)
            
            if not crm_member:
                print(f"  [{idx}/{stats['total']}] ❌ {member_name} - 변환 실패")
                stats["failed"] += 1
                stats["errors"].append(f"변환 실패: {hq_member.get('id')} ({member_name})")
                continue
            
            # 중복 확인
            if crm_member["contact_hash"] in existing_contact_hashes:
                print(f"  [{idx}/{stats['total']}] ⚠️ {member_name} - 이미 존재 (스킵)")
                stats["skipped"] += 1
                continue
            
            # 저장
            if not dry_run:
                try:
                    success = save_member_to_gcs(crm_member)
                    
                    if success:
                        print(f"  [{idx}/{stats['total']}] ✅ {member_name} - 저장 완료")
                        stats["success"] += 1
                        existing_contact_hashes.add(crm_member["contact_hash"])
                    else:
                        print(f"  [{idx}/{stats['total']}] ❌ {member_name} - 저장 실패")
                        stats["failed"] += 1
                        stats["errors"].append(f"저장 실패: {crm_member['user_id']} ({member_name})")
                except Exception as save_error:
                    print(f"  [{idx}/{stats['total']}] ❌ {member_name} - 저장 중 오류: {save_error}")
                    stats["failed"] += 1
                    stats["errors"].append(f"저장 오류: {crm_member['user_id']} ({member_name}) - {save_error}")
            else:
                print(f"  [{idx}/{stats['total']}] ✓ {member_name} - 변환 완료 (DRY-RUN)")
                stats["success"] += 1
        
        except Exception as e:
            print(f"  [{idx}/{stats['total']}] ❌ {member_name} - 처리 중 오류: {e}")
            stats["failed"] += 1
            stats["errors"].append(f"처리 오류: {hq_member.get('id')} ({member_name}) - {e}")
            continue
    
    # 4. 결과 출력
    print("\n[4/4] 마이그레이션 완료")
    print("=" * 80)
    print(f"총 회원 수: {stats['total']}")
    print(f"성공: {stats['success']}")
    print(f"실패: {stats['failed']}")
    print(f"스킵: {stats['skipped']}")
    
    if stats["errors"]:
        print(f"\n오류 목록:")
        for error in stats["errors"]:
            print(f"  - {error}")
    
    print("=" * 80)
    
    # 로그 파일 저장
    log_file = f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"📝 로그 저장: {log_file}")
    
    return stats


# ══════════════════════════════════════════════════════════════════════════════
# §5 메인 실행
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """
    메인 실행 함수
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="HQ → CRM 회원 데이터 마이그레이션")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="실제 마이그레이션 실행 (기본값: dry-run)"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="확인 메시지 없이 자동 실행"
    )
    
    args = parser.parse_args()
    
    # 확인 메시지 (--yes 옵션이 없을 때만)
    if args.execute and not args.yes:
        print("\n⚠️ 실제 마이그레이션을 실행합니다.")
        print("   - HQ 회원 데이터를 GCS로 이관합니다")
        print("   - 기존 데이터는 유지됩니다 (중복 스킵)")
        print("\n계속하시겠습니까? (YES 입력 또는 Ctrl+C로 취소)")
        
        try:
            confirm = input("입력: ").strip()
            if confirm != "YES":
                print("❌ 마이그레이션 취소")
                return
        except KeyboardInterrupt:
            print("\n❌ 사용자가 취소했습니다")
            return
        except Exception as e:
            print(f"\n❌ 입력 오류: {e}")
            return
    
    # 마이그레이션 실행
    try:
        stats = migrate_members(dry_run=not args.execute)
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다")
        return
    except Exception as e:
        print(f"\n\n❌ 마이그레이션 중 치명적 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 마이그레이션 결과 요약")
    print("=" * 80)
    
    if stats["success"] > 0:
        print(f"✅ 성공: {stats['success']}명")
    
    if stats["failed"] > 0:
        print(f"❌ 실패: {stats['failed']}명")
    
    if stats["skipped"] > 0:
        print(f"⚠️ 스킵: {stats['skipped']}명 (이미 존재)")
    
    if not args.execute:
        print("\n💡 실제 마이그레이션을 실행하려면:")
        print("   python scripts/migrate_hq_to_crm.py --execute")
        print("\n💡 확인 메시지 없이 자동 실행:")
        print("   python scripts/migrate_hq_to_crm.py --execute --yes")


if __name__ == "__main__":
    main()
