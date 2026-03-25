"""
GoldKey HEAD API — FastAPI 진입점.

실행 (프로젝트 루트에서):
  uvicorn head_api.main:app --host 0.0.0.0 --port 8800

환경:
  HEAD_API_URL — BODY 쪽에서 사용 (기본 http://127.0.0.1:8800)
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from head_api.routers.kakao import router as kakao_router
from head_api.routers.operations import router as operations_router
from head_api.routers.scan import router as scan_router
from head_api.routers.trinity import router as trinity_router
from head_api.routers.unified_report import router as unified_report_router

app = FastAPI(
    title="GoldKey HEAD API",
    description="중앙 사령부 — HQ/CRM/모바일이 호출하는 REST 엔드포인트",
    version="0.1.0",
)

_cors_raw = os.environ.get("CORS_ALLOW_ORIGINS", "").strip()
if _cors_raw:
    _cors_origins = [x.strip() for x in _cors_raw.split(",") if x.strip()]
else:
    _cors_origins = ["http://localhost:8501", "http://localhost:8502"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trinity_router)
app.include_router(unified_report_router)
app.include_router(operations_router)
app.include_router(kakao_router)
app.include_router(scan_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "head_api"}
