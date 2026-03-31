# -*- coding: utf-8 -*-
"""
GCS 동기화 서비스
source_docs 폴더의 새로운 PDF를 GCS goldkey-knowledge-base 버킷으로 자동 업로드

작성일: 2026-03-31
목적: 로컬 문서를 클라우드 환경으로 자동 동기화 및 RAG 벡터화 트리거
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib
import json

# Google Cloud Storage
try:
    from google.cloud import storage
except ImportError:
    print("❌ google-cloud-storage 라이브러리가 설치되어 있지 않습니다.")
    print("pip install google-cloud-storage 를 실행하세요.")
    raise


class GCSSyncService:
    """
    GCS 동기화 서비스
    
    핵심 기능:
    1. source_docs 폴더 모니터링
    2. 새로운 PDF 자동 감지
    3. GCS goldkey-knowledge-base 버킷으로 업로드
    4. 업로드 이력 관리 (중복 방지)
    """
    
    # GCS 버킷 이름
    BUCKET_NAME = "goldkey-knowledge-base"
    
    # 업로드 이력 파일
    UPLOAD_HISTORY_FILE = "gcs_upload_history.json"
    
    def __init__(
        self,
        source_docs_path: Optional[str] = None,
        bucket_name: Optional[str] = None,
        credentials_path: Optional[str] = None
    ):
        """
        Args:
            source_docs_path: source_docs 폴더 경로
            bucket_name: GCS 버킷 이름 (기본값: goldkey-knowledge-base)
            credentials_path: GCS 인증 파일 경로 (기본값: 환경 변수)
        """
        # source_docs 경로 설정
        if source_docs_path is None:
            project_root = Path(__file__).parent.parent.parent
            self.source_docs_path = project_root / "hq_backend" / "knowledge_base" / "source_docs"
        else:
            self.source_docs_path = Path(source_docs_path)
        
        # GCS 버킷 이름
        self.bucket_name = bucket_name or self.BUCKET_NAME
        
        # GCS 클라이언트 초기화
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        try:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.bucket_name)
        except Exception as e:
            raise Exception(f"GCS 클라이언트 초기화 실패: {e}")
        
        # 업로드 이력 파일 경로
        self.history_file_path = self.source_docs_path.parent / self.UPLOAD_HISTORY_FILE
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        파일의 SHA256 해시 계산 (중복 감지용)
        
        Args:
            file_path: 파일 경로
        
        Returns:
            str: SHA256 해시
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def load_upload_history(self) -> Dict[str, Dict]:
        """
        업로드 이력 로드
        
        Returns:
            Dict[str, Dict]: {파일 경로: {hash, upload_time, gcs_path}}
        """
        if not self.history_file_path.exists():
            return {}
        
        try:
            with open(self.history_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 업로드 이력 로드 실패: {e}")
            return {}
    
    def save_upload_history(self, history: Dict[str, Dict]):
        """
        업로드 이력 저장
        
        Args:
            history: 업로드 이력
        """
        try:
            with open(self.history_file_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 업로드 이력 저장 실패: {e}")
    
    def get_gcs_path(self, local_path: Path) -> str:
        """
        로컬 경로를 GCS 경로로 변환
        
        Args:
            local_path: 로컬 파일 경로
        
        Returns:
            str: GCS 경로 (예: 2026/03/삼성생명_2026년03월_상품카탈로그.pdf)
        """
        # source_docs 기준 상대 경로
        relative_path = local_path.relative_to(self.source_docs_path)
        
        # GCS 경로 (슬래시로 구분)
        gcs_path = str(relative_path).replace("\\", "/")
        
        return gcs_path
    
    def upload_file_to_gcs(
        self,
        local_path: Path,
        gcs_path: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        파일을 GCS에 업로드
        
        Args:
            local_path: 로컬 파일 경로
            gcs_path: GCS 경로 (기본값: 자동 생성)
            metadata: 추가 메타데이터
        
        Returns:
            Tuple[bool, str]: (성공 여부, GCS 경로 또는 에러 메시지)
        """
        if not local_path.exists():
            return False, f"파일을 찾을 수 없습니다: {local_path}"
        
        # GCS 경로 생성
        if gcs_path is None:
            gcs_path = self.get_gcs_path(local_path)
        
        try:
            # GCS Blob 생성
            blob = self.bucket.blob(gcs_path)
            
            # 메타데이터 설정
            if metadata:
                blob.metadata = metadata
            
            # 파일 업로드
            blob.upload_from_filename(str(local_path))
            
            return True, gcs_path
        
        except Exception as e:
            return False, f"업로드 실패: {e}"
    
    def scan_and_upload_new_files(
        self,
        file_pattern: str = "*.pdf",
        force_upload: bool = False
    ) -> Dict[str, List[str]]:
        """
        새로운 파일 스캔 및 업로드
        
        Args:
            file_pattern: 파일 패턴 (기본값: *.pdf)
            force_upload: 강제 업로드 (이력 무시)
        
        Returns:
            Dict[str, List[str]]: {"uploaded": [...], "skipped": [...], "failed": [...]}
        """
        print("\n" + "=" * 70)
        print("📤 GCS 동기화 시작")
        print("=" * 70)
        
        # 업로드 이력 로드
        history = self.load_upload_history()
        
        # 결과 저장
        results = {
            "uploaded": [],
            "skipped": [],
            "failed": []
        }
        
        # source_docs 폴더 스캔
        pdf_files = list(self.source_docs_path.rglob(file_pattern))
        
        print(f"\n📊 총 {len(pdf_files)}개 파일 발견")
        
        for pdf_file in pdf_files:
            file_key = str(pdf_file.relative_to(self.source_docs_path))
            
            # 파일 해시 계산
            file_hash = self.calculate_file_hash(pdf_file)
            
            # 이력 확인 (중복 방지)
            if not force_upload and file_key in history:
                if history[file_key].get("hash") == file_hash:
                    print(f"⏭️  건너뜀 (이미 업로드됨): {pdf_file.name}")
                    results["skipped"].append(file_key)
                    continue
            
            # GCS 업로드
            print(f"📤 업로드 중: {pdf_file.name}")
            
            # 메타데이터 생성
            metadata = {
                "source": "local_source_docs",
                "upload_time": datetime.now().isoformat(),
                "file_hash": file_hash,
                "file_size": str(pdf_file.stat().st_size)
            }
            
            success, gcs_path_or_error = self.upload_file_to_gcs(
                pdf_file,
                metadata=metadata
            )
            
            if success:
                gcs_path = gcs_path_or_error
                print(f"✅ 업로드 완료: {gcs_path}")
                
                # 이력 업데이트
                history[file_key] = {
                    "hash": file_hash,
                    "upload_time": datetime.now().isoformat(),
                    "gcs_path": gcs_path
                }
                
                results["uploaded"].append(file_key)
            else:
                error_msg = gcs_path_or_error
                print(f"❌ 업로드 실패: {pdf_file.name} - {error_msg}")
                results["failed"].append(file_key)
        
        # 이력 저장
        self.save_upload_history(history)
        
        # 결과 요약
        print("\n" + "=" * 70)
        print("📊 동기화 결과")
        print("=" * 70)
        print(f"✅ 업로드: {len(results['uploaded'])}개")
        print(f"⏭️  건너뜀: {len(results['skipped'])}개")
        print(f"❌ 실패: {len(results['failed'])}개")
        
        return results
    
    def list_gcs_files(self, prefix: Optional[str] = None) -> List[str]:
        """
        GCS 버킷의 파일 목록 조회
        
        Args:
            prefix: 경로 접두사 (예: "2026/03/")
        
        Returns:
            List[str]: 파일 경로 리스트
        """
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
    
    def delete_gcs_file(self, gcs_path: str) -> bool:
        """
        GCS 파일 삭제
        
        Args:
            gcs_path: GCS 파일 경로
        
        Returns:
            bool: 성공 여부
        """
        try:
            blob = self.bucket.blob(gcs_path)
            blob.delete()
            return True
        except Exception as e:
            print(f"❌ 삭제 실패: {gcs_path} - {e}")
            return False


def main():
    """
    메인 함수 - 테스트 및 수동 실행
    """
    print("=" * 70)
    print("📤 GCS 동기화 서비스")
    print("=" * 70)
    
    try:
        # GCS 동기화 서비스 초기화
        sync_service = GCSSyncService()
        
        print(f"\n📂 source_docs 경로: {sync_service.source_docs_path}")
        print(f"☁️  GCS 버킷: {sync_service.bucket_name}")
        
        # 새로운 파일 스캔 및 업로드
        results = sync_service.scan_and_upload_new_files()
        
        # GCS 파일 목록 조회
        print("\n" + "=" * 70)
        print("☁️  GCS 버킷 파일 목록 (최근 10개)")
        print("=" * 70)
        
        gcs_files = sync_service.list_gcs_files()
        for gcs_file in gcs_files[:10]:
            print(f"  - {gcs_file}")
        
        if len(gcs_files) > 10:
            print(f"  ... 외 {len(gcs_files) - 10}개")
        
        print("\n" + "=" * 70)
        print("✅ 동기화 완료")
        print("=" * 70)
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
