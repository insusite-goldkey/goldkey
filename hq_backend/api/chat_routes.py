# -*- coding: utf-8 -*-
"""
Chat API Routes
RAG 기반 고객 상담 챗봇 API with Query Expansion

작성일: 2026-03-31
목적: Query Expansion을 통한 RAG 검색 정확도 향상
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# FastAPI
try:
    from fastapi import APIRouter, HTTPException, Request
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError:
    print("❌ fastapi 라이브러리가 설치되어 있지 않습니다.")
    print("pip install fastapi 를 실행하세요.")
    raise

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Query Expansion Engine
try:
    from hq_backend.services.query_expansion_engine import QueryExpansionEngine
except ImportError:
    print("⚠️ query_expansion_engine 모듈을 찾을 수 없습니다.")
    try:
        from ..services.query_expansion_engine import QueryExpansionEngine
    except ImportError:
        print("❌ QueryExpansionEngine을 import할 수 없습니다.")
        raise

# Supabase
try:
    from supabase import create_client
except ImportError:
    print("❌ supabase 라이브러리가 설치되어 있지 않습니다.")
    print("pip install supabase 를 실행하세요.")
    raise

# OpenAI
try:
    import openai
except ImportError:
    print("❌ openai 라이브러리가 설치되어 있지 않습니다.")
    print("pip install openai 를 실행하세요.")
    raise


# API Router 초기화
router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)


# 요청/응답 모델
class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    top_k: int = 5


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    query: str
    expanded_query: str
    meta_keywords: List[str]
    search_results: List[Dict]
    answer: str
    timestamp: str


# Query Expansion Engine 초기화 (싱글톤)
_query_expansion_engine = None


def get_query_expansion_engine() -> QueryExpansionEngine:
    """Query Expansion Engine 싱글톤 인스턴스 반환"""
    global _query_expansion_engine
    if _query_expansion_engine is None:
        _query_expansion_engine = QueryExpansionEngine()
    return _query_expansion_engine


def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    OpenAI API를 사용하여 텍스트 임베딩 생성
    
    Args:
        text: 임베딩할 텍스트
        model: 임베딩 모델
    
    Returns:
        List[float]: 임베딩 벡터
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    openai.api_key = api_key
    
    try:
        response = openai.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ 임베딩 생성 실패: {e}")
        raise


def search_knowledge_base(
    query_embedding: List[float],
    top_k: int = 5,
    filter_company: Optional[str] = None,
    filter_reference_date: Optional[str] = None
) -> List[Dict]:
    """
    Supabase gk_knowledge_base에서 유사도 검색
    
    ⚠️ 중요: is_active=true인 데이터만 검색 (Hot-Swap 적용)
    
    Args:
        query_embedding: 쿼리 임베딩 벡터
        top_k: 반환할 결과 수
        filter_company: 보험사 필터 (선택)
        filter_reference_date: 기준연월 필터 (선택)
    
    Returns:
        List[Dict]: 검색 결과 (활성 버전만)
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL 또는 SUPABASE_SERVICE_KEY 환경 변수가 설정되지 않았습니다.")
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Supabase RPC 함수 호출 (search_knowledge_base)
        # 함수 내부에서 is_active=true 필터 자동 적용
        result = supabase.rpc(
            "search_knowledge_base",
            {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "filter_company": filter_company,
                "filter_reference_date": filter_reference_date
            }
        ).execute()
        
        return result.data if result.data else []
    
    except Exception as e:
        print(f"❌ Knowledge Base 검색 실패: {e}")
        return []


def generate_answer(
    query: str,
    search_results: List[Dict]
) -> str:
    """
    검색 결과를 기반으로 답변 생성
    
    Args:
        query: 사용자 질문
        search_results: 검색 결과
    
    Returns:
        str: 생성된 답변
    """
    if not search_results:
        return "죄송합니다. 관련 정보를 찾을 수 없습니다."
    
    # 검색 결과를 컨텍스트로 구성
    context = "\n\n".join([
        f"[문서 {idx+1}] {result.get('content', '')}"
        for idx, result in enumerate(search_results)
    ])
    
    # OpenAI API로 답변 생성
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    openai.api_key = api_key
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": """당신은 보험 전문 상담사입니다. 
제공된 문서를 기반으로 고객의 질문에 정확하고 친절하게 답변하세요.
전문 용어는 쉽게 풀어서 설명하고, 구체적인 예시를 들어주세요."""
                },
                {
                    "role": "user",
                    "content": f"""다음 문서를 참고하여 질문에 답변해주세요.

[참고 문서]
{context}

[질문]
{query}

[답변]"""
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"❌ 답변 생성 실패: {e}")
        return "죄송합니다. 답변 생성 중 오류가 발생했습니다."


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """
    채팅 쿼리 처리 (Query Expansion 적용)
    
    Args:
        request: 채팅 요청
    
    Returns:
        ChatResponse: 채팅 응답
    """
    print(f"\n{'='*70}")
    print(f"💬 채팅 쿼리 수신")
    print(f"{'='*70}")
    print(f"📝 원본 쿼리: {request.query}")
    
    try:
        # 1. Query Expansion (질의 확장)
        print(f"\n🔍 [1/4] Query Expansion 수행 중...")
        engine = get_query_expansion_engine()
        expansion_result = engine.expand_query(request.query)
        
        print(f"✅ 확장된 쿼리: {expansion_result.expanded_query}")
        print(f"🏷️  메타 키워드 ({expansion_result.expansion_count}개): {', '.join(expansion_result.meta_keywords)}")
        
        # 2. 임베딩 생성 (확장된 쿼리 사용)
        print(f"\n🧠 [2/4] 임베딩 생성 중...")
        query_embedding = get_embedding(expansion_result.expanded_query)
        print(f"✅ 임베딩 생성 완료 (차원: {len(query_embedding)})")
        
        # 3. Knowledge Base 검색
        print(f"\n📚 [3/4] Knowledge Base 검색 중...")
        search_results = search_knowledge_base(
            query_embedding=query_embedding,
            top_k=request.top_k
        )
        print(f"✅ 검색 완료: {len(search_results)}개 결과")
        
        # 4. 답변 생성
        print(f"\n💬 [4/4] 답변 생성 중...")
        answer = generate_answer(request.query, search_results)
        print(f"✅ 답변 생성 완료")
        
        # 응답 구성
        response = ChatResponse(
            query=request.query,
            expanded_query=expansion_result.expanded_query,
            meta_keywords=expansion_result.meta_keywords,
            search_results=search_results,
            answer=answer,
            timestamp=datetime.now().isoformat()
        )
        
        print(f"\n{'='*70}")
        print(f"✅ 채팅 쿼리 처리 완료")
        print(f"{'='*70}")
        
        return response
    
    except Exception as e:
        print(f"\n❌ 채팅 쿼리 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    engine = get_query_expansion_engine()
    
    return {
        "status": "healthy",
        "query_expansion_engine": {
            "glossary_terms": len(engine.glossary),
            "term_index_size": len(engine.term_index)
        },
        "timestamp": datetime.now().isoformat()
    }


@router.post("/expand")
async def expand_query_only(query: str):
    """
    쿼리 확장만 수행 (테스트용)
    
    Args:
        query: 사용자 질문
    
    Returns:
        Dict: 확장 결과
    """
    engine = get_query_expansion_engine()
    result = engine.expand_query(query)
    stats = engine.get_expansion_statistics(result)
    
    return {
        "original_query": result.original_query,
        "expanded_query": result.expanded_query,
        "meta_keywords": result.meta_keywords,
        "matched_terms": result.matched_terms,
        "statistics": stats
    }
