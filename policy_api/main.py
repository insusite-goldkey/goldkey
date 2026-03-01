"""
골드키 약관 RAG 업로드 API
FastAPI 백엔드 — Chrome Extension에서 가로챈 약관 PDF를 수신하여 GCS에 업로드합니다.

실행:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

환경변수 (.env 또는 시스템):
    API_KEY          : 확장 프로그램 인증 키 (임의의 긴 문자열)
    GCS_BUCKET       : GCS 버킷명 (예: goldkey-policy-rag)
    GCS_KEY_PATH     : 서비스 계정 키 JSON 경로 (Cloud Run에서는 ADC 사용)
    SUPABASE_URL     : (선택) Supabase URL (RAG 인제스트 시 필요)
    SUPABASE_KEY     : (선택) Supabase anon/service key
"""

import os
import logging
from typing import Optional

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gcs_uploader import upload_to_gcs
from rag_ingest import ingest_policy_document

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("policy_api")

app = FastAPI(
    title="골드키 약관 RAG 업로드 API",
    description="Chrome Extension이 가로챈 보험사 약관 PDF를 GCS에 업로드하고 RAG에 인제스트합니다.",
    version="1.0.0",
)

# ── CORS 설정 ──────────────────────────────────────────────────────────────
# Chrome Extension origin: chrome-extension://<EXTENSION_ID>
# 로컬 개발: http://localhost:* 허용
# 프로덕션 배포 시 ALLOWED_ORIGINS 환경변수로 제한하세요.
_raw_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "chrome-extension://,http://localhost:8000,http://127.0.0.1:8000"
)
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Extension ID가 확정되면 위 ALLOWED_ORIGINS로 교체
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# ── API 키 인증 헬퍼 ───────────────────────────────────────────────────────
_API_KEY = os.environ.get("API_KEY", "")

def _verify_api_key(x_api_key: Optional[str]) -> None:
    """X-API-Key 헤더 검증 — 키 미설정 시 개발 모드(경고만)"""
    if not _API_KEY:
        logger.warning("API_KEY 환경변수가 설정되지 않았습니다. 모든 요청을 허용합니다. (개발 모드)")
        return
    if x_api_key != _API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 API 키입니다.",
        )


# ── 엔드포인트 ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """서버 헬스체크 — Chrome Extension이 API 서버 연결 여부를 확인할 때 사용"""
    return {"status": "ok", "service": "goldkey-policy-api"}


@app.post("/api/upload-policy")
async def upload_policy(
    file: UploadFile = File(..., description="약관 PDF 파일"),
    source_url: str = Form("", description="원본 다운로드 URL (참고용)"),
    insurer: str = Form("", description="보험사명 (선택)"),
    doc_type: str = Form("보험약관", description="문서 유형"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """
    Chrome Extension에서 가로챈 약관 PDF를 수신하여 GCS에 업로드합니다.

    - **file**: multipart/form-data로 전송된 PDF
    - **source_url**: 원본 PDF URL (출처 추적용)
    - **insurer**: 보험사명 (예: 삼성화재, DB손보)
    - **doc_type**: 문서 유형 (기본값: 보험약관)
    - **X-API-Key**: 인증 헤더
    """
    _verify_api_key(x_api_key)

    # ── 파일 검증 ──────────────────────────────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    content_type = file.content_type or ""
    allowed_types = {"application/pdf", "application/octet-stream"}
    if content_type and content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"지원하지 않는 파일 형식: {content_type}. PDF만 허용됩니다.",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="빈 파일입니다.")

    max_size_mb = int(os.environ.get("MAX_FILE_MB", "50"))
    if len(file_bytes) > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기 초과 (최대 {max_size_mb}MB).",
        )

    logger.info(f"파일 수신: {file.filename} ({len(file_bytes)/1024:.1f}KB) | 출처: {source_url}")

    # ── GCS 업로드 ─────────────────────────────────────────────────────────
    try:
        gcs_result = upload_to_gcs(
            file_bytes=file_bytes,
            original_filename=file.filename,
            destination_folder="policies",
        )
    except Exception as e:
        logger.error(f"GCS 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"GCS 업로드 실패: {str(e)}")

    logger.info(f"GCS 업로드 완료: {gcs_result['gcs_uri']}")

    # ── RAG 인제스트 ───────────────────────────────────────────────────────
    rag_result = {"success": False, "message": "인제스트 생략"}
    try:
        rag_result = ingest_policy_document(
            gcs_uri=gcs_result["gcs_uri"],
            blob_name=gcs_result["blob_name"],
            original_filename=file.filename,
            file_bytes=file_bytes,
        )
    except Exception as e:
        logger.warning(f"RAG 인제스트 오류 (업로드는 성공): {e}")
        rag_result = {"success": False, "message": str(e)}

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": f"'{file.filename}' 업로드 완료",
            "gcs_uri": gcs_result["gcs_uri"],
            "blob_name": gcs_result["blob_name"],
            "size_bytes": gcs_result["size_bytes"],
            "source_url": source_url,
            "insurer": insurer,
            "doc_type": doc_type,
            "rag": rag_result,
        },
    )
