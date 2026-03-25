"""Cloud Run 카카오 발송 전담 라우터.

- DB 동의(consent_kakao*) 게이트 확인
- modules.kakao_sender 실발송 호출
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from head_api.dependencies import AuthContext, get_auth_context

router = APIRouter(
    prefix="/api/v1/kakao",
    tags=["kakao"],
    dependencies=[Depends(get_auth_context)],
)


class KakaoSendRequest(BaseModel):
    person_id: str = Field(..., min_length=1)
    report_type: str = "ai_report"
    payload: dict[str, Any] = Field(default_factory=dict)


def _db_consent_kakao(user_id: str, person_id: str) -> tuple[bool, dict[str, Any]]:
    """Cloud Run DB에서 고객 동의 필드 확인."""
    try:
        from db_utils import load_customers

        rows = load_customers(user_id, "")
        rec = next((r for r in rows if str(r.get("person_id", "")) == person_id), {})
        consent = bool(
            rec.get("consent_kakao")
            or rec.get("consent_kakao_report")
            or rec.get("kakao_consent_agreed")
        )
        return consent, rec if isinstance(rec, dict) else {}
    except Exception:
        return False, {}


@router.post("/send")
def send_kakao(body: KakaoSendRequest, auth: AuthContext = Depends(get_auth_context)) -> dict[str, Any]:
    uid = auth.user_id
    consent_ok, rec = _db_consent_kakao(uid, body.person_id)
    if not consent_ok:
        return {
            "ok": False,
            "error": "consent_kakao_required",
            "source": "cloud_run_db",
            "person_id": body.person_id,
            "user_id": uid,
        }

    phone = ""
    if isinstance(body.payload, dict):
        phone = str(body.payload.get("phone", "")).strip()
    if not phone:
        phone = str(rec.get("contact", "")).strip()

    message = ""
    if isinstance(body.payload, dict):
        message = str(body.payload.get("message", "")).strip()
    if not message:
        message = f"[골드키 AI] {body.report_type} 보고서가 준비되었습니다."

    send_result: dict[str, Any]
    try:
        from modules.kakao_sender import send_report

        send_result = send_report(
            phone=phone,
            message=message,
            title="골드키 AI 리포트",
        )
    except Exception as e:
        send_result = {"success": False, "code": "EXCEPTION", "msg": str(e)}

    return {
        "ok": bool(send_result.get("success")),
        "event_id": str(uuid4()),
        "status": "sent" if send_result.get("success") else "failed",
        "report_type": body.report_type,
        "delivery": send_result,
        "source": "modules.kakao_sender",
        "user_id": uid,
    }
