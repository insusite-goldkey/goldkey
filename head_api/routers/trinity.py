"""POST /api/v1/analyze/trinity — 트리니티 산출 (shared_components 단일 소스)."""
from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/analyze", tags=["analyze"])


class TrinityRequest(BaseModel):
    nhis_premium: int = Field(..., ge=0, le=500_000_000, description="월 건강보험료(원)")
    sub_type: Literal["workplace", "regional_general", "regional_retiree"] = "workplace"


@router.post("/trinity")
def post_trinity(body: TrinityRequest) -> dict[str, Any]:
    """트리니티 지표 산출 — 계산 SSOT는 shared_components.calculate_trinity_metrics."""
    try:
        from shared_components import calculate_trinity_metrics

        result = calculate_trinity_metrics(body.nhis_premium, body.sub_type)
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e), "result": None}
