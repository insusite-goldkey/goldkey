# -*- coding: utf-8 -*-
"""
교통사고 GCS 저장 모듈
블랙박스 영상, 분석 결과, 보고서 GCS 업로드

작성일: 2026-03-31
목적: 교통사고 데이터 안전 보관 및 암호화 저장
"""

import os
from typing import Dict, Optional
from google.cloud import storage
from cryptography.fernet import Fernet
import json
from datetime import datetime
import uuid


class TrafficAccidentGCSStorage:
    """
    교통사고 GCS 저장 관리자
    
    핵심 기능:
    1. 블랙박스 영상 GCS 업로드 (암호화)
    2. 분석 결과 JSON 저장
    3. 보고서 PDF 저장
    4. Signed URL 생성
    """
    
    def __init__(self):
        """초기화"""
        self.bucket_name = "goldkey-traffic-accidents"
        self.encryption_key = self._get_encryption_key()
        
        try:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.bucket_name)
        except Exception as e:
            print(f"GCS 클라이언트 초기화 실패: {e}")
            self.storage_client = None
            self.bucket = None
    
    def _get_encryption_key(self) -> Optional[Fernet]:
        """암호화 키 로드"""
        try:
            key = os.getenv("ENCRYPTION_KEY")
            if key:
                return Fernet(key.encode())
            return None
        except Exception:
            return None
    
    def upload_video(
        self,
        video_file,
        accident_id: str,
        agent_id: str,
        encrypt: bool = True
    ) -> Optional[str]:
        """
        블랙박스 영상 업로드
        
        Args:
            video_file: 영상 파일 객체
            accident_id: 사고 ID (UUID)
            agent_id: 설계사 ID
            encrypt: 암호화 여부
        
        Returns:
            GCS 경로
        """
        if not self.bucket:
            return None
        
        try:
            # 파일 읽기
            video_data = video_file.read()
            
            # 암호화
            if encrypt and self.encryption_key:
                video_data = self.encryption_key.encrypt(video_data)
            
            # GCS 경로 생성
            blob_path = f"videos/{agent_id}/{accident_id}.mp4.enc"
            blob = self.bucket.blob(blob_path)
            
            # 메타데이터 설정
            blob.metadata = {
                "accident_id": accident_id,
                "agent_id": agent_id,
                "uploaded_at": datetime.now().isoformat(),
                "encrypted": str(encrypt)
            }
            
            # 업로드
            blob.upload_from_string(video_data)
            
            return f"gs://{self.bucket_name}/{blob_path}"
            
        except Exception as e:
            print(f"영상 업로드 실패: {e}")
            return None
    
    def upload_analysis_result(
        self,
        analysis_result: Dict,
        accident_id: str,
        agent_id: str
    ) -> Optional[str]:
        """
        분석 결과 JSON 업로드
        
        Args:
            analysis_result: 분석 결과 딕셔너리
            accident_id: 사고 ID
            agent_id: 설계사 ID
        
        Returns:
            GCS 경로
        """
        if not self.bucket:
            return None
        
        try:
            # JSON 직렬화
            json_data = json.dumps(analysis_result, ensure_ascii=False, indent=2)
            
            # 암호화
            if self.encryption_key:
                json_data = self.encryption_key.encrypt(json_data.encode())
            else:
                json_data = json_data.encode()
            
            # GCS 경로 생성
            blob_path = f"analysis_results/{agent_id}/{accident_id}.json.enc"
            blob = self.bucket.blob(blob_path)
            
            # 메타데이터 설정
            blob.metadata = {
                "accident_id": accident_id,
                "agent_id": agent_id,
                "uploaded_at": datetime.now().isoformat(),
                "data_type": "analysis_result"
            }
            
            # 업로드
            blob.upload_from_string(json_data)
            
            return f"gs://{self.bucket_name}/{blob_path}"
            
        except Exception as e:
            print(f"분석 결과 업로드 실패: {e}")
            return None
    
    def upload_report_pdf(
        self,
        report_content: str,
        accident_id: str,
        agent_id: str
    ) -> Optional[str]:
        """
        보고서 PDF 업로드
        
        Args:
            report_content: 보고서 내용 (Markdown)
            accident_id: 사고 ID
            agent_id: 설계사 ID
        
        Returns:
            GCS 경로
        """
        if not self.bucket:
            return None
        
        try:
            # 암호화
            if self.encryption_key:
                report_data = self.encryption_key.encrypt(report_content.encode())
            else:
                report_data = report_content.encode()
            
            # GCS 경로 생성
            blob_path = f"reports/{agent_id}/{accident_id}.md.enc"
            blob = self.bucket.blob(blob_path)
            
            # 메타데이터 설정
            blob.metadata = {
                "accident_id": accident_id,
                "agent_id": agent_id,
                "uploaded_at": datetime.now().isoformat(),
                "data_type": "report"
            }
            
            # 업로드
            blob.upload_from_string(report_data)
            
            return f"gs://{self.bucket_name}/{blob_path}"
            
        except Exception as e:
            print(f"보고서 업로드 실패: {e}")
            return None
    
    def generate_signed_url(
        self,
        blob_path: str,
        expiration_minutes: int = 60
    ) -> Optional[str]:
        """
        Signed URL 생성 (다운로드용)
        
        Args:
            blob_path: GCS blob 경로
            expiration_minutes: 만료 시간 (분)
        
        Returns:
            Signed URL
        """
        if not self.bucket:
            return None
        
        try:
            blob = self.bucket.blob(blob_path)
            
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=expiration_minutes),
                method="GET"
            )
            
            return url
            
        except Exception as e:
            print(f"Signed URL 생성 실패: {e}")
            return None
    
    def download_and_decrypt(
        self,
        blob_path: str
    ) -> Optional[bytes]:
        """
        파일 다운로드 및 복호화
        
        Args:
            blob_path: GCS blob 경로
        
        Returns:
            복호화된 데이터
        """
        if not self.bucket:
            return None
        
        try:
            blob = self.bucket.blob(blob_path)
            encrypted_data = blob.download_as_bytes()
            
            # 복호화
            if self.encryption_key:
                decrypted_data = self.encryption_key.decrypt(encrypted_data)
                return decrypted_data
            
            return encrypted_data
            
        except Exception as e:
            print(f"다운로드 및 복호화 실패: {e}")
            return None


# ══════════════════════════════════════════════════════════════════════════════
# 통합 저장 함수
# ══════════════════════════════════════════════════════════════════════════════

def save_traffic_accident_to_gcs(
    video_file,
    analysis_result: Dict,
    report_content: str,
    agent_id: str
) -> Dict[str, Optional[str]]:
    """
    교통사고 데이터 일괄 GCS 저장
    
    Args:
        video_file: 블랙박스 영상 파일
        analysis_result: 분석 결과
        report_content: 보고서 내용
        agent_id: 설계사 ID
    
    Returns:
        GCS 경로 딕셔너리
    """
    storage = TrafficAccidentGCSStorage()
    accident_id = str(uuid.uuid4())
    
    paths = {
        "video_path": None,
        "analysis_path": None,
        "report_path": None,
        "accident_id": accident_id
    }
    
    # 1. 영상 업로드
    if video_file:
        paths["video_path"] = storage.upload_video(
            video_file, accident_id, agent_id
        )
    
    # 2. 분석 결과 업로드
    if analysis_result:
        paths["analysis_path"] = storage.upload_analysis_result(
            analysis_result, accident_id, agent_id
        )
    
    # 3. 보고서 업로드
    if report_content:
        paths["report_path"] = storage.upload_report_pdf(
            report_content, accident_id, agent_id
        )
    
    return paths
