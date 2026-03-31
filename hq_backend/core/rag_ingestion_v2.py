"""
[Phase 5 고도화] 지능형 증분 업데이트 RAG 임베딩 파이프라인
- 파일 중복 및 변경 감지 (Hash 기반 Skip Logic)
- 버전 및 날짜 메타데이터 자동 추출
- 카테고리 자동 분류 강화
- 상세 실행 보고서 생성

작성일: 2026-03-30
"""
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import os
import json
import hashlib
import re
from datetime import datetime

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader
    _LANGCHAIN_OK = True
except ImportError:
    _LANGCHAIN_OK = False
    print("[WARNING] LangChain 미설치. pip install langchain-text-splitters langchain-community pypdf 실행 필요")

try:
    import openai
    _OPENAI_OK = True
except ImportError:
    _OPENAI_OK = False
    print("[WARNING] OpenAI SDK 미설치. pip install openai 실행 필요")

try:
    from supabase import create_client, Client
    _SUPABASE_OK = True
except ImportError:
    _SUPABASE_OK = False
    print("[WARNING] Supabase 클라이언트 미설치. pip install supabase 실행 필요")


class IntelligentRAGPipeline:
    """지능형 증분 업데이트 RAG 파이프라인"""
    
    # 카테고리 자동 분류 규칙
    CATEGORY_RULES = {
        "법인": ["법인", "corporate", "임원", "퇴직금", "세무"],
        "배상책임": ["배상", "책임", "liability", "건물소유", "점유자"],
        "화재보험": ["화재", "fire", "특종", "공장"],
        "약관": ["약관", "terms", "조항"],
        "판례": ["판례", "판결", "court", "case"],
        "세무": ["세무", "tax", "과세", "공제"],
        "매뉴얼": ["매뉴얼", "manual", "가이드", "guide"],
    }
    
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        초기화
        
        Args:
            supabase_url: Supabase 프로젝트 URL
            supabase_key: Supabase 서비스 role 키
            openai_api_key: OpenAI API 키
            embedding_model: 임베딩 모델명 (기본: text-embedding-3-small, 1536차원)
        """
        if not _SUPABASE_OK or not _OPENAI_OK or not _LANGCHAIN_OK:
            raise ImportError(
                "필수 패키지 미설치. 다음 명령 실행:\n"
                "pip install langchain-text-splitters langchain-community pypdf openai supabase"
            )
        
        # Supabase 클라이언트
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # OpenAI 클라이언트
        openai.api_key = openai_api_key
        self.embedding_model = embedding_model
        
        # LangChain Text Splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        print("✅ 지능형 RAG 파이프라인 초기화 완료")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        파일의 SHA-256 해시 계산
        
        Args:
            file_path: 파일 경로
        
        Returns:
            SHA-256 해시 (hex 문자열)
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def extract_date_from_filename(self, filename: str) -> Optional[str]:
        """
        파일명에서 날짜 추출 (YYYYMMDD, YYYY-MM-DD, YYYY.MM.DD 등)
        
        Args:
            filename: 파일명
        
        Returns:
            날짜 문자열 (YYYY-MM-DD 형식) 또는 None
        """
        # 패턴 1: YYYYMMDD (예: 20260330)
        pattern1 = r'(\d{4})(\d{2})(\d{2})'
        match1 = re.search(pattern1, filename)
        if match1:
            year, month, day = match1.groups()
            try:
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        # 패턴 2: YYYY-MM-DD 또는 YYYY.MM.DD
        pattern2 = r'(\d{4})[-.](\d{2})[-.](\d{2})'
        match2 = re.search(pattern2, filename)
        if match2:
            year, month, day = match2.groups()
            try:
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        return None
    
    def extract_version_from_filename(self, filename: str) -> Optional[str]:
        """
        파일명에서 버전 추출 (v1.0, v2.3, ver1.0 등)
        
        Args:
            filename: 파일명
        
        Returns:
            버전 문자열 또는 None
        """
        # 패턴 1: v1.0, v2.3
        pattern1 = r'v(\d+\.\d+)'
        match1 = re.search(pattern1, filename, re.IGNORECASE)
        if match1:
            return f"v{match1.group(1)}"
        
        # 패턴 2: ver1.0, version1.0
        pattern2 = r'ver(?:sion)?(\d+\.\d+)'
        match2 = re.search(pattern2, filename, re.IGNORECASE)
        if match2:
            return f"v{match2.group(1)}"
        
        # 패턴 3: _1.0, -1.0
        pattern3 = r'[-_](\d+\.\d+)'
        match3 = re.search(pattern3, filename)
        if match3:
            return f"v{match3.group(1)}"
        
        return None
    
    def classify_category(self, filename: str, folder_path: str = "") -> str:
        """
        파일명과 폴더 경로를 분석하여 카테고리 자동 분류
        
        Args:
            filename: 파일명
            folder_path: 폴더 경로
        
        Returns:
            카테고리 문자열
        """
        text = f"{filename} {folder_path}".lower()
        
        for category, keywords in self.CATEGORY_RULES.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return category
        
        return "기타"
    
    def check_file_exists_in_db(self, file_hash: str) -> Tuple[bool, Optional[Dict]]:
        """
        파일 해시로 DB에 이미 존재하는지 확인
        
        Args:
            file_hash: 파일 SHA-256 해시
        
        Returns:
            (존재 여부, 기존 레코드 정보)
        """
        try:
            result = self.supabase.table("gk_knowledge_base") \
                .select("document_name, file_hash, file_size, created_at") \
                .eq("file_hash", file_hash) \
                .limit(1) \
                .execute()
            
            if result.data and len(result.data) > 0:
                return True, result.data[0]
            
            return False, None
        
        except Exception as e:
            print(f"⚠️ DB 조회 실패: {str(e)}")
            return False, None
    
    def load_pdf(self, pdf_path: str) -> List[Dict]:
        """
        PDF 파일 로드 및 텍스트 추출
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            페이지별 텍스트 리스트
        """
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        print(f"📄 PDF 로드 중: {pdf_path}")
        
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        documents = []
        for i, page in enumerate(pages):
            documents.append({
                "page": i + 1,
                "content": page.page_content
            })
        
        print(f"✅ PDF 로드 완료: {len(documents)}페이지")
        return documents
    
    def split_into_chunks(
        self,
        documents: List[Dict],
        document_name: str
    ) -> List[Dict]:
        """
        문서를 청크로 분할
        
        Args:
            documents: 페이지별 텍스트 리스트
            document_name: 문서명
        
        Returns:
            청크 리스트
        """
        print(f"✂️ 텍스트 청크 분할 중...")
        
        chunks = []
        chunk_index = 0
        
        for doc in documents:
            page_num = doc["page"]
            content = doc["content"]
            
            page_chunks = self.text_splitter.split_text(content)
            
            for chunk_text in page_chunks:
                clean_text = chunk_text.replace('\x00', '')
                
                chunks.append({
                    "document_name": document_name,
                    "chunk_index": chunk_index,
                    "content": clean_text,
                    "content_length": len(clean_text),
                    "source_page": page_num
                })
                chunk_index += 1
        
        print(f"✅ 청크 분할 완료: {len(chunks)}개 청크")
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 리스트를 임베딩 벡터로 변환
        
        Args:
            texts: 텍스트 리스트
        
        Returns:
            임베딩 벡터 리스트 (각 벡터는 1536차원)
        """
        print(f"🧠 임베딩 생성 중: {len(texts)}개 텍스트")
        
        try:
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            
            embeddings = [item.embedding for item in response.data]
            print(f"✅ 임베딩 생성 완료: {len(embeddings)}개 벡터")
            return embeddings
        
        except Exception as e:
            print(f"❌ 임베딩 생성 실패: {str(e)}")
            raise
    
    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """
        텍스트에서 키워드 추출 (간단한 빈도 기반)
        
        Args:
            text: 텍스트
            max_keywords: 최대 키워드 수
        
        Returns:
            키워드 리스트
        """
        words = text.split()
        word_freq = {}
        
        for word in words:
            if len(word) >= 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        return keywords
    
    def ingest_document_intelligent(
        self,
        pdf_path: str,
        document_category: Optional[str] = None,
        batch_size: int = 10,
        force_update: bool = False,
        source_root: Optional[str] = None
    ) -> Dict:
        """
        지능형 증분 업데이트 방식으로 PDF 문서 처리
        
        Args:
            pdf_path: PDF 파일 경로
            document_category: 문서 카테고리 (None이면 자동 분류)
            batch_size: 배치 크기
            force_update: True이면 중복 체크 무시하고 강제 업데이트
            source_root: 소스 루트 디렉토리 (상대 경로 계산용)
        
        Returns:
            처리 결과
        """
        print(f"\n{'='*80}")
        print(f"🚀 지능형 RAG 임베딩 파이프라인 시작")
        print(f"{'='*80}")
        print(f"문서: {pdf_path}")
        print(f"{'='*80}\n")
        
        file_path = Path(pdf_path)
        document_name = file_path.name
        
        # 폴더 경로 계산 (source_root 기준 상대 경로)
        if source_root:
            try:
                folder_path = str(file_path.parent.relative_to(Path(source_root)))
            except ValueError:
                # 상대 경로 계산 실패 시 절대 경로 사용
                folder_path = str(file_path.parent)
        else:
            folder_path = str(file_path.parent)
        
        # 1. 파일 메타데이터 추출
        print("📊 파일 메타데이터 추출 중...")
        file_hash = self.calculate_file_hash(pdf_path)
        file_size = file_path.stat().st_size
        doc_date = self.extract_date_from_filename(document_name)
        
        if not doc_date:
            # 파일 최종 수정일 사용
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            doc_date = mod_time.strftime('%Y-%m-%d')
        
        version = self.extract_version_from_filename(document_name)
        
        print(f"  파일 해시: {file_hash[:16]}...")
        print(f"  파일 크기: {file_size:,} bytes")
        print(f"  폴더 경로: {folder_path}")
        print(f"  문서 날짜: {doc_date}")
        print(f"  버전: {version or '없음'}")
        
        # 2. 카테고리 자동 분류
        if not document_category:
            document_category = self.classify_category(document_name, folder_path)
            print(f"  자동 분류 카테고리: {document_category}")
        else:
            print(f"  지정 카테고리: {document_category}")
        
        # ═══════════════════════════════════════════════════════════════════
        # [PRE-FLIGHT] 해시 기반 중복 차단 (Zero-Duplication)
        # [ABSOLUTE DIRECTIVE] OpenAI API 호출 원천 통제
        # ═══════════════════════════════════════════════════════════════════
        if not force_update:
            print("\n🔍 [PRE-FLIGHT] 중복 파일 검사 중...")
            exists, existing_record = self.check_file_exists_in_db(file_hash)
            
            if exists:
                # [SKIP] 로그 출력 의무화
                print(f"\n" + "="*80)
                print(f"⏭️  [SKIP] 중복 파일 발견 - OpenAI API 호출 원천 차단")
                print(f"="*80)
                print(f"📄 파일명: {document_name}")
                print(f"🔐 해시값: {file_hash[:32]}...")
                print(f"📅 기존 인제스트 일시: {existing_record['created_at']}")
                print(f"💰 임베딩 비용 절감 완료 (토큰 및 리소스 방어)")
                print(f"="*80 + "\n")
                
                return {
                    "success": True,
                    "status": "skipped",
                    "document_name": document_name,
                    "file_hash": file_hash,
                    "reason": "[SKIP] 중복 파일 발견 (해시값 일치) - 임베딩 생략",
                    "existing_record": existing_record,
                    "cost_saved": True  # 비용 절감 플래그
                }
        
        # 신규 문서 감지 → 임베딩 생성 시작
        print(f"\n✨ 신규 문서 감지 → OpenAI API 호출 시작")
        print(f"   파일 해시: {file_hash[:32]}... (신규)")
        
        try:
            # 4. PDF 로드
            documents = self.load_pdf(pdf_path)
            
            # 5. 청크 분할
            chunks = self.split_into_chunks(documents, document_name)
            
            # 6. 배치별 임베딩 생성 및 저장
            total_chunks = len(chunks)
            inserted_count = 0
            
            for i in range(0, total_chunks, batch_size):
                batch = chunks[i:i+batch_size]
                batch_texts = [chunk["content"] for chunk in batch]
                
                print(f"\n📦 배치 {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size} 처리 중...")
                
                # 임베딩 생성
                embeddings = self.generate_embeddings(batch_texts)
                
                # Supabase에 저장
                for chunk, embedding in zip(batch, embeddings):
                    keywords = self.extract_keywords(chunk["content"])
                    
                    record = {
                        "document_name": chunk["document_name"],
                        "document_category": document_category,
                        "chunk_index": chunk["chunk_index"],
                        "content": chunk["content"],
                        "content_length": chunk["content_length"],
                        "embedding": embedding,
                        "source_page": chunk["source_page"],
                        "keywords": keywords,
                        # 새로운 메타데이터
                        "file_hash": file_hash,
                        "file_size": file_size,
                        "doc_date": doc_date,
                        "version": version,
                        "folder_path": folder_path
                    }
                    
                    result = self.supabase.table("gk_knowledge_base").upsert(record).execute()
                    
                    if result.data:
                        inserted_count += 1
                
                print(f"✅ 배치 저장 완료: {len(batch)}개 청크")
            
            print(f"\n{'='*80}")
            print(f"✅ RAG 임베딩 파이프라인 완료")
            print(f"{'='*80}")
            print(f"총 청크: {total_chunks}개")
            print(f"저장 완료: {inserted_count}개")
            print(f"{'='*80}\n")
            
            return {
                "success": True,
                "status": "processed",
                "document_name": document_name,
                "chunks_count": inserted_count,
                "category": document_category,
                "file_hash": file_hash,
                "file_size": file_size,
                "doc_date": doc_date,
                "version": version,
                "folder_path": folder_path
            }
        
        except Exception as e:
            print(f"❌ 파이프라인 실패: {str(e)}")
            return {
                "success": False,
                "status": "failed",
                "error": str(e),
                "document_name": document_name,
                "chunks_count": 0,
                "category": document_category
            }
    
    def ingest_directory_intelligent(
        self,
        source_dir: str,
        force_update: bool = False
    ) -> Dict:
        """
        디렉토리 내 모든 PDF 파일을 지능형 방식으로 일괄 처리
        
        Args:
            source_dir: 소스 디렉토리 경로
            force_update: True이면 중복 체크 무시
        
        Returns:
            상세 실행 보고서
        """
        source_path = Path(source_dir)
        
        if not source_path.exists():
            raise FileNotFoundError(f"디렉토리를 찾을 수 없습니다: {source_dir}")
        
        # PDF 파일 목록 수집
        pdf_files = list(source_path.glob("**/*.pdf"))
        
        if not pdf_files:
            print(f"⚠️ PDF 파일이 없습니다: {source_dir}")
            return {
                "success": True,
                "total_files": 0,
                "processed": 0,
                "skipped": 0,
                "failed": 0,
                "results": []
            }
        
        print(f"\n{'='*80}")
        print(f"📁 디렉토리 일괄 처리 시작")
        print(f"{'='*80}")
        print(f"디렉토리: {source_dir}")
        print(f"PDF 파일 수: {len(pdf_files)}개")
        print(f"{'='*80}\n")
        
        results = []
        processed_count = 0
        skipped_count = 0
        failed_count = 0
        
        for pdf_file in pdf_files:
            result = self.ingest_document_intelligent(
                pdf_path=str(pdf_file),
                force_update=force_update,
                source_root=source_dir
            )
            
            results.append(result)
            
            if result["status"] == "processed":
                processed_count += 1
            elif result["status"] == "skipped":
                skipped_count += 1
            elif result["status"] == "failed":
                failed_count += 1
        
        # 상세 보고서 생성
        report = {
            "success": True,
            "total_files": len(pdf_files),
            "processed": processed_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "results": results,
            "summary": {
                "기존 파일 유지": skipped_count,
                "새 파일 추가 완료": processed_count,
                "중복 제외": skipped_count,
                "실패": failed_count
            }
        }
        
        # 보고서 출력
        print(f"\n{'='*80}")
        print(f"📊 실행 보고서")
        print(f"{'='*80}")
        print(f"총 파일 수: {len(pdf_files)}개")
        print(f"  ✅ 새 파일 추가 완료: {processed_count}개")
        print(f"  ⏭️ 기존 파일 유지 (중복 제외): {skipped_count}개")
        print(f"  ❌ 실패: {failed_count}개")
        print(f"{'='*80}\n")
        
        # 카테고리별 통계
        category_stats = {}
        folder_stats = {}
        for result in results:
            if result["status"] == "processed":
                category = result.get("category", "기타")
                category_stats[category] = category_stats.get(category, 0) + 1
                
                folder = result.get("folder_path", ".")
                folder_stats[folder] = folder_stats.get(folder, 0) + 1
        
        if category_stats:
            print("📊 카테고리별 통계:")
            for category, count in sorted(category_stats.items()):
                print(f"  {category}: {count}개")
            print()
        
        if folder_stats:
            print("📁 폴더별 통계:")
            for folder, count in sorted(folder_stats.items()):
                print(f"  {folder}: {count}개")
            print()
        
        return report


# ══════════════════════════════════════════════════════════════════════════════
# 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    # 환경변수에서 API 키 로드
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
        print("❌ 환경변수 미설정:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_KEY")
        print("  - OPENAI_API_KEY")
        sys.exit(1)
    
    # 파이프라인 초기화
    pipeline = IntelligentRAGPipeline(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        openai_api_key=OPENAI_API_KEY
    )
    
    print("✅ 지능형 RAG 파이프라인 모듈 로드 완료")
    print("사용 예시:")
    print("  pipeline.ingest_directory_intelligent('./hq_backend/knowledge_base/source_docs')")
