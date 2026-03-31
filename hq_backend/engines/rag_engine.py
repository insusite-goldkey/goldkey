"""
[Phase 5] RAG 검색 증강 생성기 (Retrieval-Augmented Generation Engine)
Supabase pgvector 기반 유사도 검색 + Gemini 1.5 Pro 환각 차단 생성

작성일: 2026-03-30
"""
from typing import List, Dict, Optional
import os

try:
    import openai
    _OPENAI_OK = True
except ImportError:
    _OPENAI_OK = False
    print("[WARNING] OpenAI SDK 미설치. pip install openai 실행 필요")

try:
    import google.generativeai as genai
    _GEMINI_OK = True
except ImportError:
    _GEMINI_OK = False
    print("[WARNING] Gemini SDK 미설치. pip install google-generativeai 실행 필요")

try:
    from supabase import create_client, Client
    _SUPABASE_OK = True
except ImportError:
    _SUPABASE_OK = False
    print("[WARNING] Supabase 클라이언트 미설치. pip install supabase 실행 필요")


class RAGEngine:
    """RAG 검색 증강 생성 엔진"""
    
    # [엄격한 프롬프트 제약] 환각 차단 시스템 프롬프트
    SYSTEM_PROMPT = """당신은 보험 전문 지식 검색 AI 어시스턴트입니다.

**절대 규칙 (환각 차단):**
1. 반드시 제공된 문맥(Context) 내에서만 답변하십시오.
2. 문맥에 없는 내용은 절대 추측하거나 생성하지 마십시오.
3. 답변할 수 없는 질문이면 "제공된 문서에서 해당 내용을 찾을 수 없습니다"라고 명확히 답변하십시오.
4. 법률, 세무, 인수심사 관련 내용은 특히 정확성이 중요하므로 확실하지 않으면 답변하지 마십시오.
5. 출처를 명시할 때는 문서명과 페이지 번호를 반드시 포함하십시오.

**답변 형식:**
- 간결하고 명확하게 답변
- 출처: [문서명, 페이지 X]
- 관련 법령이나 규정이 있으면 인용
"""
    
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        openai_api_key: str,
        gemini_api_key: str,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        초기화
        
        Args:
            supabase_url: Supabase 프로젝트 URL
            supabase_key: Supabase anon/service key
            openai_api_key: OpenAI API 키 (임베딩용)
            gemini_api_key: Gemini API 키 (생성용)
            embedding_model: 임베딩 모델명
        """
        if not _SUPABASE_OK or not _OPENAI_OK or not _GEMINI_OK:
            raise ImportError(
                "필수 패키지 미설치. 다음 명령 실행:\n"
                "pip install openai google-generativeai supabase"
            )
        
        # Supabase 클라이언트
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # OpenAI 클라이언트 (임베딩)
        openai.api_key = openai_api_key
        self.embedding_model = embedding_model
        
        # Gemini 클라이언트 (생성)
        genai.configure(api_key=gemini_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        
        print("✅ RAG 엔진 초기화 완료")
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        사용자 질의를 임베딩 벡터로 변환
        
        Args:
            query: 사용자 질의
        
        Returns:
            임베딩 벡터 (1536차원)
        """
        try:
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=query
            )
            
            embedding = response.data[0].embedding
            return embedding
        
        except Exception as e:
            print(f"❌ 임베딩 생성 실패: {str(e)}")
            raise
    
    def retrieve_relevant_documents(
        self,
        query_embedding: List[float],
        category: Optional[str] = None,
        match_threshold: float = 0.7,
        match_count: int = 5
    ) -> List[Dict]:
        """
        벡터 유사도 검색으로 관련 문서 검색
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            category: 카테고리 필터 (None이면 전체 검색)
            match_threshold: 유사도 임계값 (0.0~1.0)
            match_count: 반환할 최대 문서 수
        
        Returns:
            검색된 문서 리스트
                [
                    {
                        "id": "uuid",
                        "document_name": "법인_상담_자료.pdf",
                        "document_category": "법인컨설팅",
                        "content": "...",
                        "source_page": 5,
                        "similarity": 0.85
                    }
                ]
        """
        try:
            # Supabase RPC 함수 호출
            result = self.supabase.rpc(
                'search_knowledge_base',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': match_threshold,
                    'match_count': match_count,
                    'filter_category': category
                }
            ).execute()
            
            documents = result.data if result.data else []
            
            print(f"🔍 검색 완료: {len(documents)}개 문서 발견")
            for i, doc in enumerate(documents):
                print(f"  [{i+1}] {doc['document_name']} (페이지 {doc['source_page']}) - 유사도: {doc['similarity']:.2f}")
            
            return documents
        
        except Exception as e:
            print(f"❌ 문서 검색 실패: {str(e)}")
            return []
    
    def generate_answer(
        self,
        query: str,
        context_documents: List[Dict],
        temperature: float = 0.0
    ) -> Dict:
        """
        검색된 문서를 기반으로 답변 생성 (환각 차단)
        
        Args:
            query: 사용자 질의
            context_documents: 검색된 문서 리스트
            temperature: 생성 온도 (0.0 = 결정론적, 환각 최소화)
        
        Returns:
            생성 결과
                {
                    "answer": "...",
                    "sources": [
                        {"document": "법인_상담_자료.pdf", "page": 5}
                    ],
                    "confidence": "high"  # high, medium, low
                }
        """
        if not context_documents:
            return {
                "answer": "제공된 문서에서 해당 내용을 찾을 수 없습니다. 질문을 다시 구체화하거나 다른 키워드로 검색해주세요.",
                "sources": [],
                "confidence": "none"
            }
        
        # 문맥 구성
        context_text = "\n\n".join([
            f"[문서: {doc['document_name']}, 페이지: {doc['source_page']}, 유사도: {doc['similarity']:.2f}]\n{doc['content']}"
            for doc in context_documents
        ])
        
        # 프롬프트 구성
        user_prompt = f"""**질문:**
{query}

**검색된 문맥 (Context):**
{context_text}

**지시사항:**
위 문맥을 바탕으로 질문에 답변하십시오. 문맥에 없는 내용은 절대 추측하지 마십시오.
답변 마지막에 출처를 명시하십시오 (형식: 출처: [문서명, 페이지 X]).
"""
        
        try:
            # Gemini 1.5 Pro 호출 (temperature=0.0 강제)
            response = self.gemini_model.generate_content(
                [self.SYSTEM_PROMPT, user_prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,  # 환각 최소화
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=1024
                )
            )
            
            answer = response.text
            
            # 출처 추출
            sources = [
                {
                    "document": doc['document_name'],
                    "page": doc['source_page'],
                    "similarity": doc['similarity']
                }
                for doc in context_documents
            ]
            
            # 신뢰도 평가 (간단한 휴리스틱)
            avg_similarity = sum(doc['similarity'] for doc in context_documents) / len(context_documents)
            if avg_similarity >= 0.85:
                confidence = "high"
            elif avg_similarity >= 0.70:
                confidence = "medium"
            else:
                confidence = "low"
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence
            }
        
        except Exception as e:
            print(f"❌ 답변 생성 실패: {str(e)}")
            return {
                "answer": f"답변 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "confidence": "error"
            }
    
    def query(
        self,
        user_query: str,
        category: Optional[str] = None,
        match_threshold: float = 0.7,
        match_count: int = 5,
        temperature: float = 0.0
    ) -> Dict:
        """
        RAG 전체 파이프라인 실행
        
        Args:
            user_query: 사용자 질의
            category: 카테고리 필터 (예: "법인컨설팅", "화재보험")
            match_threshold: 유사도 임계값
            match_count: 검색할 문서 수
            temperature: 생성 온도 (0.0 권장)
        
        Returns:
            RAG 결과
                {
                    "query": "...",
                    "answer": "...",
                    "sources": [...],
                    "confidence": "high",
                    "retrieved_count": 5
                }
        """
        print(f"\n{'='*80}")
        print(f"🔍 RAG 파이프라인 시작")
        print(f"{'='*80}")
        print(f"질의: {user_query}")
        if category:
            print(f"카테고리 필터: {category}")
        print(f"{'='*80}\n")
        
        # 1단계: 질의 임베딩 생성
        print("🧠 [단계 1/3] 질의 임베딩 생성 중...")
        query_embedding = self.generate_query_embedding(user_query)
        print("✅ 임베딩 생성 완료")
        
        # 2단계: 관련 문서 검색
        print(f"\n🔍 [단계 2/3] 벡터 유사도 검색 중...")
        documents = self.retrieve_relevant_documents(
            query_embedding,
            category=category,
            match_threshold=match_threshold,
            match_count=match_count
        )
        
        # 3단계: 답변 생성
        print(f"\n💬 [단계 3/3] 답변 생성 중 (환각 차단 모드)...")
        result = self.generate_answer(user_query, documents, temperature)
        
        # 최종 결과
        final_result = {
            "query": user_query,
            "answer": result["answer"],
            "sources": result["sources"],
            "confidence": result["confidence"],
            "retrieved_count": len(documents)
        }
        
        print(f"\n{'='*80}")
        print(f"✅ RAG 파이프라인 완료")
        print(f"{'='*80}")
        print(f"검색된 문서: {len(documents)}개")
        print(f"신뢰도: {result['confidence']}")
        print(f"{'='*80}\n")
        
        return final_result
    
    def batch_query(
        self,
        queries: List[str],
        category: Optional[str] = None
    ) -> List[Dict]:
        """
        여러 질의를 일괄 처리
        
        Args:
            queries: 질의 리스트
            category: 카테고리 필터
        
        Returns:
            결과 리스트
        """
        results = []
        
        for i, query in enumerate(queries):
            print(f"\n[질의 {i+1}/{len(queries)}]")
            result = self.query(query, category=category)
            results.append(result)
        
        return results


# ══════════════════════════════════════════════════════════════════════════════
# 사용 예시 (테스트용)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    import json
    
    # 환경변수에서 API 키 로드
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, GEMINI_API_KEY]):
        print("❌ 환경변수 미설정:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_KEY")
        print("  - OPENAI_API_KEY")
        print("  - GEMINI_API_KEY")
        sys.exit(1)
    
    # RAG 엔진 초기화
    rag_engine = RAGEngine(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        openai_api_key=OPENAI_API_KEY,
        gemini_api_key=GEMINI_API_KEY
    )
    
    # 테스트 질의
    # result = rag_engine.query(
    #     user_query="공장 화재보험 가입 시 120% 가입 룰이 뭐야?",
    #     category="화재보험",
    #     match_threshold=0.7,
    #     match_count=5,
    #     temperature=0.0  # 환각 차단
    # )
    # 
    # print("\n📄 최종 답변:")
    # print(result["answer"])
    # print(f"\n신뢰도: {result['confidence']}")
    # print(f"\n출처:")
    # for source in result["sources"]:
    #     print(f"  - {source['document']} (페이지 {source['page']}, 유사도: {source['similarity']:.2f})")
    
    print("✅ rag_engine.py 모듈 로드 완료")
