"""
[Phase 5] RAG 지식베이스 임베딩 파이프라인
PDF 문서를 Text Chunk로 분할하고 벡터화하여 Supabase pgvector에 저장

작성일: 2026-03-30
"""
from typing import List, Dict, Optional
from pathlib import Path
import os
import json

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


class RAGIngestionPipeline:
    """RAG 지식베이스 임베딩 파이프라인"""
    
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
                "pip install langchain pypdf openai supabase"
            )
        
        # Supabase 클라이언트
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # OpenAI 클라이언트
        openai.api_key = openai_api_key
        self.embedding_model = embedding_model
        
        # LangChain Text Splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,           # 청크 크기 (1000~2000자 권장)
            chunk_overlap=200,         # 청크 간 중복 (문맥 유지)
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        print("✅ RAG 임베딩 파이프라인 초기화 완료")
    
    def load_pdf(self, pdf_path: str) -> List[Dict]:
        """
        PDF 파일 로드 및 텍스트 추출
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            페이지별 텍스트 리스트
                [
                    {"page": 1, "content": "..."},
                    {"page": 2, "content": "..."}
                ]
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
                [
                    {
                        "document_name": "법인_상담_자료.pdf",
                        "chunk_index": 0,
                        "content": "...",
                        "source_page": 1
                    }
                ]
        """
        print(f"✂️ 텍스트 청크 분할 중...")
        
        chunks = []
        chunk_index = 0
        
        for doc in documents:
            page_num = doc["page"]
            content = doc["content"]
            
            # 페이지 내용을 청크로 분할
            page_chunks = self.text_splitter.split_text(content)
            
            for chunk_text in page_chunks:
                # NULL 문자 제거 (PostgreSQL 호환성)
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
        # 간단한 구현: 공백 기준 분리 후 빈도 계산
        # 실제로는 KoNLPy, spaCy 등 사용 권장
        words = text.split()
        word_freq = {}
        
        for word in words:
            # 3글자 이상만 키워드로 간주
            if len(word) >= 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도 순 정렬
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        return keywords
    
    def ingest_document(
        self,
        pdf_path: str,
        document_category: str,
        batch_size: int = 10
    ) -> Dict:
        """
        PDF 문서를 전체 파이프라인으로 처리하여 Supabase에 저장
        
        Args:
            pdf_path: PDF 파일 경로
            document_category: 문서 카테고리 (예: "법인컨설팅", "화재보험")
            batch_size: 배치 크기 (임베딩 API 호출 최적화)
        
        Returns:
            처리 결과
                {
                    "success": True,
                    "document_name": "법인_상담_자료.pdf",
                    "chunks_count": 45,
                    "category": "법인컨설팅"
                }
        """
        print(f"\n{'='*80}")
        print(f"🚀 RAG 임베딩 파이프라인 시작")
        print(f"{'='*80}")
        print(f"문서: {pdf_path}")
        print(f"카테고리: {document_category}")
        print(f"{'='*80}\n")
        
        document_name = Path(pdf_path).name
        
        try:
            # 1단계: PDF 로드
            documents = self.load_pdf(pdf_path)
            
            # 2단계: 청크 분할
            chunks = self.split_into_chunks(documents, document_name)
            
            # 3단계: 배치별 임베딩 생성 및 저장
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
                    # 키워드 추출
                    keywords = self.extract_keywords(chunk["content"])
                    
                    # 레코드 생성
                    record = {
                        "document_name": chunk["document_name"],
                        "document_category": document_category,
                        "chunk_index": chunk["chunk_index"],
                        "content": chunk["content"],
                        "content_length": chunk["content_length"],
                        "embedding": embedding,
                        "source_page": chunk["source_page"],
                        "keywords": keywords
                    }
                    
                    # Supabase 삽입 (upsert)
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
                "document_name": document_name,
                "chunks_count": inserted_count,
                "category": document_category
            }
        
        except Exception as e:
            print(f"❌ 파이프라인 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document_name": document_name,
                "chunks_count": 0,
                "category": document_category
            }
    
    def ingest_multiple_documents(
        self,
        pdf_paths: List[str],
        categories: List[str]
    ) -> List[Dict]:
        """
        여러 PDF 문서를 일괄 처리
        
        Args:
            pdf_paths: PDF 파일 경로 리스트
            categories: 각 문서의 카테고리 리스트
        
        Returns:
            처리 결과 리스트
        """
        if len(pdf_paths) != len(categories):
            raise ValueError("pdf_paths와 categories 길이가 일치해야 합니다")
        
        results = []
        
        for pdf_path, category in zip(pdf_paths, categories):
            result = self.ingest_document(pdf_path, category)
            results.append(result)
        
        return results


# ══════════════════════════════════════════════════════════════════════════════
# 사용 예시 (테스트용)
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
    pipeline = RAGIngestionPipeline(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        openai_api_key=OPENAI_API_KEY
    )
    
    # 테스트: 단일 문서 처리
    # result = pipeline.ingest_document(
    #     pdf_path="./documents/법인_상담_자료.pdf",
    #     document_category="법인컨설팅"
    # )
    # print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 테스트: 다중 문서 처리
    # results = pipeline.ingest_multiple_documents(
    #     pdf_paths=[
    #         "./documents/법인_상담_자료.pdf",
    #         "./documents/건물소유점유자_배상책임.pdf",
    #         "./documents/화재_특종보험_통합자료.pdf"
    #     ],
    #     categories=[
    #         "법인컨설팅",
    #         "배상책임",
    #         "화재보험"
    #     ]
    # )
    # 
    # for result in results:
    #     print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("✅ rag_ingestion.py 모듈 로드 완료")
