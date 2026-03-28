"""
[GP-SEC §GOOGLE_PLAY] 구글 심사용 테스트 계정 자동 생성
시스템 기동 시 TestUser 계정 자동 시드(Seed)

Author: Goldkey AI Masters 2026
Created: 2026-03-28
"""
from __future__ import annotations
import hashlib
import datetime


def seed_test_account_if_needed(db_get_func=None, db_upsert_func=None, gcs_dual_write_func=None) -> bool:
    """
    [Phase 1] 구글 심사용 테스트 계정 자동 생성
    
    Args:
        db_get_func: DB 조회 함수 (예: _du_get_member)
        db_upsert_func: DB 저장 함수 (예: _du_upsert_member)
        gcs_dual_write_func: GCS Dual Write 함수 (예: dual_write_member)
    
    Returns:
        bool: True (생성됨), False (이미 존재)
    
    테스트 계정 정보:
        - 이름: TestUser
        - 연락처: 010-0000-0000
        - PIN: 123456 (SHA-256 해시)
        - 역할: agent
    """
    if not db_get_func:
        return False
    
    # 1. TestUser 계정 존재 여부 확인
    try:
        existing = db_get_func("TestUser")
        if existing:
            # 이미 존재함
            return False
    except Exception:
        pass
    
    # 2. TestUser 계정 생성
    try:
        from utils.crypto_utils import encrypt_name, generate_user_id
        
        # PIN 해시 생성 (123456)
        test_pin = "123456"
        test_pin_hash = hashlib.sha256(test_pin.encode()).hexdigest()
        
        # 연락처 해시 생성 (010-0000-0000)
        test_contact = "01000000000"
        test_contact_hash = hashlib.sha256(test_contact.encode()).hexdigest()
        
        # 테스트 계정 데이터
        test_account = {
            "user_id": generate_user_id(),
            "name": "TestUser",
            "name_encrypted": encrypt_name("TestUser"),
            "contact": test_contact_hash,
            "pin_hash": test_pin_hash,
            "job": "구글 심사용 테스트 계정",
            "user_role": "agent",
            "role": "agent",
            "quota_remaining": 100,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
        }
        
        # 3. Dual Write (Supabase + GCS)
        if gcs_dual_write_func and db_upsert_func:
            gcs_dual_write_func(test_account, db_save_func=db_upsert_func)
        elif db_upsert_func:
            db_upsert_func(test_account)
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 계정 생성 실패: {e}")
        return False
