# -*- coding: utf-8 -*-
"""
문서 전처리 및 Chunking 서비스
보험 카탈로그 PDF를 의미 단위로 분할하여 RAG 시스템에 최적화

작성일: 2026-03-31
목적: 보험 상품명-보장내용-보험료 단위로 Chunk 분할 및 메타데이터 주입
"""

import os
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# LangChain Text Splitter
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    print("❌ langchain 라이브러리가 설치되어 있지 않습니다.")
    print("pip install langchain 를 실행하세요.")
    raise

# PDF 처리
try:
    import PyPDF2
except ImportError:
    print("❌ PyPDF2 라이브러리가 설치되어 있지 않습니다.")
    print("pip install PyPDF2 를 실행하세요.")
    raise

# 보안 필터 (PII 마스킹)
try:
    from hq_backend.services.security_filter import SecurityFilter
except ImportError:
    print("⚠️ security_filter 모듈을 찾을 수 없습니다. 상대 경로로 시도합니다.")
    try:
        from .security_filter import SecurityFilter
    except ImportError:
        print("❌ SecurityFilter를 import할 수 없습니다.")
        raise


class InsuranceDocumentProcessor:
    """
    보험 문서 전처리 및 Chunking 프로세서
    
    핵심 기능:
    1. PDF 텍스트 추출
    2. 보험 상품명-보장내용-보험료 단위 Chunk 분할
    3. 파일명에서 보험사명 및 기준연월 자동 추출
    4. 메타데이터 강제 주입
    """
    
    # 보험사명 매핑 (파일명 패턴 → 표준 보험사명)
    INSURANCE_COMPANY_MAPPING = {
        "삼성": "삼성생명",
        "samsung": "삼성생명",
        "한화": "한화생명",
        "hanwha": "한화생명",
        "교보": "교보생명",
        "kyobo": "교보생명",
        "kb": "KB생명",
        "KB": "KB생명",
        "신한": "신한라이프",
        "shinhan": "신한라이프",
        "메리츠": "메리츠화재",
        "meritz": "메리츠화재",
        "현대": "현대해상",
        "hyundai": "현대해상",
        "db": "DB손해보험",
        "DB": "DB손해보험",
        "흥국": "흥국화재",
        "heungkuk": "흥국화재"
    }
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,  # 15% overlap (1000 * 0.15 = 150)
        separators: Optional[List[str]] = None
    ):
        """
        Args:
            chunk_size: Chunk 크기 (기본값: 1000자)
            chunk_overlap: Chunk 간 중복 (기본값: 150자, 15%)
            separators: 구분자 리스트 (기본값: 보험 문서 최적화 구분자)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 보험 문서 최적화 구분자
        # 상품명 → 보장내용 → 보험료 순서로 분할
        if separators is None:
            self.separators = [
                "\n\n\n",  # 상품 구분
                "\n\n",    # 섹션 구분
                "\n",      # 줄 구분
                "。",      # 문장 구분 (한자)
                ".",       # 문장 구분
                " ",       # 단어 구분
                ""         # 글자 구분
            ]
        else:
            self.separators = separators
        
        # RecursiveCharacterTextSplitter 초기화
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len
        )
        
        # 보안 필터 초기화 (PII 마스킹)
        self.security_filter = SecurityFilter()
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        PDF 파일에서 텍스트 추출
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            str: 추출된 텍스트
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        text = ""
        
        try:
            with open(pdf_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n\n[페이지 {page_num}]\n{page_text}"
        
        except Exception as e:
            raise Exception(f"PDF 텍스트 추출 실패: {e}")
        
        # 보안 필터 적용 (PII 마스킹) - 절대 누락 금지
        # 개인정보 보호법 준수 및 민원 대응 정당성 유지
        raw_text = text.strip()
        security_result = self.security_filter.apply_all_filters(raw_text)
        
        # PII 감지 로그 (선택적)
        if security_result.detection_count > 0:
            print(f"🔒 보안 필터: {security_result.detection_count}개 PII 감지 및 마스킹 완료")
        
        return security_result.masked_text
    
    def extract_metadata_from_filename(self, filename: str) -> Dict[str, str]:
        """
        파일명에서 보험사명 및 기준연월 추출
        
        파일명 패턴 예시:
        - 삼성생명_2026년03월_상품카탈로그.pdf
        - KB생명_202603_catalog.pdf
        - 메리츠화재_2026-03_보험상품.pdf
        
        Args:
            filename: 파일명
        
        Returns:
            Dict[str, str]: {"company": "보험사명", "reference_date": "2026-03"}
        """
        metadata = {
            "company": "알 수 없음",
            "reference_date": None
        }
        
        # 확장자 제거
        filename_without_ext = Path(filename).stem
        
        # 1. 보험사명 추출
        for pattern, standard_name in self.INSURANCE_COMPANY_MAPPING.items():
            if pattern.lower() in filename_without_ext.lower():
                metadata["company"] = standard_name
                break
        
        # 2. 기준연월 추출
        # 패턴 1: 2026년03월, 2026년3월
        match = re.search(r'(\d{4})년\s*(\d{1,2})월', filename_without_ext)
        if match:
            year = match.group(1)
            month = match.group(2).zfill(2)
            metadata["reference_date"] = f"{year}-{month}"
            return metadata
        
        # 패턴 2: 202603, 2026-03, 2026_03
        match = re.search(r'(\d{4})[-_]?(\d{2})', filename_without_ext)
        if match:
            year = match.group(1)
            month = match.group(2)
            metadata["reference_date"] = f"{year}-{month}"
            return metadata
        
        # 패턴 3: 파일명에 날짜가 없으면 현재 연월 사용
        if metadata["reference_date"] is None:
            now = datetime.now()
            metadata["reference_date"] = f"{now.year}-{now.month:02d}"
        
        return metadata
    
    def split_document(
        self,
        text: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict[str, str]]:
        """
        문서를 Chunk로 분할
        
        Args:
            text: 분할할 텍스트
            metadata: 추가 메타데이터
        
        Returns:
            List[Dict[str, str]]: Chunk 리스트 (각 Chunk는 content와 metadata 포함)
        """
        if metadata is None:
            metadata = {}
        
        # RecursiveCharacterTextSplitter로 분할
        chunks = self.text_splitter.split_text(text)
        
        # 각 Chunk에 메타데이터 추가
        result = []
        for idx, chunk in enumerate(chunks, 1):
            chunk_data = {
                "content": chunk,
                "chunk_index": idx,
                "chunk_total": len(chunks),
                "content_length": len(chunk),
                **metadata
            }
            result.append(chunk_data)
        
        return result
    
    def process_pdf(
        self,
        pdf_path: str,
        additional_metadata: Optional[Dict] = None
    ) -> List[Dict[str, str]]:
        """
        PDF 파일 전체 처리 파이프라인
        
        Args:
            pdf_path: PDF 파일 경로
            additional_metadata: 추가 메타데이터
        
        Returns:
            List[Dict[str, str]]: 처리된 Chunk 리스트
        """
        pdf_path = Path(pdf_path)
        
        # 1. 파일명에서 메타데이터 추출
        filename_metadata = self.extract_metadata_from_filename(pdf_path.name)
        
        # 2. PDF 텍스트 추출
        text = self.extract_text_from_pdf(pdf_path)
        
        # 3. 메타데이터 병합
        metadata = {
            "document_name": pdf_path.name,
            "document_path": str(pdf_path),
            **filename_metadata
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # 4. 문서 분할
        chunks = self.split_document(text, metadata)
        
        return chunks
    
    def process_directory(
        self,
        directory_path: str,
        file_pattern: str = "*.pdf",
        additional_metadata: Optional[Dict] = None
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        디렉토리 내 모든 PDF 파일 처리
        
        Args:
            directory_path: 디렉토리 경로
            file_pattern: 파일 패턴 (기본값: *.pdf)
            additional_metadata: 추가 메타데이터
        
        Returns:
            Dict[str, List[Dict[str, str]]]: {파일명: Chunk 리스트}
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"디렉토리를 찾을 수 없습니다: {directory}")
        
        results = {}
        
        for pdf_file in directory.rglob(file_pattern):
            try:
                chunks = self.process_pdf(str(pdf_file), additional_metadata)
                results[pdf_file.name] = chunks
                print(f"✅ 처리 완료: {pdf_file.name} ({len(chunks)}개 Chunk)")
            except Exception as e:
                print(f"❌ 처리 실패: {pdf_file.name} - {e}")
                continue
        
        return results
    
    def get_statistics(self, chunks: List[Dict[str, str]]) -> Dict:
        """
        Chunk 통계 정보 반환
        
        Args:
            chunks: Chunk 리스트
        
        Returns:
            Dict: 통계 정보
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_length": 0,
                "min_chunk_length": 0,
                "max_chunk_length": 0
            }
        
        chunk_lengths = [chunk["content_length"] for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths),
            "min_chunk_length": min(chunk_lengths),
            "max_chunk_length": max(chunk_lengths)
        }


