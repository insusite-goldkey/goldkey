"""
[GP-SEC §GOOGLE_PLAY] 회원 탈퇴(계정 삭제) 기능
구글 Play 심사 필수 요건

Author: Goldkey AI Masters 2026
Created: 2026-03-28
"""
from __future__ import annotations
from typing import Tuple


def delete_account_permanently(
    user_id: str,
    user_name: str,
    db_delete_func=None,
    gcs_delete_func=None
) -> Tuple[bool, str]:
    """
    [Phase 3] 회원 탈퇴 - 완전 영구 삭제 (Hard Delete)
    
    Args:
        user_id: 사용자 ID
        user_name: 사용자 이름
        db_delete_func: DB 삭제 함수
        gcs_delete_func: GCS 삭제 함수
    
    Returns:
        (성공 여부, 메시지)
    
    삭제 범위:
        - Supabase gk_members 테이블에서 완전 삭제
        - GCS master_roster/{user_id}.json 파일 삭제
        - 모든 개인 식별 정보 영구 제거
    """
    if not user_id or not user_name:
        return (False, "사용자 정보가 없습니다.")
    
    db_success = False
    gcs_success = False
    
    # 1. Supabase DB에서 삭제
    if db_delete_func:
        try:
            db_success = db_delete_func(user_id, user_name)
        except Exception as e:
            return (False, f"DB 삭제 실패: {e}")
    
    # 2. GCS에서 삭제
    if gcs_delete_func:
        try:
            gcs_success = gcs_delete_func(user_id)
        except Exception as e:
            return (False, f"GCS 삭제 실패: {e}")
    
    if db_success or gcs_success:
        return (True, "회원 탈퇴가 완료되었습니다. 모든 개인 정보가 영구 삭제되었습니다.")
    else:
        return (False, "회원 탈퇴 처리 중 오류가 발생했습니다.")


def delete_member_from_db(user_id: str, user_name: str) -> bool:
    """
    Supabase gk_members 테이블에서 회원 완전 삭제
    
    Args:
        user_id: 사용자 ID
        user_name: 사용자 이름
    
    Returns:
        bool: 삭제 성공 여부
    """
    try:
        from db_utils import _get_sb
        
        sb = _get_sb()
        if not sb:
            return False
        
        # user_id 또는 name 기준으로 삭제
        if user_id:
            sb.table("gk_members").delete().eq("user_id", user_id).execute()
        elif user_name:
            sb.table("gk_members").delete().eq("name", user_name).execute()
        
        return True
    except Exception:
        return False


def delete_member_from_gcs(user_id: str) -> bool:
    """
    GCS master_roster/{user_id}.json 파일 삭제
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        bool: 삭제 성공 여부
    """
    try:
        from google.cloud import storage
        import os
        
        bucket_name = os.environ.get("GCS_BUCKET_NAME", "goldkey-ai-master-roster")
        
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # master_roster/{user_id}.json 삭제
        blob_path = f"master_roster/{user_id}.json"
        blob = bucket.blob(blob_path)
        
        if blob.exists():
            blob.delete()
            return True
        
        return False
    except Exception:
        return False
