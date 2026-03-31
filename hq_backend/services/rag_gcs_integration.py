# -*- coding: utf-8 -*-
"""
RAG-GCS 통합 서비스
source_docs 원본 파일을 GCS에 저장하고 임베딩 데이터는 Supabase에 저장

작성일: 2026-03-31
목적: 4대 인프라 완전 통합 (RAG + Supabase + GCS + Cloud Run)
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

try:
    from google.cloud import storage
    _GCS_OK = True
except ImportError:
    _GCS_OK = False
    print("[WARNING] Google Cloud Storage 미설치. pip install google-cloud-storage 실행 필요")

try:
    from cryptography.fernet import Fernet
    _CRYPTO_OK = True
except ImportError:
    _CRYPTO_OK = False
    print("[WARNING] cryptography 미설치. pip install cryptography 실행 필요")


# ═══════════════════════════════════════════════════════════════════
# GCS 설정
# ═══════════════════════════════════════════════════════════════════

_GCS_BUCKET_NAME = "goldkey-knowledge-base"
_GCS_PATH_PREFIX = "source_docs"

def get_encryption_key() -> bytes:
    """암호화 키 로드 (환경변수)"""
    key_str = os.getenv("ENCRYPTION_KEY")
    if not key_str:
        raise ValueError("ENCRYPTION_KEY 환경변수가 설정되지 않았습니다")
    return key_str.encode()


# ═══════════════════════════════════════════════════════════════════
# GCS 업로드 함수
# ═══════════════════════════════════════════════════════════════════

def upload_source_doc_to_gcs(
    file_path: Path,
    file_hash: str,
    category: str = "general",
    encrypt: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    source_docs 원본 파일을 GCS에 업로드
    
    Args:
        file_path: 로컬 파일 경로
        file_hash: SHA-256 해시값 (파일명 대신 사용)
        category: 카테고리 (traffic_accident, fire_insurance 등)
        encrypt: 암호화 여부 (기본: True)
    
    Returns:
        (성공 여부, GCS 경로)
    """
    if not _GCS_OK:
        return False, "Google Cloud Storage 라이브러리 미설치"
    
    if not _CRYPTO_OK and encrypt:
        return False, "cryptography 라이브러리 미설치"
    
    try:
        # GCS 클라이언트 초기화
        gcs_client = storage.Client()
        bucket = gcs_client.bucket(_GCS_BUCKET_NAME)
        
        # 파일 확장자
        file_ext = file_path.suffix
        
        # GCS 경로: source_docs/{category}/{hash}{ext}
        gcs_path = f"{_GCS_PATH_PREFIX}/{category}/{file_hash}{file_ext}"
        
        # 파일 읽기
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # 암호화 (선택)
        if encrypt:
            encryption_key = get_encryption_key()
            fernet = Fernet(encryption_key)
            file_data = fernet.encrypt(file_data)
            gcs_path += ".enc"  # 암호화 파일 표시
        
        # GCS 업로드
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(
            file_data,
            content_type="application/octet-stream"
        )
        
        # 메타데이터 설정
        blob.metadata = {
            "file_hash": file_hash,
            "original_name": file_path.name,
            "category": category,
            "uploaded_at": datetime.now().isoformat(),
            "encrypted": str(encrypt)
        }
        blob.patch()
        
        full_gcs_path = f"gs://{_GCS_BUCKET_NAME}/{gcs_path}"
        return True, full_gcs_path
        
    except Exception as e:
        return False, f"GCS 업로드 실패: {str(e)}"


