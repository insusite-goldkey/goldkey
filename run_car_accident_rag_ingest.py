# -*- coding: utf-8 -*-
"""
교통사고 과실비율 인정기준 RAG 인제스트 스크립트
PDF 파일 파싱 → 벡터 임베딩 생성 → Supabase 저장

작성일: 2026-03-31
버전: 2.0 (PDF 파싱 통합)
"""

import os
import hashlib
import json
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
import openai
import PyPDF2
import re
from typing import List, Dict, Optional
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# Supabase 클라이언트 초기화
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("SUPABASE_URL 및 SUPABASE_SERVICE_KEY 환경 변수가 필요합니다.")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경 변수가 필요합니다.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
openai.api_key = OPENAI_API_KEY

# 인제스트할 PDF 파일
PDF_FILE = {
    "path": "static/230630_자동차사고 과실비율 인정기준_최종.pdf",
    "category": "traffic_accident_fault_ratio",
    "description": "자동차사고 과실비율 인정기준 (2023년 개정판)"
}

# 임베딩 히스토리 파일 경로
HISTORY_FILE = "hq_backend/knowledge_base/embedding_history.json"

def generate_embedding(text: str) -> list:
    """
    OpenAI API를 사용하여 텍스트 임베딩 생성
    
    Args:
        text: 임베딩할 텍스트
    
    Returns:
        list: 1536차원 임베딩 벡터
    """
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"⚠️ 임베딩 생성 실패: {e}")
        return [0.0] * 1536  # 실패 시 제로 벡터 반환

def calculate_file_hash(file_path: str) -> str:
    """
    파일의 SHA-256 해시 계산 (내용 기반 고유 식별자)
    
    Args:
        file_path: 파일 경로
    
    Returns:
        str: SHA-256 해시 값
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_embedding_history() -> Dict:
    """
    임베딩 히스토리 로드 (State Tracking)
    
    Returns:
        Dict: 히스토리 데이터
    """
    history_path = Path(HISTORY_FILE)
    
    if history_path.exists():
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 히스토리 파일 로드 실패: {e}")
            return {"documents": []}
    else:
        # 히스토리 파일 없으면 새로 생성
        history_path.parent.mkdir(parents=True, exist_ok=True)
        return {"documents": []}

def save_embedding_history(history: Dict):
    """
    임베딩 히스토리 저장 (영구 보존)
    
    Args:
        history: 히스토리 데이터
    """
    history_path = Path(HISTORY_FILE)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 히스토리 파일 저장 실패: {e}")

def check_document_exists(file_hash: str, history: Dict) -> Optional[Dict]:
    """
    문서 중복 검사 (Zero-Duplication)
    
    Args:
        file_hash: 파일 해시값
        history: 히스토리 데이터
    
    Returns:
        Optional[Dict]: 기존 문서 정보 (없으면 None)
    """
    for doc in history.get("documents", []):
        if doc.get("file_hash") == file_hash:
            return doc
    return None

def delete_existing_chunks(file_hash: str) -> int:
    """
    기존 청크 삭제 (Smart Upsert)
    
    Args:
        file_hash: 파일 해시값
    
    Returns:
        int: 삭제된 청크 수
    """
    try:
        result = supabase.table("gk_knowledge_base").delete().eq(
            "file_hash", file_hash
        ).execute()
        
        deleted_count = len(result.data) if result.data else 0
        return deleted_count
    except Exception as e:
        print(f"⚠️ 기존 청크 삭제 실패: {e}")
        return 0

def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    PDF 파일에서 페이지별 텍스트 추출
    
    Args:
        pdf_path: PDF 파일 경로
    
    Returns:
        List[Dict]: 페이지별 텍스트 리스트
    """
    pages_data = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            print(f"   📖 총 {total_pages}페이지 PDF 파일")
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                
                if text.strip():
                    pages_data.append({
                        "page_number": page_num + 1,
                        "text": text,
                        "char_count": len(text)
                    })
                
                if (page_num + 1) % 10 == 0:
                    print(f"   ⏳ {page_num + 1}/{total_pages} 페이지 처리 중...")
            
            print(f"   ✅ {len(pages_data)}페이지 텍스트 추출 완료")
            
    except Exception as e:
        print(f"   ❌ PDF 파싱 실패: {e}")
    
    return pages_data

def extract_fault_scenarios(text: str) -> List[Dict]:
    """
    텍스트에서 과실비율 시나리오 추출
    
    Args:
        text: 페이지 텍스트
    
    Returns:
        List[Dict]: 시나리오 리스트
    """
    scenarios = []
    
    # 과실비율 패턴 매칭 (예: "100:0", "80:20", "70:30")
    ratio_pattern = r'(\d{1,3})\s*:\s*(\d{1,3})'
    matches = re.finditer(ratio_pattern, text)
    
    for match in matches:
        offender_ratio = int(match.group(1))
        victim_ratio = int(match.group(2))
        
        # 합이 100인 경우만 유효
        if offender_ratio + victim_ratio == 100:
            # 주변 텍스트 추출 (시나리오 설명)
            start_pos = max(0, match.start() - 200)
            end_pos = min(len(text), match.end() + 200)
            context = text[start_pos:end_pos].strip()
            
            scenarios.append({
                "offender_ratio": offender_ratio,
                "victim_ratio": victim_ratio,
                "context": context,
                "ratio_text": f"{offender_ratio}:{victim_ratio}"
            })
    
    return scenarios

