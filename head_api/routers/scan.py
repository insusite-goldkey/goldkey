"""실시간 스마트 스캔 라우터 (Image Guard)."""
from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from head_api.dependencies import AuthContext, get_auth_context
from head_api.image_guard import run_image_guard

router = APIRouter(
    prefix="/api/v1/scan",
    tags=["scan"],
    dependencies=[Depends(get_auth_context)],
)


class PreprocessRequest(BaseModel):
    person_id: str = Field(..., min_length=1)
    image_b64: str = Field(..., min_length=8)
    source: str = "camera"
    filename: str = "capture.jpg"


@router.post("/preprocess")
def preprocess_scan(body: PreprocessRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    try:
        img_bytes = base64.b64decode(body.image_b64.encode(), validate=False)
    except Exception:
        return {"ok": False, "error": "invalid_base64"}

    out = run_image_guard(img_bytes, agent_id=auth.user_id, person_id=body.person_id)
    if not out.ok and out.reason == "low_quality":
        return {
            "ok": False,
            "status": "retry_required",
            "quality_score": out.quality_score,
            "guide": "이미지가 너무 어둡거나 반사가 심합니다. 다시 촬영해 주세요.",
            "meta": out.meta,
        }
    if not out.ok:
        return {"ok": False, "error": out.reason, "meta": out.meta}
    return {
        "ok": True,
        "status": "ready",
        "quality_score": out.quality_score,
        "processed_image_b64": out.processed_b64,
        "gcs_uri": out.gcs_uri,
        "meta": out.meta,
        "source": body.source,
        "filename": body.filename,
    }
