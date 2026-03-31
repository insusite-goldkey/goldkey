# -*- coding: utf-8 -*-
"""
이달의 상품 API
보험 리플릿 자동 처리 및 마케팅 포인트 조회

작성일: 2026-03-31
목적: 매월 신규 리플릿 입력 시 자동 트리거 및 프론트엔드 데이터 제공
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

try:
    from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError:
    print("❌ fastapi 라이브러리가 설치되어 있지 않습니다.")
    raise

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from hq_backend.services.document_hash_validator import DocumentHashValidator
    from hq_backend.services.marketing_point_extractor import MarketingPointExtractor
    from hq_backend.services.document_processor import InsuranceDocumentProcessor
    from hq_backend.utils.folder_manager import FolderManager
    from supabase import create_client
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    raise


# API Router 초기화
router = APIRouter(
    prefix="/monthly-product",
    tags=["monthly-product"]
)


# 요청/응답 모델
class ProcessLeafletRequest(BaseModel):
    """리플릿 처리 요청"""
    company: str
    year: Optional[int] = None
    month: Optional[int] = None


class MarketingPoint(BaseModel):
    """마케팅 포인트"""
    company: str
    company_type: str
    marketing_point: str
    priority: int


class MonthlyProductResponse(BaseModel):
    """이달의 상품 응답"""
    year: int
    month: int
    non_life_insurance: List[MarketingPoint]  # 손해보험
    life_insurance: List[MarketingPoint]  # 생명보험
    total_count: int


# 백그라운드 작업: 리플릿 처리
async def process_leaflet_background(
    file_path: str,
    company: str,
    year: int,
    month: int
):
    """
    리플릿 처리 백그라운드 작업
    
    1. 중복 검증 (SHA-256)
    2. PDF 텍스트 추출
    3. LLM 마케팅 포인트 추출
    4. Supabase 저장
    """
    print(f"\n{'='*70}")
    print(f"📄 리플릿 처리 시작: {company} ({year}년 {month}월)")
    print(f"{'='*70}")
    
    try:
        # 1. 중복 검증
        print(f"\n🔒 [1/4] 중복 검증 중...")
        validator = DocumentHashValidator()
        validation_result = validator.validate_and_register(
            file_path=file_path,
            company=company,
            reference_date=f"{year}-{month:02d}"
        )
        
        print(validation_result["message"])
        
        if validation_result["is_duplicate"]:
            print("⚠️ 중복 문서입니다. 처리를 중단합니다.")
            return
        
        # 2. PDF 텍스트 추출
        print(f"\n📄 [2/4] PDF 텍스트 추출 중...")
        processor = InsuranceDocumentProcessor()
        text = processor.extract_text_from_pdf(file_path)
        print(f"✅ 텍스트 추출 완료: {len(text)}자")
        
        # 3. LLM 마케팅 포인트 추출
        print(f"\n🤖 [3/4] LLM 마케팅 포인트 추출 중...")
        extractor = MarketingPointExtractor()
        result = extractor.process_leaflet(
            text=text,
            company=company,
            year=year,
            month=month,
            max_points=3
        )
        
        if result["success"]:
            print(f"✅ 마케팅 포인트 추출 완료: {len(result['points'])}개")
        else:
            print(f"❌ 마케팅 포인트 추출 실패: {result['message']}")
        
        # 4. 로그 기록
        print(f"\n📝 [4/4] 로그 기록 중...")
        log_data = {
            "company": company,
            "year": year,
            "month": month,
            "file_path": file_path,
            "file_hash": validation_result["file_hash"],
            "points_extracted": len(result.get("points", [])),
            "status": "success" if result["success"] else "failed",
            "processed_at": datetime.now().isoformat()
        }
        
        # Supabase 로그 테이블에 저장
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        supabase.table("leaflet_processing_logs").insert(log_data).execute()
        
        print(f"✅ 로그 기록 완료")
        
        print(f"\n{'='*70}")
        print(f"🎉 리플릿 처리 완료")
        print(f"{'='*70}")
    
    except Exception as e:
        print(f"\n❌ 리플릿 처리 실패: {e}")
        import traceback
        traceback.print_exc()


@router.get("/", response_model=MonthlyProductResponse)
async def get_monthly_products(
    year: Optional[int] = None,
    month: Optional[int] = None
):
    """
    이달의 상품 조회
    
    손해보험 7개, 생명보험 3개 우선순위 순으로 반환
    
    Args:
        year: 조회 연도 (기본값: 현재)
        month: 조회 월 (기본값: 현재)
    
    Returns:
        MonthlyProductResponse: 이달의 상품 데이터
    """
    if year is None or month is None:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    try:
        # Supabase RPC 함수 호출
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        
        result = supabase.rpc(
            "get_monthly_marketing_points",
            {
                "target_year": year,
                "target_month": month,
                "limit_count": 10  # 손해보험 7개 + 생명보험 3개
            }
        ).execute()
        
        # 데이터 분류
        non_life = []
        life = []
        
        for row in result.data:
            point = MarketingPoint(
                company=row["company"],
                company_type=row["company_type"],
                marketing_point=row["marketing_point"],
                priority=row["priority"]
            )
            
            if row["company_type"] == "손해보험" and len(non_life) < 7:
                non_life.append(point)
            elif row["company_type"] == "생명보험" and len(life) < 3:
                life.append(point)
        
        return MonthlyProductResponse(
            year=year,
            month=month,
            non_life_insurance=non_life,
            life_insurance=life,
            total_count=len(non_life) + len(life)
        )
    
    except Exception as e:
        print(f"❌ 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-leaflet")
async def process_leaflet(
    file: UploadFile = File(...),
    company: str = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    background_tasks: BackgroundTasks = None
):
    """
    리플릿 업로드 및 처리
    
    Args:
        file: PDF 파일
        company: 보험사명
        year: 적용 연도
        month: 적용 월
        background_tasks: 백그라운드 작업
    
    Returns:
        JSONResponse: 처리 시작 응답
    """
    if not company:
        raise HTTPException(status_code=400, detail="보험사명이 필요합니다.")
    
    if year is None or month is None:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    try:
        # 1. 폴더 생성
        folder_manager = FolderManager()
        folder_path = folder_manager.create_insurance_leaflet_folder(
            company_name=company,
            year=year,
            month=month
        )
        
        # 2. 파일 저장
        file_path = folder_path / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 3. 백그라운드 작업 추가
        background_tasks.add_task(
            process_leaflet_background,
            file_path=str(file_path),
            company=company,
            year=year,
            month=month
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "message": "리플릿 처리가 백그라운드에서 시작되었습니다.",
                "company": company,
                "year": year,
                "month": month,
                "file_name": file.filename
            }
        )
    
    except Exception as e:
        print(f"❌ 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# 앱 시작 이벤트
@router.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    print("\n" + "="*70)
    print("🚀 이달의 상품 API 시작")
    print("="*70)
    print(f"⏰ 시작 시간: {datetime.now().isoformat()}")
    print("="*70 + "\n")
