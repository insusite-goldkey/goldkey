"""Cloud Run 운영 정책 라우터 (DB 기반, Stateless)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from head_api.dependencies import AuthContext, get_auth_context
from db_utils import _get_sb

router = APIRouter(
    prefix="/api/v1/ops",
    tags=["ops"],
    dependencies=[Depends(get_auth_context)],
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CustomerUpsertRequest(BaseModel):
    person_id: str = Field(..., min_length=1)
    patch: dict[str, Any] = Field(default_factory=dict)
    expected_version: int | None = None


class CustomerListRequest(BaseModel):
    query: str = ""
    include_deleted: bool = False


@router.post("/customer/upsert")
def upsert_customer(body: CustomerUpsertRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    """낙관적 락 + owner(agent_id)=auth.user_id 강제."""
    sb = _get_sb()
    if not sb:
        return {"ok": False, "error": "db_unavailable"}
    uid = auth.user_id
    try:
        rows = (
            sb.table("gk_people")
            .select("*")
            .eq("person_id", body.person_id)
            .eq("agent_id", uid)
            .limit(1)
            .execute()
            .data
            or []
        )
        if rows:
            cur = rows[0]
            cur_ver = int(cur.get("version", 1))
            if body.expected_version is not None and int(body.expected_version) != cur_ver:
                return {"ok": False, "conflict": True, "error": "version_conflict", "server_record": cur}
            payload = {**(body.patch or {})}
            payload["version"] = cur_ver + 1
            payload["updated_at"] = _utc_now()
            q = (
                sb.table("gk_people")
                .update(payload)
                .eq("person_id", body.person_id)
                .eq("agent_id", uid)
            )
            if body.expected_version is not None:
                q = q.eq("version", int(body.expected_version))
            data = q.execute().data or []
            if not data:
                rows2 = (
                    sb.table("gk_people")
                    .select("*")
                    .eq("person_id", body.person_id)
                    .eq("agent_id", uid)
                    .limit(1)
                    .execute()
                    .data
                    or []
                )
                return {"ok": False, "conflict": True, "error": "version_conflict", "server_record": rows2[0] if rows2 else None}
            return {"ok": True, "conflict": False, "record": data[0]}
        now = _utc_now()
        insert_payload = {
            "person_id": body.person_id,
            "agent_id": uid,
            "is_deleted": False,
            "version": 1,
            "created_at": now,
            "updated_at": now,
        }
        insert_payload.update(body.patch or {})
        data = sb.table("gk_people").insert(insert_payload).execute().data or []
        return {"ok": True, "conflict": False, "record": data[0] if data else insert_payload}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/customer/list")
def list_customers(body: CustomerListRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    sb = _get_sb()
    if not sb:
        return {"ok": False, "error": "db_unavailable"}
    uid = auth.user_id
    try:
        q = sb.table("gk_people").select("*").eq("agent_id", uid)
        if not body.include_deleted:
            q = q.eq("is_deleted", False)
        rows = q.order("updated_at", desc=True).limit(500).execute().data or []
        needle = (body.query or "").strip().lower()
        if needle:
            rows = [
                r
                for r in rows
                if needle
                in " ".join(
                    [
                        str(r.get("name", "")),
                        str(r.get("contact", "")),
                        str(r.get("job", "")),
                        str(r.get("address", "")),
                        str(r.get("memo", "")),
                    ]
                ).lower()
            ]
        return {"ok": True, "items": rows, "count": len(rows)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class CustomerSoftDeleteRequest(BaseModel):
    person_id: str = Field(..., min_length=1)
    expected_version: int | None = None


@router.post("/customer/soft-delete")
def soft_delete_customer(body: CustomerSoftDeleteRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    """물리 DELETE 금지: is_deleted=True."""
    return upsert_customer(
        CustomerUpsertRequest(
            person_id=body.person_id,
            patch={"is_deleted": True},
            expected_version=body.expected_version,
        ),
        auth=auth,
    )


class HandoffCreateRequest(BaseModel):
    person_id: str = Field(..., min_length=1)
    channel: str = "qr"


@router.post("/handoff/create")
def create_handoff(body: HandoffCreateRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    sb = _get_sb()
    if not sb:
        return {"ok": False, "error": "db_unavailable"}
    session_id = str(uuid4())
    rec: dict[str, Any] = {
        "session_id": session_id,
        "user_id": auth.user_id,
        "person_id": body.person_id,
        "channel": body.channel,
        "status": "pending",
        "consent_info_lookup": False,
        "consent_kakao_report": False,
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }
    try:
        data = sb.table("gk_handoff_sessions").insert(rec).execute().data or []
        return {"ok": True, "session": data[0] if data else rec}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/handoff/status/{session_id}")
def handoff_status(session_id: str, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    sb = _get_sb()
    if not sb:
        return {"ok": False, "error": "db_unavailable"}
    try:
        rows = (
            sb.table("gk_handoff_sessions")
            .select("*")
            .eq("session_id", session_id)
            .eq("user_id", auth.user_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            return {"ok": False, "error": "session_not_found"}
        return {"ok": True, "session": rows[0]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class HandoffCompleteRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    consent_info_lookup: bool = True
    consent_kakao_report: bool = False


@router.post("/handoff/complete")
def complete_handoff(body: HandoffCompleteRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    sb = _get_sb()
    if not sb:
        return {"ok": False, "error": "db_unavailable"}
    try:
        rows = (
            sb.table("gk_handoff_sessions")
            .select("*")
            .eq("session_id", body.session_id)
            .eq("user_id", auth.user_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            return {"ok": False, "error": "session_not_found"}
        rec = rows[0]
        upd = {
            "status": "completed",
            "consent_info_lookup": bool(body.consent_info_lookup),
            "consent_kakao_report": bool(body.consent_kakao_report),
            "updated_at": _utc_now(),
        }
        srows = (
            sb.table("gk_handoff_sessions")
            .update(upd)
            .eq("session_id", body.session_id)
            .eq("user_id", auth.user_id)
            .execute()
            .data
            or []
        )
        session = srows[0] if srows else {**rec, **upd}
        consent = {
            "user_id": auth.user_id,
            "person_id": rec.get("person_id", ""),
            "consent_info_lookup": bool(body.consent_info_lookup),
            "consent_kakao_report": bool(body.consent_kakao_report),
            "source_session_id": body.session_id,
            "updated_at": upd["updated_at"],
        }
        sb.table("gk_consents").upsert(consent, on_conflict="user_id,person_id").execute()
        return {"ok": True, "session": session, "consent": consent}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class KakaoSendRequest(BaseModel):
    person_id: str = Field(..., min_length=1)
    report_type: str = "ai_report"
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/kakao/send")
def send_kakao_with_consent(body: KakaoSendRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    """하위호환: 전용 카카오 라우터로 위임."""
    from head_api.routers.kakao import KakaoSendRequest as _KReq
    from head_api.routers.kakao import send_kakao as _send_kakao

    return _send_kakao(
        _KReq(
            user_id=auth.user_id,
            person_id=body.person_id,
            report_type=body.report_type,
            payload=body.payload,
        )
    )
