# -*- coding: utf-8 -*-
"""
RAG 트리거 API
GCS 업로드 감지 및 Supabase 벡터화 백그라운드 작업 시작

작성일: 2026-03-31
목적: Cloud Run 환경에서 GCS 트리거를 감지하고 RAG 벡터화 자동 실행
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json

# FastAPI
try:
    from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError:
    print("❌ fastapi 라이브러리가 설치되어 있지 않습니다.")
    print("pip install fastapi uvicorn 를 실행하세요.")
    raise

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# FastAPI 앱 초기화
app = FastAPI(
    title="Goldkey RAG Trigger API",
    description="GCS 업로드 감지 및 Supabase 벡터화 트리거",
    version="1.0.0"
)


# 요청 모델
class GCSUploadNotification(BaseModel):
    """GCS 업로드 알림 모델"""
    bucket: str
    name: str  # 파일 경로
    contentType: Optional[str] = None
    size: Optional[int] = None
    timeCreated: Optional[str] = None
    updated: Optional[str] = None
    generation: Optional[str] = None
    metageneration: Optional[str] = None


class ManualTriggerRequest(BaseModel):
    """수동 트리거 요청 모델"""
    file_path: str
    force: bool = False


# 벡터화 작업 함수
async def vectorize_document(
    bucket_name: str,
    file_path: str,
    metadata: Optional[Dict] = None
):
    """
    문서 벡터화 백그라운드 작업
    
    Args:
        bucket_name: GCS 버킷 이름
        file_path: 파일 경로
        metadata: 추가 메타데이터
    """
    print(f"\n{'='*70}")
    print(f"🚀 벡터화 작업 시작")
    print(f"{'='*70}")
    print(f"📦 버킷: {bucket_name}")
    print(f"📄 파일: {file_path}")
    print(f"⏰ 시작 시간: {datetime.now().isoformat()}")
    
    try:
        # 1. GCS에서 파일 다운로드
        print(f"\n📥 [1/5] GCS에서 파일 다운로드 중...")
        from google.cloud import storage
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        
        # 임시 파일로 다운로드
        temp_file_path = f"/tmp/{Path(file_path).name}"
        blob.download_to_filename(temp_file_path)
        print(f"✅ 다운로드 완료: {temp_file_path}")
        
        # 2. 문서 전처리 및 Chunking
        print(f"\n📄 [2/5] 문서 전처리 및 Chunking 중...")
        from hq_backend.services.document_processor import InsuranceDocumentProcessor
        
        processor = InsuranceDocumentProcessor(
            chunk_size=1000,
            chunk_overlap=150
        )
        
        chunks = processor.process_pdf(temp_file_path)
        print(f"✅ Chunking 완료: {len(chunks)}개 Chunk 생성")
        
        # 3. 임베딩 생성
        print(f"\n🧠 [3/5] 임베딩 생성 중...")
        import openai
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        openai.api_key = openai_api_key
        
        for idx, chunk in enumerate(chunks, 1):
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=chunk["content"]
            )
            chunk["embedding"] = response.data[0].embedding
            
            if idx % 10 == 0:
                print(f"  진행률: {idx}/{len(chunks)} ({idx/len(chunks)*100:.1f}%)")
        
        print(f"✅ 임베딩 생성 완료: {len(chunks)}개")
        
        # 4. Supabase에 저장
        print(f"\n💾 [4/5] Supabase에 저장 중...")
        from supabase import create_client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL 또는 SUPABASE_SERVICE_KEY 환경 변수가 설정되지 않았습니다.")
        
        supabase = create_client(supabase_url, supabase_key)
        
        for idx, chunk in enumerate(chunks, 1):
            data = {
                "document_name": chunk.get("document_name"),
                "document_category": "보험카탈로그",
                "chunk_index": chunk.get("chunk_index"),
                "content": chunk.get("content"),
                "content_length": chunk.get("content_length"),
                "embedding": chunk.get("embedding"),
                "company": chunk.get("company"),
                "reference_date": chunk.get("reference_date"),
                "source": "GCS",
                "gcs_path": file_path
            }
            
            supabase.table("gk_knowledge_base").insert(data).execute()
            
            if idx % 10 == 0:
                print(f"  진행률: {idx}/{len(chunks)} ({idx/len(chunks)*100:.1f}%)")
        
        print(f"✅ Supabase 저장 완료: {len(chunks)}개")
        
        # 5. 임시 파일 삭제
        print(f"\n🗑️  [5/5] 임시 파일 정리 중...")
        os.remove(temp_file_path)
        print(f"✅ 정리 완료")
        
        print(f"\n{'='*70}")
        print(f"🎉 벡터화 작업 완료")
        print(f"{'='*70}")
        print(f"📄 파일: {file_path}")
        print(f"📊 총 Chunk 수: {len(chunks)}")
        print(f"⏰ 완료 시간: {datetime.now().isoformat()}")
        
    except Exception as e:
        print(f"\n❌ 벡터화 작업 실패: {e}")
        import traceback
        traceback.print_exc()
        raise


# API 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Goldkey RAG Trigger API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/trigger/gcs-upload")
async def trigger_gcs_upload(
    notification: GCSUploadNotification,
    background_tasks: BackgroundTasks
):
    """
    GCS 업로드 트리거 엔드포인트
    
    Cloud Storage Pub/Sub 알림을 수신하여 벡터화 작업 시작
    
    Args:
        notification: GCS 업로드 알림
        background_tasks: FastAPI 백그라운드 작업
    
    Returns:
        JSONResponse: 작업 시작 응답
    """
    print(f"\n{'='*70}")
    print(f"📨 GCS 업로드 알림 수신")
    print(f"{'='*70}")
    print(f"📦 버킷: {notification.bucket}")
    print(f"📄 파일: {notification.name}")
    print(f"📏 크기: {notification.size} bytes")
    print(f"⏰ 생성 시간: {notification.timeCreated}")
    
    # PDF 파일만 처리
    if not notification.name.lower().endswith('.pdf'):
        print(f"⏭️  건너뜀: PDF 파일이 아님")
        return JSONResponse(
            status_code=200,
            content={
                "status": "skipped",
                "reason": "Not a PDF file",
                "file": notification.name
            }
        )
    
    # 백그라운드 작업 추가
    background_tasks.add_task(
        vectorize_document,
        bucket_name=notification.bucket,
        file_path=notification.name,
        metadata={
            "contentType": notification.contentType,
            "size": notification.size,
            "timeCreated": notification.timeCreated
        }
    )
    
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "message": "벡터화 작업이 백그라운드에서 시작되었습니다.",
            "file": notification.name,
            "bucket": notification.bucket
        }
    )


@app.post("/trigger/manual")
async def trigger_manual(
    request: ManualTriggerRequest,
    background_tasks: BackgroundTasks
):
    """
    수동 트리거 엔드포인트
    
    특정 파일에 대해 수동으로 벡터화 작업 시작
    
    Args:
        request: 수동 트리거 요청
        background_tasks: FastAPI 백그라운드 작업
    
    Returns:
        JSONResponse: 작업 시작 응답
    """
    print(f"\n{'='*70}")
    print(f"🖐️  수동 트리거 요청 수신")
    print(f"{'='*70}")
    print(f"📄 파일: {request.file_path}")
    print(f"🔄 강제 실행: {request.force}")
    
    # 백그라운드 작업 추가
    background_tasks.add_task(
        vectorize_document,
        bucket_name="goldkey-knowledge-base",
        file_path=request.file_path
    )
    
    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "message": "벡터화 작업이 백그라운드에서 시작되었습니다.",
            "file": request.file_path
        }
    )


@app.post("/webhook/gcs")
async def webhook_gcs(request: Request):
    """
    GCS Pub/Sub Webhook 엔드포인트
    
    Cloud Storage Pub/Sub 메시지를 수신
    
    Args:
        request: HTTP 요청
    
    Returns:
        JSONResponse: 응답
    """
    try:
        # Pub/Sub 메시지 파싱
        envelope = await request.json()
        
        if "message" not in envelope:
            raise HTTPException(status_code=400, detail="Invalid Pub/Sub message")
        
        message = envelope["message"]
        
        # Base64 디코딩
        import base64
        data = json.loads(base64.b64decode(message["data"]).decode("utf-8"))
        
        print(f"\n{'='*70}")
        print(f"📨 Pub/Sub 메시지 수신")
        print(f"{'='*70}")
        print(f"📦 버킷: {data.get('bucket')}")
        print(f"📄 파일: {data.get('name')}")
        
        # GCS 업로드 알림으로 변환
        notification = GCSUploadNotification(
            bucket=data.get("bucket"),
            name=data.get("name"),
            contentType=data.get("contentType"),
            size=data.get("size"),
            timeCreated=data.get("timeCreated"),
            updated=data.get("updated")
        )
        
        # 백그라운드 작업 시작
        background_tasks = BackgroundTasks()
        return await trigger_gcs_upload(notification, background_tasks)
    
    except Exception as e:
        print(f"❌ Webhook 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 앱 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    print("\n" + "="*70)
    print("🚀 Goldkey RAG Trigger API 시작")
    print("="*70)
    print(f"⏰ 시작 시간: {datetime.now().isoformat()}")
    print(f"🌍 환경: {os.getenv('K_SERVICE', 'local')}")
    print("="*70 + "\n")


# 앱 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 실행"""
    print("\n" + "="*70)
    print("🛑 Goldkey RAG Trigger API 종료")
    print("="*70)
    print(f"⏰ 종료 시간: {datetime.now().isoformat()}")
    print("="*70 + "\n")


if __name__ == "__main__":
    import uvicorn
    
    # 로컬 개발 서버 실행
    uvicorn.run(
        "rag_trigger_api:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )
