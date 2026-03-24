# modules/hq_analysis_api.py — HQ(goldkey-ai) 전용 REST 브리지
"""
증권/정밀 분석 UI는 app.py(Streamlit)가 담당하고,
CRM이 동일 Cloud Run 서비스로 먼저 API를 호출할 때 사용하는 얇은 엔드포인트.

실행: uvicorn modules.hq_analysis_api:app (내부 포트, nginx 뒤에서 /api/v1 로 프록시)
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


def _cors_origins() -> list[str]:
    raw = os.environ.get("HQ_API_CORS_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    crm = os.environ.get("CRM_APP_URL", "").strip()
    if crm:
        return [crm.rstrip("/")]
    return ["*"]


app = FastAPI(title="Goldkey HQ Analysis Bridge", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisTriggerBody(BaseModel):
    person_id: str = Field(..., min_length=1)
    agent_id: str = ""
    user_id: str = ""
    sector: str = "home"


def _verify_bridge(x_gk_bridge_key: Optional[str] = Header(None)) -> None:
    exp = os.environ.get("GK_ANALYSIS_BRIDGE_SECRET", "").strip()
    if not exp:
        return
    if (x_gk_bridge_key or "").strip() != exp:
        raise HTTPException(status_code=401, detail="invalid_bridge_key")


@app.get("/api/v1/health")
def health() -> dict:
    return {"ok": True, "service": "goldkey-ai-analysis-bridge", "version": "1.0.0"}


@app.post("/api/v1/analysis/trigger", dependencies=[Depends(_verify_bridge)])
def analysis_trigger(body: AnalysisTriggerBody) -> dict:
    """
    person_id 기준으로 HQ Streamlit 딥링크를 생성해 반환.
    실제 분석 파이프라인은 HQ UI(app.py)에서 수행.
    """
    try:
        from shared_components import build_deeplink_to_hq, resolve_hq_app_url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"shared_components_import:{e}") from e

    try:
        deeplink = build_deeplink_to_hq(
            cid=body.person_id,
            agent_id=body.agent_id or "",
            sector=body.sector or "home",
            user_id=body.user_id or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return {
        "ok": True,
        "person_id": body.person_id,
        "sector": body.sector,
        "hq_app_url": resolve_hq_app_url(),
        "hq_deeplink": deeplink,
        "hint": "Open hq_deeplink in browser for full HQ analysis UI.",
    }
