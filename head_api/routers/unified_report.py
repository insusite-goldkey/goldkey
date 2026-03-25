"""통합 AI 보고서 파이프라인 (DB 기반, Stateless)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from head_api.dependencies import AuthContext, get_auth_context
from db_utils import _get_sb

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["reports"],
    dependencies=[Depends(get_auth_context)],
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UnifiedReportRequest(BaseModel):
    person_id: str = Field(..., min_length=1, description="피보험자 person_id")
    include_kb: bool = True
    include_trinity: bool = True
    include_scan: bool = False
    include_nibo: bool = False
    trigger_reanalyze: bool = False


@router.post("/unified")
def post_unified_report(body: UnifiedReportRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    """단일 JSON(섹션별 KB/트리니티/스캔/NIBO) 반환."""
    sb = _get_sb()
    if not sb:
        return {"ok": False, "error": "db_unavailable"}
    uid = auth.user_id
    rows = (
        sb.table("gk_unified_reports")
        .select("*")
        .eq("agent_id", uid)
        .eq("person_id", body.person_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        cached = {
            "person_id": body.person_id,
            "agent_id": uid,
            "updated_at": _now(),
            "version": 1,
            "sections": {
                "kb": {"note": "KB 손보 스코어 — 미연동"},
                "trinity": {"note": "트리니티 — 미연동"},
                "scan": {"note": "스캔 파일 — 미연동"},
                "nibo": {"note": "NIBO JSON — 미연동"},
            },
        }
        sb.table("gk_unified_reports").upsert(cached, on_conflict="agent_id,person_id").execute()
    else:
        cached = rows[0]
    sections = cached.get("sections", {})
    filtered = {
        "kb": None if not body.include_kb else sections.get("kb"),
        "trinity": None if not body.include_trinity else sections.get("trinity"),
        "scan": None if not body.include_scan else sections.get("scan"),
        "nibo": None if not body.include_nibo else sections.get("nibo"),
    }
    return {
        "ok": True,
        "status": "ready",
        "person_id": body.person_id,
        "agent_id": uid,
        "updated_at": cached.get("updated_at"),
        "version": cached.get("version", 1),
        "sections": filtered,
        "message": "Unified report ready",
    }


class ReanalyzeRequest(BaseModel):
    person_id: str = Field(..., min_length=1)
    source: Literal["scan_upload", "manual"] = "scan_upload"
    scan_file_names: list[str] = Field(default_factory=list)


@router.post("/reanalyze")
def post_reanalyze_after_scan(body: ReanalyzeRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    """추가계약 스캔 후 재분석 트리거."""
    sb = _get_sb()
    if not sb:
        return {"ok": False, "error": "db_unavailable"}
    uid = auth.user_id
    rows = (
        sb.table("gk_unified_reports")
        .select("*")
        .eq("agent_id", uid)
        .eq("person_id", body.person_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    cur = rows[0] if rows else {"version": 0}
    nv = int(cur.get("version", 0)) + 1
    updated = {
        "person_id": body.person_id,
        "agent_id": uid,
        "updated_at": _now(),
        "version": nv,
        "sections": {
            "kb": {"status": "queued_reanalyze", "source": body.source, "version": nv},
            "trinity": {"status": "queued_reanalyze", "source": body.source, "version": nv},
            "scan": {
                "status": "uploaded",
                "files": body.scan_file_names,
                "count": len(body.scan_file_names),
                "version": nv,
            },
            "nibo": {"status": "linked", "version": nv},
        },
    }
    sb.table("gk_unified_reports").upsert(updated, on_conflict="agent_id,person_id").execute()
    return {
        "ok": True,
        "status": "queued",
        "person_id": body.person_id,
        "agent_id": uid,
        "source": body.source,
        "version": updated["version"],
        "updated_at": updated["updated_at"],
        "message": "Re-analyze queued; fetch /unified to refresh sections",
    }