def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list:
    """
    텍스트를 청크로 분할 (과실비율 시나리오 중심)
    
    Args:
        text: 분할할 텍스트
        chunk_size: 청크 크기 (문자 수)
        overlap: 청크 간 오버랩 (문자 수)
    
    Returns:
        list: 청크 리스트
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        
        # 청크가 너무 짧으면 스킵
        if len(chunk.strip()) > 100:
            chunks.append(chunk)
        
        start += chunk_size - overlap
    
    return chunks

def ingest_pdf_file(file_info: dict, base_path: str = "d:/CascadeProjects"):
    """
    PDF 파일을 읽어 Supabase gk_knowledge_base에 저장
    [ABSOLUTE DIRECTIVE] 해시 기반 중복 차단 파이프라인 적용
    
    Args:
        file_info: 파일 정보 딕셔너리
        base_path: 프로젝트 루트 경로
    """
    file_path = os.path.join(base_path, file_info["path"])
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    print(f"\n📄 처리 중: {file_info['path']}")
    
    # ═══════════════════════════════════════════════════════════════════
    # [PRE-FLIGHT] 해시 기반 중복 차단 (Zero-Duplication)
    # ═══════════════════════════════════════════════════════════════════
    
    # 1. 히스토리 로드
    history = load_embedding_history()
    
    # 2. 파일 해시 계산 (내용 기반 고유 식별자)
    file_hash = calculate_file_hash(file_path)
    print(f"   🔐 파일 해시: {file_hash[:16]}...")
    
    # 3. 중복 검사
    existing_doc = check_document_exists(file_hash, history)
    
    if existing_doc:
        # [Absolute Skip] 중복 문서 발견 → 임베딩 API 호출 원천 차단
        print(f"   ⏭️  [Skipped] 중복 자료 제외")
        print(f"   📅 기존 인제스트 일시: {existing_doc.get('ingested_at')}")
        print(f"   📦 기존 청크 수: {existing_doc.get('chunk_count')}")
        print(f"   ✅ 임베딩 비용 절감 완료 (토큰 및 리소스 방어)")
        return
    
    print(f"   ✨ 신규 문서 감지 → 임베딩 생성 시작")
    
    # PDF 텍스트 추출
    pages_data = extract_text_from_pdf(file_path)
    
    if not pages_data:
        print(f"❌ PDF에서 텍스트를 추출할 수 없습니다")
        return
    
    total_chunks = 0
    total_scenarios = 0
    
    # 페이지별 처리
    for page_data in pages_data:
        page_num = page_data["page_number"]
        page_text = page_data["text"]
        
        # 과실비율 시나리오 추출
        scenarios = extract_fault_scenarios(page_text)
        total_scenarios += len(scenarios)
        
        # 텍스트 청크 분할
        chunks = chunk_text(page_text)
        
        # 각 청크를 Supabase에 저장
        for idx, chunk in enumerate(chunks):
            # 임베딩 생성
            embedding = generate_embedding(chunk)
            
            # 메타데이터 구성
            metadata = {
                "page_number": page_num,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "file_hash": file_hash,
                "document_type": file_info["category"],
                "has_fault_ratio": len(scenarios) > 0
            }
            
            # 시나리오가 있으면 메타데이터에 추가
            if scenarios:
                metadata["fault_scenarios"] = [
                    {
                        "offender_ratio": s["offender_ratio"],
                        "victim_ratio": s["victim_ratio"],
                        "ratio_text": s["ratio_text"]
                    }
                    for s in scenarios
                ]
            
            # 데이터 구조
            data = {
                "document_name": Path(file_info["path"]).name,
                "document_category": file_info["category"],
                "chunk_index": total_chunks,
                "content": chunk,
                "content_length": len(chunk),
                "embedding": embedding,
                "file_hash": file_hash,
                "metadata": metadata,
                "keywords": ["교통사고", "과실비율", "자동차사고", "보험"],
                "version": "2023"
            }
            
            try:
                # Supabase에 삽입
                result = supabase.table("gk_knowledge_base").insert(data).execute()
                total_chunks += 1
                
                if (total_chunks % 10) == 0:
                    print(f"   ⏳ {total_chunks}개 청크 저장 완료...")
                    
            except Exception as e:
                print(f"   ❌ 청크 저장 실패 (페이지 {page_num}, 청크 {idx}): {e}")
    
    print(f"\n   ✅ 총 {total_chunks}개 청크 저장 완료")
    print(f"   📊 추출된 과실비율 시나리오: {total_scenarios}개")
    
    # ═══════════════════════════════════════════════════════════════════
    # [POST-FLIGHT] 히스토리 영구 기록 (State Tracking)
    # ═══════════════════════════════════════════════════════════════════
    
    # 히스토리에 문서 정보 추가
    doc_record = {
        "file_hash": file_hash,
        "file_name": Path(file_info["path"]).name,
        "file_path": file_info["path"],
        "ingested_at": datetime.now().isoformat(),
        "chunk_count": total_chunks,
        "scenario_count": total_scenarios,
        "category": file_info["category"],
        "description": file_info.get("description", "")
    }
    
    history["documents"].append(doc_record)
    save_embedding_history(history)
    
    print(f"   💾 히스토리 기록 완료 → {HISTORY_FILE}")

def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("🚗 교통사고 과실비율 인정기준 RAG 인제스트 시작")
    print("=" * 80)
    
    ingest_pdf_file(PDF_FILE)
    
    print("\n" + "=" * 80)
    print("✅ PDF 파일 인제스트 완료")
    print("=" * 80)

if __name__ == "__main__":
    main()
