# -*- coding: utf-8 -*-
"""
문서 해시 검증 서비스
SHA-256 해시를 사용한 중복 문서 방지

작성일: 2026-03-31
목적: 동일한 리플릿이 중복 임베딩되지 않도록 Supabase 연동
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ supabase 라이브러리가 설치되어 있지 않습니다.")
    raise


class DocumentHashValidator:
    """
    문서 해시 검증 서비스
    
    핵심 기능:
    1. PDF 파일의 SHA-256 해시 계산
    2. Supabase document_hashes 테이블과 비교
    3. 중복 문서 자동 감지 및 차단
    """
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        """
        Args:
            supabase_url: Supabase URL
            supabase_key: Supabase Service Key
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL 또는 SUPABASE_SERVICE_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        파일의 SHA-256 해시 계산
        
        Args:
            file_path: 파일 경로
        
        Returns:
            str: SHA-256 해시 (64자 hex)
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def check_duplicate(self, file_hash: str) -> bool:
        """
        중복 문서 확인
        
        Args:
            file_hash: SHA-256 해시
        
        Returns:
            bool: True=중복, False=신규
        """
        try:
            result = self.supabase.table("document_hashes").select("*").eq("file_hash", file_hash).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"⚠️ 중복 확인 실패: {e}")
            return False
    
    def register_document(
        self,
        file_path: str,
        file_hash: str,
        company: str,
        reference_date: str
    ) -> bool:
        """
        문서 해시 등록
        
        Args:
            file_path: 파일 경로
            file_hash: SHA-256 해시
            company: 보험사명
            reference_date: 기준연월
        
        Returns:
            bool: 등록 성공 여부
        """
        try:
            data = {
                "file_hash": file_hash,
                "file_name": Path(file_path).name,
                "file_path": str(file_path),
                "company": company,
                "reference_date": reference_date,
                "registered_at": datetime.now().isoformat()
            }
            
            self.supabase.table("document_hashes").insert(data).execute()
            return True
        
        except Exception as e:
            print(f"❌ 문서 등록 실패: {e}")
            return False
    
    def validate_and_register(
        self,
        file_path: str,
        company: str,
        reference_date: str
    ) -> Dict[str, any]:
        """
        문서 검증 및 등록 (통합 메서드)
        
        Args:
            file_path: 파일 경로
            company: 보험사명
            reference_date: 기준연월
        
        Returns:
            Dict: {"is_duplicate": bool, "file_hash": str, "message": str}
        """
        # 1. 해시 계산
        file_hash = self.calculate_file_hash(file_path)
        
        # 2. 중복 확인
        is_duplicate = self.check_duplicate(file_hash)
        
        if is_duplicate:
            return {
                "is_duplicate": True,
                "file_hash": file_hash,
                "message": f"⚠️ 중복 문서 감지: {Path(file_path).name}"
            }
        
        # 3. 신규 문서 등록
        success = self.register_document(file_path, file_hash, company, reference_date)
        
        if success:
            return {
                "is_duplicate": False,
                "file_hash": file_hash,
                "message": f"✅ 신규 문서 등록: {Path(file_path).name}"
            }
        else:
            return {
                "is_duplicate": False,
                "file_hash": file_hash,
                "message": f"❌ 문서 등록 실패: {Path(file_path).name}"
            }


def main():
    """테스트 실행"""
    print("=" * 70)
    print("🔒 문서 해시 검증 서비스")
    print("=" * 70)
    
    validator = DocumentHashValidator()
    
    print("\n💡 사용 예시:")
    print("""
from hq_backend.services.document_hash_validator import DocumentHashValidator

validator = DocumentHashValidator()

# 중복 검증 및 등록
result = validator.validate_and_register(
    file_path="삼성생명_2026년03월_리플릿.pdf",
    company="삼성생명",
    reference_date="2026-03"
)

if result["is_duplicate"]:
    print("중복 문서입니다. 임베딩을 건너뜁니다.")
else:
    print("신규 문서입니다. 임베딩을 진행합니다.")
    """)


if __name__ == "__main__":
    main()
