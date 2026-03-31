"""
기존 RAG 지식베이스 데이터 삭제 스크립트
재실행 전 중복 방지용
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

def main():
    # 환경변수 로드
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_KEY"))
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ 환경변수 미설정")
        sys.exit(1)
    
    # Supabase 클라이언트
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\n" + "="*80)
    print("🗑️  RAG 지식베이스 데이터 삭제")
    print("="*80 + "\n")
    
    try:
        # 기존 데이터 조회
        result = supabase.table("gk_knowledge_base").select("id", count="exact").execute()
        count = result.count if hasattr(result, 'count') else len(result.data)
        
        print(f"📊 현재 저장된 청크 수: {count}개\n")
        
        if count == 0:
            print("✅ 삭제할 데이터가 없습니다.")
            return
        
        # 전체 삭제
        print("🗑️  전체 데이터 삭제 중...")
        
        # Supabase는 전체 삭제 시 조건 필요 - 모든 레코드 삭제
        delete_result = supabase.table("gk_knowledge_base").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        print("✅ 삭제 완료!\n")
        print("="*80)
        print("이제 RAG 임베딩 파이프라인을 다시 실행하세요:")
        print("python hq_backend\\run_rag_ingestion.py")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ 삭제 실패: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
