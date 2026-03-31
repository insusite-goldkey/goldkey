# -*- coding: utf-8 -*-
"""
RAG Knowledge Base 설정 파일
폴더 구조 및 경로 관리

작성일: 2026-03-31
목적: source_docs 경로 정규화 및 YYYY/MM/ 계층 구조 관리
"""

from pathlib import Path
from typing import Optional
from datetime import datetime


class RAGConfig:
    """
    RAG Knowledge Base 설정 관리자
    """
    
    # 프로젝트 루트 경로
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    
    # Knowledge Base 기본 경로
    KNOWLEDGE_BASE_ROOT = PROJECT_ROOT / "hq_backend" / "knowledge_base"
    
    # Source Documents 경로 (정규화됨)
    SOURCE_DOCS_PATH = KNOWLEDGE_BASE_ROOT / "source_docs"
    
    # Schema 경로
    SCHEMA_PATH = KNOWLEDGE_BASE_ROOT / "schema"
    
    # Static 경로
    STATIC_PATH = KNOWLEDGE_BASE_ROOT / "static"
    
    @classmethod
    def get_current_month_path(cls) -> Path:
        """
        현재 연도/월 경로 반환
        
        Returns:
            Path: YYYY/MM/ 경로
        """
        now = datetime.now()
        return cls.SOURCE_DOCS_PATH / str(now.year) / f"{now.month:02d}"
    
    @classmethod
    def get_month_path(cls, year: int, month: int) -> Path:
        """
        특정 연도/월 경로 반환
        
        Args:
            year: 연도
            month: 월
        
        Returns:
            Path: YYYY/MM/ 경로
        """
        return cls.SOURCE_DOCS_PATH / str(year) / f"{month:02d}"
    
    @classmethod
    def ensure_paths_exist(cls):
        """
        필수 경로 생성
        """
        cls.SOURCE_DOCS_PATH.mkdir(parents=True, exist_ok=True)
        cls.SCHEMA_PATH.mkdir(parents=True, exist_ok=True)
        cls.STATIC_PATH.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_source_docs_path(cls) -> Path:
        """
        Source Documents 기본 경로 반환
        
        Returns:
            Path: source_docs 경로
        """
        return cls.SOURCE_DOCS_PATH
    
    @classmethod
    def get_all_document_files(cls, extensions: Optional[list] = None) -> list:
        """
        모든 문서 파일 경로 반환
        
        Args:
            extensions: 파일 확장자 리스트 (기본값: ['.md', '.pdf', '.txt'])
        
        Returns:
            list: 파일 경로 리스트
        """
        if extensions is None:
            extensions = ['.md', '.pdf', '.txt']
        
        files = []
        for ext in extensions:
            files.extend(cls.SOURCE_DOCS_PATH.rglob(f"*{ext}"))
        
        return files


# 설정 초기화
RAGConfig.ensure_paths_exist()


# 편의 함수
def get_source_docs_path() -> Path:
    """Source Documents 경로 반환"""
    return RAGConfig.get_source_docs_path()


def get_current_month_path() -> Path:
    """현재 연도/월 경로 반환"""
    return RAGConfig.get_current_month_path()


def get_month_path(year: int, month: int) -> Path:
    """특정 연도/월 경로 반환"""
    return RAGConfig.get_month_path(year, month)
