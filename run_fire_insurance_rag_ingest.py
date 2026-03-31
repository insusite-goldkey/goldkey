"""
법인화재보험 130% 플랜 RAG 인제스트 스크립트
source_docs 폴더의 화재보험 관련 마크다운 파일을 Supabase RAG에 업로드

실행 방법:
    python run_fire_insurance_rag_ingest.py

작성일: 2026-03-31
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# 환경변수 로드
from dotenv import load_dotenv
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 환경변수 로드: {env_path.absolute()}")
else:
    print(f"⚠️ .env 파일 없음 (Streamlit secrets 사용 가능)")

print("\n" + "="*80)
print("🔥 법인화재보험 130% 플랜 RAG 인제스트")
print("="*80)

# 임베딩 히스토리 파일 경로
HISTORY_FILE = "hq_backend/knowledge_base/embedding_history.json"

# 대상 파일 목록
fire_insurance_files = [
    "source_docs/법인화재보험_130프로_논리_완결판.md",
    "source_docs/실화책임법_2007개정_법인리스크.md",
    "source_docs/재조달가액_보험가액_용어정의.md",
]

def calculate_file_hash(file_path: str) -> str:
    """파일의 SHA-256 해시 계산 (내용 기반 고유 식별자)"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_embedding_history() -> Dict:
    """임베딩 히스토리 로드 (State Tracking)"""
    history_path = Path(HISTORY_FILE)
    if history_path.exists():
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 히스토리 파일 로드 실패: {e}")
            return {"documents": []}
    else:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        return {"documents": []}

def save_embedding_history(history: Dict):
    """임베딩 히스토리 저장 (영구 보존)"""
    history_path = Path(HISTORY_FILE)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 히스토리 파일 저장 실패: {e}")

def check_document_exists(file_hash: str, history: Dict) -> Optional[Dict]:
    """문서 중복 검사 (Zero-Duplication)"""
    for doc in history.get("documents", []):
        if doc.get("file_hash") == file_hash:
            return doc
    return None

print("\n📋 인제스트 대상 파일:")
existing_files = []
for i, file_path in enumerate(fire_insurance_files, 1):
    full_path = Path(file_path)
    if full_path.exists():
        file_size = full_path.stat().st_size / 1024  # KB
        print(f"  ✅ {i}. {full_path.name} ({file_size:.1f} KB)")
        existing_files.append(full_path)
    else:
        print(f"  ❌ {i}. {full_path.name} (파일 없음)")

if not existing_files:
    print("\n❌ 인제스트할 파일이 없습니다.")
    sys.exit(1)

print(f"\n총 {len(existing_files)}개 파일 발견")

# Supabase 클라이언트 초기화
try:
    from supabase import create_client, Client
    
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_KEY"))
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n❌ Supabase 환경변수 미설정")
        print("  필요: SUPABASE_URL, SUPABASE_SERVICE_KEY")
        sys.exit(1)
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("\n✅ Supabase 클라이언트 초기화 완료")
    
except Exception as e:
    print(f"\n❌ Supabase 초기화 실패: {e}")
    sys.exit(1)

# 마크다운 파일을 knowledge_base 테이블에 저장
print("\n" + "="*80)
print("📤 RAG 인제스트 시작")
print("="*80)

# 히스토리 로드
history = load_embedding_history()

success_count = 0
fail_count = 0
skip_count = 0

for file_path in existing_files:
    try:
        print(f"\n처리 중: {file_path.name}")
        
        # ═══════════════════════════════════════════════════════════════════
        # [PRE-FLIGHT] 해시 기반 중복 차단 (Zero-Duplication)
        # ═══════════════════════════════════════════════════════════════════
        
        # 1. 파일 해시 계산 (내용 기반)
        file_hash = calculate_file_hash(str(file_path))
        print(f"   🔐 파일 해시: {file_hash[:16]}...")
        
        # 2. 중복 검사
        existing_doc = check_document_exists(file_hash, history)
        
        if existing_doc:
            # [SKIP] 로그 출력 의무화
            print(f"\n" + "="*80)
            print(f"⏭️  [SKIP] 중복 파일 발견 - OpenAI API 호출 원천 차단")
            print(f"="*80)
            print(f"📄 파일명: {file_path.name}")
            print(f"🔐 해시값: {file_hash[:32]}...")
            print(f"📅 기존 인제스트 일시: {existing_doc.get('ingested_at')}")
            print(f"📦 기존 청크 수: {existing_doc.get('chunk_count')}")
            print(f"💰 임베딩 비용 절감 완료 (토큰 및 리소스 방어)")
            print(f"="*80 + "\n")
            skip_count += 1
            continue  # 임베딩 API 호출 원천 차단
        
        print(f"   ✨ 신규 문서 감지 → OpenAI API 호출 시작")
        
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 임베딩 생성 (OpenAI API 사용)
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        
        # 텍스트를 청크로 분할 (1500자 단위)
        chunk_size = 1500
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        
        for chunk_idx, chunk_text in enumerate(chunks):
            # OpenAI 임베딩 생성
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=chunk_text
            )
            embedding_vector = response.data[0].embedding
            
            # gk_knowledge_base 스키마에 맞는 데이터 구조
            data = {
                "document_name": file_path.name,
                "document_category": "법인화재보험",
                "chunk_index": chunk_idx,
                "content": chunk_text,
                "content_length": len(chunk_text),
                "embedding": embedding_vector,
                "keywords": ["화재보험", "130%플랜", "재조달가액", "실화책임법", "비례보상"],
                "file_hash": None,
                "file_size": file_path.stat().st_size,
                "doc_date": datetime.now().date().isoformat(),
                "version": "1.0",
            }
            
            result = supabase.table("gk_knowledge_base").insert(data).execute()
            print(f"    청크 {chunk_idx + 1}/{len(chunks)} 저장 완료")
        
        print(f"  ✅ 성공: {len(content)} 문자 저장")
        success_count += 1
        
        # ═══════════════════════════════════════════════════════════════════
        # [POST-FLIGHT] 히스토리 영구 기록 (State Tracking)
        # ═══════════════════════════════════════════════════════════════════
        doc_record = {
            "file_hash": file_hash,
            "file_name": file_path.name,
            "file_path": str(file_path),
            "ingested_at": datetime.now().isoformat(),
            "chunk_count": len(chunks),
            "category": "fire_insurance",
            "description": "법인화재보험 130% 플랜"
        }
        history["documents"].append(doc_record)
        save_embedding_history(history)
        print(f"  💾 히스토리 기록 완료")
        
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        fail_count += 1

# 결과 요약
print("\n" + "="*80)
print("📊 인제스트 결과")
print("="*80)
print(f"  ✅ 성공: {success_count}개")
print(f"  ❌ 실패: {fail_count}개")
print(f"  ⏭️  건너뜀 (중복): {skip_count}개")
print(f"  📁 총 파일: {len(existing_files)}개")
if skip_count > 0:
    print(f"  💰 절감된 비용: 약 ${skip_count * 0.50:.2f} (추정)")

if success_count > 0:
    print("\n✅ RAG 인제스트 완료!")
    print("\n다음 단계:")
    print("  1. HQ 앱에서 화재보험 상담 시 RAG 검색으로 자동 인출")
    print("  2. gk_sec09 탭에서 130% 플랜 시뮬레이션 활용")
    print("  3. CEO 권고안 생성 시 법률 근거 자동 삽입")
else:
    print("\n⚠️ 인제스트 실패")

print("\n" + "="*80)
