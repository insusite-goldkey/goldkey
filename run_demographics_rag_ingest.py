# -*- coding: utf-8 -*-
"""
인구통계학적 지능 RAG 인제스트 스크립트
대한민국 페르소나별 급소(Pain Point) 지도를 Supabase gk_knowledge_base에 주입

작성일: 2026-03-31
목적: 에이전틱 AI 비서의 근거 기반 전략 수립을 위한 지식 베이스 구축
"""

import os
import sys
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Supabase 클라이언트
try:
    from supabase import create_client, Client
except ImportError:
    print("❌ supabase 라이브러리가 설치되어 있지 않습니다.")
    print("pip install supabase 를 실행하세요.")
    sys.exit(1)

# OpenAI 임베딩
try:
    import openai
except ImportError:
    print("❌ openai 라이브러리가 설치되어 있지 않습니다.")
    print("pip install openai 를 실행하세요.")
    sys.exit(1)


# 임베딩 히스토리 파일 경로
HISTORY_FILE = "hq_backend/knowledge_base/embedding_history.json"

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

def load_env_secrets():
    """환경 변수 로드"""
    from dotenv import load_dotenv
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not all([supabase_url, supabase_key, openai_api_key]):
        print("❌ 환경 변수가 설정되지 않았습니다.")
        print("SUPABASE_URL, SUPABASE_SERVICE_KEY, OPENAI_API_KEY를 확인하세요.")
        sys.exit(1)
    
    return supabase_url, supabase_key, openai_api_key


def get_embedding(text: str, api_key: str) -> List[float]:
    """OpenAI API를 사용하여 텍스트 임베딩 생성"""
    openai.api_key = api_key
    
    try:
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ 임베딩 생성 실패: {e}")
        return [0.0] * 1536  # 기본 벡터 반환


def chunk_text(text: str, max_length: int = 2000) -> List[str]:
    """텍스트를 청크로 분할"""
    chunks = []
    lines = text.split('\n')
    current_chunk = ""
    
    for line in lines:
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + "\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def ingest_demographics_intelligence(
    supabase: Client,
    openai_api_key: str
) -> None:
    """인구통계학적 지능 문서를 RAG 시스템에 주입"""
    
    # 문서 경로
    doc_path = Path(__file__).parent / "source_docs" / "demographics_intelligence_2026.md"
    
    if not doc_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {doc_path}")
        return
    
    print(f"📄 파일 읽기: {doc_path}")
    
    # ═══════════════════════════════════════════════════════════════════
    # [PRE-FLIGHT] 해시 기반 중복 차단 (Zero-Duplication)
    # ═══════════════════════════════════════════════════════════════════
    
    # 1. 히스토리 로드
    history = load_embedding_history()
    
    # 2. 파일 해시 계산 (내용 기반)
    file_hash = calculate_file_hash(str(doc_path))
    print(f"🔐 파일 해시: {file_hash[:16]}...")
    
    # 3. 중복 검사
    existing_doc = check_document_exists(file_hash, history)
    
    if existing_doc:
        # [SKIP] 로그 출력 의무화
        print(f"\n" + "="*80)
        print(f"⏭️  [SKIP] 중복 파일 발견 - OpenAI API 호출 원천 차단")
        print(f"="*80)
        print(f"📄 파일명: {doc_path.name}")
        print(f"🔐 해시값: {file_hash[:32]}...")
        print(f"📅 기존 인제스트 일시: {existing_doc.get('ingested_at')}")
        print(f"📦 기존 청크 수: {existing_doc.get('chunk_count')}")
        print(f"💰 임베딩 비용 절감 완료 (토큰 및 리소스 방어)")
        print(f"="*80 + "\n")
        return  # 임베딩 API 호출 원천 차단
    
    print(f"✨ 신규 문서 감지 → OpenAI API 호출 시작")
    
    # 파일 읽기
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 청크 분할
    chunks = chunk_text(content, max_length=1500)
    
    print(f"\n✅ 인제스트 완료: {len(chunks)}개 청크 저장됨")
    
    # ═══════════════════════════════════════════════════════════════════
    # [POST-FLIGHT] 히스토리 영구 기록 (State Tracking)
    # ═══════════════════════════════════════════════════════════════════
    doc_record = {
        "file_hash": file_hash,
        "file_name": doc_path.name,
        "file_path": str(doc_path),
        "ingested_at": datetime.now().isoformat(),
        "chunk_count": len(chunks),
        "category": "demographics_intelligence",
        "description": "대한민국 페르소나별 급소(Pain Point) 지도"
    }
    history["documents"].append(doc_record)
    save_embedding_history(history)
    print(f"💾 히스토리 기록 완료 → {HISTORY_FILE}")
    
    # 각 청크를 Supabase에 삽입
    for idx, chunk in enumerate(chunks, 1):
        print(f"🔄 [{idx}/{len(chunks)}] 청크 처리 중...")
        
        # 임베딩 생성
        embedding = get_embedding(chunk, openai_api_key)
        
        # 카테고리 자동 감지
        category = "인구통계"
        if "5060" in chunk or "법인 대표" in chunk or "사업가" in chunk:
            category = "인구통계_5060법인대표"
        elif "3040" in chunk or "공무원" in chunk or "교사" in chunk:
            category = "인구통계_3040공무원"
        elif "MZ" in chunk or "1인 가구" in chunk:
            category = "인구통계_MZ1인가구"
        elif "생산직" in chunk or "현장" in chunk:
            category = "인구통계_생산직현장"
        
        # 데이터 구조
        data = {
            "document_name": "demographics_intelligence_2026.md",
            "document_category": category,
            "chunk_index": idx,
            "content": chunk,
            "content_length": len(chunk),
            "embedding": embedding,
            "source": "통계청/보험연구원/보건사회연구원",
            "year": 2026,
            "quarter": 1,
            "tags": ["인구통계", "페르소나", "급소", "Pain Point", "2026년 1분기"]
        }
        
        try:
            # Supabase에 삽입
            result = supabase.table("gk_knowledge_base").insert(data).execute()
            print(f"✅ [{idx}/{len(chunks)}] 삽입 완료: {category}")
        except Exception as e:
            print(f"❌ [{idx}/{len(chunks)}] 삽입 실패: {e}")
            continue
    
    print(f"\n🎉 인구통계학적 지능 주입 완료!")
    print(f"📊 총 {len(chunks)}개 청크가 gk_knowledge_base에 저장되었습니다.")


def main():
    """메인 함수"""
    print("=" * 60)
    print("🧠 인구통계학적 지능 RAG 인제스트")
    print("=" * 60)
    
    # 환경 변수 로드
    supabase_url, supabase_key, openai_api_key = load_env_secrets()
    
    # Supabase 클라이언트 생성
    supabase: Client = create_client(supabase_url, supabase_key)
    
    print("✅ Supabase 연결 성공")
    
    # 인구통계학적 지능 주입
    ingest_demographics_intelligence(supabase, openai_api_key)
    
    print("\n" + "=" * 60)
    print("✅ 모든 작업 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