def download_source_doc_from_gcs(
    file_hash: str,
    category: str = "general",
    file_ext: str = ".pdf",
    decrypt: bool = True
) -> Tuple[bool, Optional[bytes]]:
    """
    GCS에서 원본 파일 다운로드
    
    Args:
        file_hash: SHA-256 해시값
        category: 카테고리
        file_ext: 파일 확장자
        decrypt: 복호화 여부
    
    Returns:
        (성공 여부, 파일 데이터)
    """
    if not _GCS_OK:
        return False, None
    
    try:
        # GCS 클라이언트 초기화
        gcs_client = storage.Client()
        bucket = gcs_client.bucket(_GCS_BUCKET_NAME)
        
        # GCS 경로
        gcs_path = f"{_GCS_PATH_PREFIX}/{category}/{file_hash}{file_ext}"
        if decrypt:
            gcs_path += ".enc"
        
        # 다운로드
        blob = bucket.blob(gcs_path)
        if not blob.exists():
            return False, None
        
        file_data = blob.download_as_bytes()
        
        # 복호화 (선택)
        if decrypt and _CRYPTO_OK:
            encryption_key = get_encryption_key()
            fernet = Fernet(encryption_key)
            file_data = fernet.decrypt(file_data)
        
        return True, file_data
        
    except Exception as e:
        print(f"GCS 다운로드 실패: {e}")
        return False, None


def check_file_exists_in_gcs(
    file_hash: str,
    category: str = "general",
    file_ext: str = ".pdf"
) -> bool:
    """
    GCS에 파일이 존재하는지 확인
    
    Args:
        file_hash: SHA-256 해시값
        category: 카테고리
        file_ext: 파일 확장자
    
    Returns:
        존재 여부
    """
    if not _GCS_OK:
        return False
    
    try:
        gcs_client = storage.Client()
        bucket = gcs_client.bucket(_GCS_BUCKET_NAME)
        
        # 암호화 파일 확인
        gcs_path = f"{_GCS_PATH_PREFIX}/{category}/{file_hash}{file_ext}.enc"
        blob = bucket.blob(gcs_path)
        
        return blob.exists()
        
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════
# 통합 워크플로우
# ═══════════════════════════════════════════════════════════════════

def integrated_rag_gcs_workflow(
    file_path: Path,
    file_hash: str,
    category: str,
    supabase_chunks: list
) -> Dict:
    """
    통합 워크플로우: 원본 파일 → GCS, 임베딩 → Supabase
    
    Args:
        file_path: 로컬 파일 경로
        file_hash: SHA-256 해시값
        category: 카테고리
        supabase_chunks: Supabase에 저장할 청크 리스트
    
    Returns:
        처리 결과
    """
    result = {
        "success": False,
        "gcs_uploaded": False,
        "gcs_path": None,
        "supabase_chunks": 0,
        "error": None
    }
    
    try:
        # [1단계] GCS에 원본 파일 업로드
        gcs_success, gcs_path = upload_source_doc_to_gcs(
            file_path=file_path,
            file_hash=file_hash,
            category=category,
            encrypt=True
        )
        
        if gcs_success:
            result["gcs_uploaded"] = True
            result["gcs_path"] = gcs_path
        else:
            result["error"] = gcs_path  # 에러 메시지
            return result
        
        # [2단계] Supabase에 임베딩 청크 저장 (호출 측에서 처리)
        result["supabase_chunks"] = len(supabase_chunks)
        result["success"] = True
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        return result


# ═══════════════════════════════════════════════════════════════════
# GCS 통계 조회
# ═══════════════════════════════════════════════════════════════════

def get_gcs_storage_stats() -> Dict:
    """
    GCS 저장소 통계 조회
    
    Returns:
        통계 딕셔너리
    """
    if not _GCS_OK:
        return {"error": "Google Cloud Storage 라이브러리 미설치"}
    
    try:
        gcs_client = storage.Client()
        bucket = gcs_client.bucket(_GCS_BUCKET_NAME)
        
        # 모든 파일 조회
        blobs = list(bucket.list_blobs(prefix=_GCS_PATH_PREFIX))
        
        # 카테고리별 통계
        categories = {}
        total_size = 0
        
        for blob in blobs:
            # 카테고리 추출
            parts = blob.name.split("/")
            if len(parts) >= 2:
                category = parts[1]
                categories[category] = categories.get(category, 0) + 1
            
            total_size += blob.size
        
        return {
            "total_files": len(blobs),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "categories": categories,
            "bucket": _GCS_BUCKET_NAME
        }
        
    except Exception as e:
        return {"error": str(e)}
