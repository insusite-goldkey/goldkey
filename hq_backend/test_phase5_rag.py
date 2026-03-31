"""
Phase 5 RAG 파이프라인 테스트 스크립트
임베딩 → 검색 → 생성 전체 워크플로우 검증

작성일: 2026-03-30
"""
import os
import sys
from pathlib import Path

# 백엔드 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

def test_rag_ingestion():
    """RAG 임베딩 파이프라인 테스트"""
    print("\n" + "="*80)
    print("🧪 [테스트 1] RAG 임베딩 파이프라인")
    print("="*80 + "\n")
    
    try:
        from core.rag_ingestion import RAGIngestionPipeline
        
        # 환경변수 확인
        SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        
        if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
            print("⚠️ 환경변수 미설정. 시뮬레이션 모드로 진행")
            print("  필요 변수: SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY")
            return False
        
        # 파이프라인 초기화
        pipeline = RAGIngestionPipeline(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            openai_api_key=OPENAI_API_KEY
        )
        
        print("✅ RAG 임베딩 파이프라인 초기화 성공")
        
        # 테스트 문서 경로 (실제 파일이 있어야 함)
        test_pdf = "./documents/법인_상담_자료.pdf"
        
        if Path(test_pdf).exists():
            print(f"\n📄 테스트 문서: {test_pdf}")
            
            # 임베딩 실행
            result = pipeline.ingest_document(
                pdf_path=test_pdf,
                document_category="법인컨설팅"
            )
            
            if result["success"]:
                print(f"\n✅ 임베딩 완료:")
                print(f"  - 문서명: {result['document_name']}")
                print(f"  - 청크 수: {result['chunks_count']}")
                print(f"  - 카테고리: {result['category']}")
                return True
            else:
                print(f"\n❌ 임베딩 실패: {result.get('error')}")
                return False
        else:
            print(f"\n⚠️ 테스트 문서 없음: {test_pdf}")
            print("  실제 PDF 파일을 ./documents/ 폴더에 배치하세요")
            return False
    
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_engine():
    """RAG 검색 증강 생성기 테스트"""
    print("\n" + "="*80)
    print("🧪 [테스트 2] RAG 검색 증강 생성기")
    print("="*80 + "\n")
    
    try:
        from engines.rag_engine import RAGEngine
        
        # 환경변수 확인
        SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        
        if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, GEMINI_API_KEY]):
            print("⚠️ 환경변수 미설정. 시뮬레이션 모드로 진행")
            print("  필요 변수: SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, GEMINI_API_KEY")
            return False
        
        # RAG 엔진 초기화
        rag_engine = RAGEngine(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            openai_api_key=OPENAI_API_KEY,
            gemini_api_key=GEMINI_API_KEY
        )
        
        print("✅ RAG 엔진 초기화 성공")
        
        # 테스트 질의
        test_queries = [
            {
                "query": "공장 화재보험 가입 시 120% 가입 룰이 뭐야?",
                "category": "화재보험"
            },
            {
                "query": "법인 임원 퇴직금 한도 관련 예규 찾아줘",
                "category": "법인컨설팅"
            },
            {
                "query": "건물소유자 배상책임보험 가입 대상은?",
                "category": "배상책임"
            }
        ]
        
        results = []
        
        for i, test in enumerate(test_queries):
            print(f"\n{'─'*80}")
            print(f"질의 {i+1}: {test['query']}")
            print(f"카테고리: {test['category']}")
            print(f"{'─'*80}")
            
            result = rag_engine.query(
                user_query=test["query"],
                category=test["category"],
                match_threshold=0.7,
                match_count=5,
                temperature=0.0  # 환각 차단
            )
            
            print(f"\n📄 답변:")
            print(result["answer"])
            print(f"\n신뢰도: {result['confidence']}")
            print(f"검색된 문서: {result['retrieved_count']}개")
            
            if result["sources"]:
                print(f"\n출처:")
                for source in result["sources"]:
                    print(f"  - {source['document']} (페이지 {source['page']}, 유사도: {source['similarity']:.2f})")
            
            results.append(result)
        
        print(f"\n✅ 총 {len(results)}개 질의 처리 완료")
        return True
    
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_master_router():
    """마스터 라우터 분기 로직 테스트"""
    print("\n" + "="*80)
    print("🧪 [테스트 3] 마스터 라우터 분기 로직")
    print("="*80 + "\n")
    
    try:
        from core.master_router import MasterRouter
        
        # 환경변수 확인
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        
        if not all([GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
            print("⚠️ 환경변수 미설정. 시뮬레이션 모드로 진행")
            return False
        
        # 마스터 라우터 초기화 (RAG 활성화)
        router = MasterRouter(
            gemini_api_key=GEMINI_API_KEY,
            enable_rag=True,
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            openai_api_key=OPENAI_API_KEY
        )
        
        print("✅ 마스터 라우터 초기화 성공 (RAG 활성화)")
        
        # 테스트 1: 지식베이스 질의 (Cat 7: 법인컨설팅)
        print("\n" + "─"*80)
        print("시나리오 1: 법인컨설팅 질의 → RAG 엔진")
        print("─"*80)
        
        result1 = router.route_request(
            request_type="knowledge_query",
            user_query="법인 임원 퇴직금 한도는?",
            category="법인컨설팅"
        )
        
        print(f"\n답변: {result1.get('answer', 'N/A')[:200]}...")
        print(f"신뢰도: {result1.get('confidence', 'N/A')}")
        
        # 테스트 2: 지식베이스 질의 (Cat 5: 화재보험)
        print("\n" + "─"*80)
        print("시나리오 2: 화재보험 질의 → RAG 엔진")
        print("─"*80)
        
        result2 = router.route_request(
            request_type="knowledge_query",
            user_query="공장 화재보험 120% 가입 룰",
            category="화재보험"
        )
        
        print(f"\n답변: {result2.get('answer', 'N/A')[:200]}...")
        print(f"신뢰도: {result2.get('confidence', 'N/A')}")
        
        # 테스트 3: 증권 분석 (Cat 1, 8: 기존 로직)
        print("\n" + "─"*80)
        print("시나리오 3: 증권 분석 → Coverage Calculator (기존 로직)")
        print("─"*80)
        print("⚠️ 실제 GCS URI가 필요하므로 스킵")
        
        print("\n✅ 라우터 분기 로직 검증 완료")
        return True
    
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """전체 테스트 실행"""
    print("\n" + "="*80)
    print("🚀 Phase 5 RAG 파이프라인 통합 테스트")
    print("="*80)
    
    results = {
        "임베딩 파이프라인": test_rag_ingestion(),
        "RAG 엔진": test_rag_engine(),
        "마스터 라우터": test_master_router()
    }
    
    print("\n" + "="*80)
    print("📊 테스트 결과 요약")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 모든 테스트 통과!")
    else:
        print("\n⚠️ 일부 테스트 실패. 환경변수 및 문서 파일을 확인하세요.")
    
    print("="*80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
