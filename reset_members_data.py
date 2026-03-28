"""
[GP-SEC §PIN] 기존 회원 데이터 초기화 스크립트
6자리 PIN 인증 시스템 도입에 따른 전체 회원 데이터 삭제

실행 방법:
    python reset_members_data.py

주의사항:
    - 이 스크립트는 Supabase gk_members 테이블과 GCS master_roster/ 전체를 삭제합니다.
    - 복구 불가능하므로 실행 전 반드시 백업을 확인하세요.
    - 마스터 계정(이세윤 등)도 삭제되므로 재가입이 필요합니다.
"""
import os
import sys


def reset_supabase_members():
    """Supabase gk_members 테이블 전체 삭제"""
    try:
        from supabase import create_client, Client
        
        # Supabase 연결
        supabase_url = os.environ.get("SUPABASE_URL", "")
        supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        
        if not supabase_url or not supabase_key:
            try:
                import streamlit as st
                supabase_url = st.secrets.get("SUPABASE_URL", "")
                supabase_key = st.secrets.get("SUPABASE_SERVICE_KEY", "")
            except Exception:
                pass
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase 연결 정보가 없습니다. (SUPABASE_URL, SUPABASE_SERVICE_KEY)")
            return False
        
        sb: Client = create_client(supabase_url, supabase_key)
        
        # gk_members 테이블 전체 조회
        result = sb.table("gk_members").select("user_id, name").execute()
        members = result.data or []
        
        if not members:
            print("✅ Supabase gk_members 테이블이 이미 비어 있습니다.")
            return True
        
        print(f"📊 삭제 대상 회원: {len(members)}명")
        for m in members:
            print(f"  - {m.get('name', 'Unknown')} ({m.get('user_id', 'N/A')})")
        
        # 사용자 확인
        confirm = input("\n⚠️  위 회원 데이터를 모두 삭제하시겠습니까? (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ 취소되었습니다.")
            return False
        
        # 전체 삭제
        for m in members:
            user_id = m.get("user_id")
            if user_id:
                sb.table("gk_members").delete().eq("user_id", user_id).execute()
        
        print(f"✅ Supabase gk_members 테이블에서 {len(members)}명 삭제 완료")
        return True
        
    except Exception as e:
        print(f"❌ Supabase 삭제 실패: {e}")
        return False


def reset_gcs_members():
    """GCS master_roster/ 전체 삭제"""
    try:
        from google.cloud import storage
        
        # GCS 연결
        bucket_name = os.environ.get("GCS_BUCKET_NAME", "goldkey-ai-master-roster")
        
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # master_roster/ 경로의 모든 파일 조회
        blobs = list(bucket.list_blobs(prefix="master_roster/"))
        
        if not blobs:
            print("✅ GCS master_roster/ 폴더가 이미 비어 있습니다.")
            return True
        
        print(f"📊 삭제 대상 파일: {len(blobs)}개")
        for blob in blobs:
            print(f"  - {blob.name}")
        
        # 사용자 확인
        confirm = input("\n⚠️  위 파일을 모두 삭제하시겠습니까? (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ 취소되었습니다.")
            return False
        
        # 전체 삭제
        for blob in blobs:
            blob.delete()
        
        print(f"✅ GCS master_roster/ 폴더에서 {len(blobs)}개 파일 삭제 완료")
        return True
        
    except Exception as e:
        print(f"❌ GCS 삭제 실패: {e}")
        return False


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("[GP-SEC §PIN] 기존 회원 데이터 초기화")
    print("=" * 60)
    print()
    print("⚠️  경고: 이 스크립트는 다음 데이터를 영구 삭제합니다:")
    print("  1. Supabase gk_members 테이블 전체")
    print("  2. GCS master_roster/ 폴더 전체")
    print()
    print("📌 삭제 후 복구 불가능합니다. 반드시 백업을 확인하세요.")
    print()
    
    # 최종 확인
    final_confirm = input("계속 진행하시겠습니까? (YES 입력 필요): ")
    if final_confirm != "YES":
        print("❌ 취소되었습니다.")
        sys.exit(0)
    
    print()
    print("=" * 60)
    print("[1/2] Supabase gk_members 테이블 초기화")
    print("=" * 60)
    supabase_ok = reset_supabase_members()
    
    print()
    print("=" * 60)
    print("[2/2] GCS master_roster/ 폴더 초기화")
    print("=" * 60)
    gcs_ok = reset_gcs_members()
    
    print()
    print("=" * 60)
    print("초기화 완료")
    print("=" * 60)
    print(f"Supabase: {'✅ 성공' if supabase_ok else '❌ 실패'}")
    print(f"GCS:      {'✅ 성공' if gcs_ok else '❌ 실패'}")
    print()
    print("📌 다음 단계:")
    print("  1. CRM 앱 재배포 (deploy_crm.ps1)")
    print("  2. 새로운 6자리 PIN으로 회원가입 진행")
    print()


if __name__ == "__main__":
    main()
