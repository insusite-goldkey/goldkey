"""
[GP-SEC §SSOT] 통합 인증 모듈 - Single Source of Truth
회원 조회, 중복 검사, 관리자 승격 로직 통합

Author: Goldkey AI Masters 2026
Created: 2026-03-28
"""
from __future__ import annotations
import hashlib
from typing import Optional, Dict, Any, Tuple


def get_clean_phone(phone: str) -> str:
    """연락처 정규화 (하이픈, 공백 제거)"""
    return phone.replace("-", "").replace(" ", "").strip()


def hash_pin(pin: str) -> str:
    """
    6자리 PIN 번호를 SHA-256 해시로 변환
    
    Args:
        pin: 6자리 PIN 번호 (숫자 문자열)
    
    Returns:
        str: SHA-256 해시 (64자 hex)
    
    Example:
        >>> hash_pin("123456")
        '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
    """
    if not pin:
        return ""
    return hashlib.sha256(pin.encode()).hexdigest()


def verify_pin_hash(pin: str, pin_hash: str) -> bool:
    """
    PIN 번호 해시 검증
    
    Args:
        pin: 입력된 PIN 번호 (평문)
        pin_hash: 저장된 PIN 해시값
    
    Returns:
        bool: 일치 여부
    """
    if not pin or not pin_hash:
        return False
    return hash_pin(pin) == pin_hash


def verify_member_unified(
    name: str,
    contact: str,
    db_get_func=None,
    gcs_list_func=None,
    decrypt_func=None,
    encryption_key: str = ""
) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    [SSOT] 통합 회원 조회 - 이름 + 연락처 해시 기반
    
    Args:
        name: 회원 이름
        contact: 연락처 (원문)
        db_get_func: Supabase 조회 함수 (예: _du_get_member)
        gcs_list_func: GCS 전체 목록 조회 함수
        decrypt_func: 이름 복호화 함수
        encryption_key: 암호화 키 (검증용)
    
    Returns:
        (회원 정보 dict or None, 데이터 소스 str)
        데이터 소스: "Supabase", "GCS", "NotFound"
    
    Example:
        >>> member, source = verify_member_unified("이세윤", "010-1234-5678", 
        ...                                        db_get_func=_du_get_member,
        ...                                        gcs_list_func=list_all_members_from_gcs,
        ...                                        decrypt_func=decrypt_name)
        >>> if member:
        ...     print(f"회원 발견: {source}")
    """
    _clean_contact = get_clean_phone(contact)
    _contact_hash = hashlib.sha256(_clean_contact.encode()).hexdigest()
    
    # Track 1: Supabase DB 조회 (이름 기반)
    if db_get_func:
        try:
            _db_member = db_get_func(name)
            if _db_member:
                # 연락처 해시 검증
                _db_pin = _db_member.get("pin_hash", "")
                _db_contact = _db_member.get("contact", "")
                if _db_pin == _contact_hash or _db_contact == _contact_hash:
                    return (_db_member, "Supabase")
        except Exception:
            pass
    
    # Track 2: GCS 마스터 명부 조회 (암호화 이름 복호화)
    if gcs_list_func and decrypt_func:
        try:
            # ENCRYPTION_KEY 무결성 검증
            if not encryption_key:
                import os
                encryption_key = os.environ.get("ENCRYPTION_KEY", "")
                if not encryption_key:
                    try:
                        import streamlit as st
                        encryption_key = st.secrets.get("ENCRYPTION_KEY", "")
                    except Exception:
                        pass
            
            if not encryption_key:
                raise RuntimeError("❌ ENCRYPTION_KEY not found - GCS 조회 불가")
            
            _all_gcs = gcs_list_func()
            for _gm in _all_gcs:
                try:
                    _gm_name = decrypt_func(_gm.get("name_encrypted", ""))
                    _gm_contact = _gm.get("contact", "")
                    _gm_pin = _gm.get("pin_hash", "")
                    
                    # 이름 + 연락처 해시 동시 매칭
                    if _gm_name == name and (_gm_contact == _contact_hash or _gm_pin == _contact_hash):
                        return (_gm, "GCS")
                except Exception:
                    continue
        except Exception as _gcs_err:
            # GCS 조회 실패 시 에러 로깅 (조용히 넘기지 않음)
            import streamlit as st
            st.warning(f"⚠️ [SSOT] GCS 조회 실패: {_gcs_err}")
    
    return (None, "NotFound")


def check_duplicate_member(
    name: str,
    contact: str,
    db_get_func=None,
    gcs_list_func=None,
    decrypt_func=None
) -> bool:
    """
    회원 중복 검사 (회원가입 전 필수 호출)
    
    Returns:
        True: 이미 존재하는 회원
        False: 신규 회원
    """
    member, source = verify_member_unified(
        name, contact, db_get_func, gcs_list_func, decrypt_func
    )
    return member is not None


def is_master_account(name: str, contact: str = "") -> bool:
    """
    관리자(Master) 계정 여부 확인
    
    Args:
        name: 회원 이름
        contact: 연락처 (선택)
    
    Returns:
        True: 마스터 계정
        False: 일반 회원
    """
    # 환경변수에서 마스터 이름 목록 조회
    import os
    try:
        import streamlit as st
        _master_name = st.secrets.get("MASTER_NAME", "이세윤")
    except Exception:
        _master_name = os.environ.get("MASTER_NAME", "이세윤")
    
    # 마스터 이름 목록 (쉼표 구분)
    _master_names = [n.strip() for n in _master_name.split(",")]
    
    return name.strip() in _master_names or name.lower() == "admin"


def auto_promote_to_admin(
    member: Dict[str, Any],
    session_state_setter=None
) -> bool:
    """
    관리자 자동 승격 (Smart Routing)
    
    Args:
        member: 회원 정보
        session_state_setter: 세션 상태 설정 함수 (예: st.session_state.__setitem__)
    
    Returns:
        True: 승격 성공
        False: 일반 회원
    """
    _name = member.get("name", "")
    _user_id = member.get("user_id", "")
    _role = member.get("user_role", member.get("role", ""))
    
    # 마스터 계정 확인
    if is_master_account(_name) or _role == "admin":
        if session_state_setter:
            session_state_setter("crm_is_admin", True)
            session_state_setter("crm_user_id", _user_id or "ADMIN_MASTER")
            session_state_setter("crm_user_name", _name)
            session_state_setter("crm_role", "admin")
            session_state_setter("crm_authenticated", True)
        return True
    
    return False