def main():
    """
    테스트 및 예제 실행
    """
    print("=" * 70)
    print("📄 보험 문서 전처리 및 Chunking 서비스")
    print("=" * 70)
    
    # 프로세서 초기화
    processor = InsuranceDocumentProcessor(
        chunk_size=1000,
        chunk_overlap=150  # 15% overlap
    )
    
    print(f"\n⚙️ 설정:")
    print(f"   Chunk 크기: {processor.chunk_size}자")
    print(f"   Chunk 중복: {processor.chunk_overlap}자 (15%)")
    
    # 파일명 메타데이터 추출 테스트
    print("\n" + "=" * 70)
    print("🧪 파일명 메타데이터 추출 테스트")
    print("=" * 70)
    
    test_filenames = [
        "삼성생명_2026년03월_상품카탈로그.pdf",
        "KB생명_202603_catalog.pdf",
        "메리츠화재_2026-03_보험상품.pdf",
        "현대해상_자동차보험_2026_03.pdf"
    ]
    
    for filename in test_filenames:
        metadata = processor.extract_metadata_from_filename(filename)
        print(f"\n📄 {filename}")
        print(f"   보험사: {metadata['company']}")
        print(f"   기준연월: {metadata['reference_date']}")
    
    print("\n" + "=" * 70)
    print("✅ 테스트 완료")
    print("=" * 70)
    
    print("\n💡 사용 예시:")
    print("""
    # PDF 파일 처리
    processor = InsuranceDocumentProcessor()
    chunks = processor.process_pdf("삼성생명_2026년03월_상품카탈로그.pdf")
    
    # 디렉토리 전체 처리
    results = processor.process_directory("hq_backend/knowledge_base/source_docs/2026/03/")
    
    # 통계 정보
    stats = processor.get_statistics(chunks)
    print(f"총 Chunk 수: {stats['total_chunks']}")
    """)


if __name__ == "__main__":
    main()
