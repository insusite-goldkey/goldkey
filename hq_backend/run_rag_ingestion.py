"""
Phase 5 RAG 임베딩 파이프라인 실행 스크립트
3개 핵심 PDF 문서를 Supabase pgvector에 임베딩

작성일: 2026-03-30
"""
import os
import sys
from pathlib import Path

# 백엔드 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

def load_secrets():
    """.env 파일에서 환경변수 로드"""
    env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        print(f"❌ .env 파일을 찾을 수 없습니다: {env_path}")
        return None, None, None
    
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        
        SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_KEY", ""))
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        
        return SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY
    except Exception as e:
        print(f"❌ .env 파일 로드 실패: {str(e)}")
        return None, None, None


def main():
    """RAG 임베딩 실행"""
    print("\n" + "="*80)
    print("🚀 Phase 5 RAG 임베딩 파이프라인 실행")
    print("="*80 + "\n")
    
    # secrets.toml에서 환경변수 로드
    print("📋 환경변수 로드 중...")
    SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY = load_secrets()
    
    if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
        print("\n❌ 환경변수 미설정:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_KEY (또는 SUPABASE_KEY)")
        print("  - OPENAI_API_KEY")
        print("\n프로젝트 루트의 .env 파일을 확인하세요.")
        sys.exit(1)
    
    print("✅ 환경변수 로드 성공\n")
    
    try:
        from core.rag_ingestion import RAGIngestionPipeline
        
        # 파이프라인 초기화
        pipeline = RAGIngestionPipeline(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            openai_api_key=OPENAI_API_KEY
        )
        
        print("✅ RAG 임베딩 파이프라인 초기화 성공\n")
        
        # 소스 문서 디렉토리
        source_dir = Path(__file__).parent / "knowledge_base" / "source_docs"
        
        # 3개 핵심 PDF 문서
        documents = [
            {
                "path": source_dir / "법인 상담 자료 통합본 2022.09..pdf",
                "category": "법인컨설팅"
            },
            {
                "path": source_dir / "건물소유점유자 배상책임 및 특종배상책임.pdf",
                "category": "배상책임"
            },
            {
                "path": source_dir / "개인.법인 화재및 특종보험 통합 자료.pdf",
                "category": "화재보험"
            }
        ]
        
        # 파일 존재 확인
        print("📋 문서 파일 확인 중...\n")
        for doc in documents:
            if doc["path"].exists():
                size_mb = doc["path"].stat().st_size / (1024 * 1024)
                print(f"  ✅ {doc['path'].name} ({size_mb:.2f} MB)")
            else:
                print(f"  ❌ {doc['path'].name} - 파일 없음")
                sys.exit(1)
        
        print("\n" + "="*80)
        print("🔥 임베딩 시작")
        print("="*80 + "\n")
        
        # 각 문서 임베딩 실행
        results = []
        total_chunks = 0
        
        for i, doc in enumerate(documents):
            print(f"\n{'='*80}")
            print(f"📄 문서 {i+1}/3: {doc['path'].name}")
            print(f"카테고리: {doc['category']}")
            print(f"{'='*80}\n")
            
            result = pipeline.ingest_document(
                pdf_path=str(doc["path"]),
                document_category=doc["category"],
                batch_size=10
            )
            
            results.append(result)
            
            if result["success"]:
                total_chunks += result["chunks_count"]
                print(f"\n✅ 문서 {i+1} 임베딩 완료:")
                print(f"  - 청크 수: {result['chunks_count']}개")
                print(f"  - 카테고리: {result['category']}")
            else:
                print(f"\n❌ 문서 {i+1} 임베딩 실패:")
                print(f"  - 오류: {result.get('error', 'Unknown')}")
        
        # 최종 결과 요약
        print("\n" + "="*80)
        print("📊 최종 결과 요약")
        print("="*80)
        
        success_count = sum(1 for r in results if r["success"])
        
        print(f"\n총 문서 수: {len(documents)}개")
        print(f"성공: {success_count}개")
        print(f"실패: {len(documents) - success_count}개")
        print(f"총 청크 수: {total_chunks}개")
        
        print("\n문서별 상세:")
        for i, result in enumerate(results):
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['document_name']}: {result['chunks_count']}개 청크 ({result['category']})")
        
        print("\n" + "="*80)
        print("🎉 RAG 임베딩 파이프라인 완료!")
        print("="*80 + "\n")
        
        # 결과 파일 저장
        import json
        result_file = Path(__file__).parent.parent / "RAG_INGESTION_RESULT.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump({
                "total_documents": len(documents),
                "success_count": success_count,
                "total_chunks": total_chunks,
                "results": results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📄 결과 파일 저장: {result_file}\n")
        
        return True
    
    except Exception as e:
        print(f"\n❌ 파이프라인 실행 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
