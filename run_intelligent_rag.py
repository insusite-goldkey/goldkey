"""
[Phase 5 고도화] 지능형 RAG 임베딩 파이프라인 독립 실행 스크립트
source_docs 폴더의 모든 PDF를 자동으로 처리하고 상세 보고서 생성

실행 방법:
    python run_intelligent_rag.py

작성일: 2026-03-30
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 환경변수 로드
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 환경변수 로드: {env_path.absolute()}")
else:
    print(f"⚠️ .env 파일 없음: {env_path.absolute()}")

# 환경변수 확인
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_KEY"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print("\n" + "="*80)
print("🚀 지능형 RAG 임베딩 파이프라인 실행")
print("="*80)

# 환경변수 검증
missing_vars = []
if not SUPABASE_URL:
    missing_vars.append("SUPABASE_URL")
if not SUPABASE_KEY:
    missing_vars.append("SUPABASE_SERVICE_KEY")
if not OPENAI_API_KEY:
    missing_vars.append("OPENAI_API_KEY")

if missing_vars:
    print("\n❌ 환경변수 미설정:")
    for var in missing_vars:
        print(f"  - {var}")
    print(f"\n.env 파일 경로: {env_path.absolute()}")
    print("환경변수를 설정한 후 다시 실행하세요.")
    sys.exit(1)

print("\n✅ 환경변수 확인 완료")
print(f"  SUPABASE_URL: {SUPABASE_URL[:30]}...")
print(f"  SUPABASE_KEY: {'*' * 20}")
print(f"  OPENAI_API_KEY: {'*' * 20}")

# 파이프라인 import
print("\n🔧 모듈 로드 중...")
try:
    # 직접 import (순환 참조 방지)
    import importlib.util
    
    spec = importlib.util.spec_from_file_location(
        "rag_ingestion_v2",
        "hq_backend/core/rag_ingestion_v2.py"
    )
    rag_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rag_module)
    
    IntelligentRAGPipeline = rag_module.IntelligentRAGPipeline
    print("✅ 모듈 로드 완료")
    
except Exception as e:
    print(f"\n❌ 모듈 import 실패: {e}")
    print("\n다음 명령으로 필수 패키지를 설치하세요:")
    print("pip install langchain-text-splitters langchain-community pypdf openai supabase")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 소스 디렉토리 확인
source_dir = Path("hq_backend/knowledge_base/source_docs")

if not source_dir.exists():
    print(f"\n❌ 소스 디렉토리 없음: {source_dir.absolute()}")
    sys.exit(1)

pdf_files = list(source_dir.glob("**/*.pdf"))
print(f"\n📁 소스 디렉토리: {source_dir.absolute()}")
print(f"📄 PDF 파일 수: {len(pdf_files)}개")

if not pdf_files:
    print("\n⚠️ PDF 파일이 없습니다. source_docs 폴더에 PDF 파일을 추가하세요.")
    sys.exit(0)

# 파일 목록 출력
print("\n📋 발견된 PDF 파일:")
for i, pdf_file in enumerate(pdf_files, 1):
    file_size = pdf_file.stat().st_size / 1024  # KB
    print(f"  {i}. {pdf_file.name} ({file_size:.1f} KB)")

# 사용자 확인
print("\n" + "="*80)
print("⚠️ 주의: 이 작업은 OpenAI API 비용이 발생합니다.")
print("="*80)
print(f"처리할 파일 수: {len(pdf_files)}개")
print("예상 비용: 약 $0.01 ~ $0.10 (파일 크기에 따라 다름)")
print("\n계속하시겠습니까? (y/n): ", end="")

try:
    user_input = input().strip().lower()
    if user_input != 'y':
        print("\n❌ 사용자가 취소했습니다.")
        sys.exit(0)
except KeyboardInterrupt:
    print("\n\n❌ 사용자가 취소했습니다.")
    sys.exit(0)

# 파이프라인 초기화
print("\n" + "="*80)
print("🔧 파이프라인 초기화 중...")
print("="*80)

try:
    pipeline = IntelligentRAGPipeline(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY,
        openai_api_key=OPENAI_API_KEY
    )
except Exception as e:
    print(f"\n❌ 파이프라인 초기화 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 디렉토리 일괄 처리
print("\n" + "="*80)
print("📂 디렉토리 일괄 처리 시작")
print("="*80)

try:
    report = pipeline.ingest_directory_intelligent(
        source_dir=str(source_dir),
        force_update=False  # 중복 파일은 자동으로 스킵
    )
    
    # 보고서 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"RAG_INGESTION_REPORT_{timestamp}.json"
    report_path = Path(report_filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, indent=2, ensure_ascii=False, fp=f)
    
    print(f"\n💾 보고서 저장: {report_path.absolute()}")
    
    # 최종 요약
    print("\n" + "="*80)
    print("✅ 지능형 RAG 임베딩 파이프라인 완료")
    print("="*80)
    print(f"총 파일 수: {report['total_files']}개")
    print(f"  ✅ 새 파일 추가 완료: {report['processed']}개")
    print(f"  ⏭️ 기존 파일 유지 (중복 제외): {report['skipped']}개")
    print(f"  ❌ 실패: {report['failed']}개")
    print("="*80)
    
    # 처리된 파일 상세 정보
    if report['processed'] > 0:
        print("\n📊 처리된 파일 상세:")
        for result in report['results']:
            if result['status'] == 'processed':
                print(f"  ✅ {result['document_name']}")
                print(f"     카테고리: {result['category']}")
                print(f"     청크 수: {result['chunks_count']}개")
                print(f"     문서 날짜: {result.get('doc_date', '없음')}")
                print(f"     버전: {result.get('version', '없음')}")
    
    # 스킵된 파일 상세 정보
    if report['skipped'] > 0:
        print("\n⏭️ 스킵된 파일 (중복):")
        for result in report['results']:
            if result['status'] == 'skipped':
                print(f"  ⏭️ {result['document_name']}")
                print(f"     사유: {result['reason']}")
    
    # 실패한 파일 상세 정보
    if report['failed'] > 0:
        print("\n❌ 실패한 파일:")
        for result in report['results']:
            if result['status'] == 'failed':
                print(f"  ❌ {result['document_name']}")
                print(f"     오류: {result.get('error', '알 수 없음')}")
    
    print("\n" + "="*80)
    print("다음 단계:")
    print("  1. CRM 앱 실행: streamlit run crm_app.py --server.port 8502")
    print("  2. AI 상담 채팅에서 RAG 기능 테스트")
    print("="*80)
    print()

except Exception as e:
    print(f"\n❌ 파이프라인 실행 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
