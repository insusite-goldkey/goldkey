"""
HQ / CRM → HEAD API REST 클라이언트 (urllib — 추가 의존성 없음).

환경변수:
  HEAD_API_URL — 기본 http://127.0.0.1:8800
  HEAD_API_LOCAL_FALLBACK — 1/true 시 API 실패 시 로컬 shared_components로 재계산 (개발용)
"""
from __future__ import annotations

import json
import hmac
import os
import time
import base64
import urllib.error
import urllib.request


def get_head_api_base() -> str:
    return os.environ.get("HEAD_API_URL", "http://127.0.0.1:8800").strip().rstrip("/")


def _local_fallback_enabled() -> bool:
    v = os.environ.get("HEAD_API_LOCAL_FALLBACK", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _build_bearer_token() -> str:
    uid = os.environ.get("HEAD_API_USER_ID", "").strip()
    if not uid:
        return ""
    ts = int(time.time())
    secret = os.environ.get("ENCRYPTION_KEY", "GoldKey_System_Encrypt_Master_2026_@#$")
    sig = hmac.new(secret.encode(), f"{uid}.{ts}".encode(), "sha256").hexdigest()[:32]
    return f"{uid}.{ts}.{sig}"


def _auth_headers() -> dict[str, str]:
    tok = _build_bearer_token()
    if not tok:
        return {}
    return {"Authorization": f"Bearer {tok}"}


def _post_json(path: str, payload: dict, timeout: float = 20.0) -> dict:
    base = get_head_api_base()
    url = f"{base}{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            **_auth_headers(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception as ex:
            return {"ok": False, "error": f"http_{e.code}", "detail": str(ex)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _get_json(path: str, timeout: float = 20.0) -> dict:
    base = get_head_api_base()
    url = f"{base}{path}"
    req = urllib.request.Request(url, method="GET", headers=_auth_headers())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception as ex:
            return {"ok": False, "error": f"http_{e.code}", "detail": str(ex)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def fetch_trinity_metrics(nhis_premium: int, sub_type: str = "workplace", timeout: float = 25.0) -> dict:
    """
    POST /api/v1/analyze/trinity
    Returns calculate_trinity_metrics와 동일한 dict.
    """
    base = get_head_api_base()
    url = f"{base}/api/v1/analyze/trinity"
    payload = json.dumps(
        {"nhis_premium": int(nhis_premium), "sub_type": sub_type},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            **_auth_headers(),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            raw = json.loads(e.read().decode())
        except Exception:
            raw = {"ok": False, "error": f"HTTP {e.code}"}
        if _local_fallback_enabled():
            return _trinity_local(nhis_premium, sub_type)
        if not raw.get("ok", True):
            raise RuntimeError(raw.get("error", f"HEAD API HTTP {e.code}"))
        r = raw.get("result")
        if isinstance(r, dict):
            return r
        raise RuntimeError(raw.get("error", f"HEAD API HTTP {e.code}"))
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        if _local_fallback_enabled():
            return _trinity_local(nhis_premium, sub_type)
        raise RuntimeError(
            f"HEAD API에 연결할 수 없습니다 ({base}). "
            f"uvicorn head_api.main:app --host 0.0.0.0 --port 8800 실행 여부를 확인하세요. ({e})"
        ) from e

    if not raw.get("ok"):
        if _local_fallback_enabled():
            return _trinity_local(nhis_premium, sub_type)
        raise RuntimeError(raw.get("error", "HEAD API returned ok=false"))

    out = raw.get("result")
    if not isinstance(out, dict):
        raise RuntimeError("HEAD API: invalid result shape")
    return out


def _trinity_local(nhis_premium: int, sub_type: str) -> dict:
    from shared_components import calculate_trinity_metrics

    return calculate_trinity_metrics(int(nhis_premium), sub_type)


def create_handoff_session(user_id: str, person_id: str, channel: str = "qr") -> dict:
    return _post_json(
        "/api/v1/ops/handoff/create",
        {"user_id": user_id, "person_id": person_id, "channel": channel},
    )


def get_handoff_status(session_id: str) -> dict:
    return _get_json(f"/api/v1/ops/handoff/status/{session_id}")


def complete_handoff_session(
    session_id: str, *, consent_info_lookup: bool = True, consent_kakao_report: bool = False
) -> dict:
    return _post_json(
        "/api/v1/ops/handoff/complete",
        {
            "session_id": session_id,
            "consent_info_lookup": consent_info_lookup,
            "consent_kakao_report": consent_kakao_report,
        },
    )


def request_kakao_send(user_id: str, person_id: str, report_type: str = "ai_report", payload: dict | None = None) -> dict:
    return _post_json(
        "/api/v1/kakao/send",
        {
            "user_id": user_id,
            "person_id": person_id,
            "report_type": report_type,
            "payload": payload or {},
        },
    )


def upsert_customer_record(
    *,
    user_id: str,
    person_id: str,
    patch: dict,
    expected_version: int | None = None,
) -> dict:
    return _post_json(
        "/api/v1/ops/customer/upsert",
        {
            "user_id": user_id,
            "person_id": person_id,
            "patch": patch or {},
            "expected_version": expected_version,
        },
    )


def list_customer_records(*, user_id: str, query: str = "", include_deleted: bool = False) -> dict:
    return _post_json(
        "/api/v1/ops/customer/list",
        {
            "user_id": user_id,
            "query": query,
            "include_deleted": include_deleted,
        },
    )


def trigger_reanalyze_report(
    *,
    user_id: str,
    person_id: str,
    source: str = "scan_upload",
    scan_file_names: list[str] | None = None,
) -> dict:
    return _post_json(
        "/api/v1/reports/reanalyze",
        {
            "agent_id": user_id,
            "person_id": person_id,
            "source": source,
            "scan_file_names": scan_file_names or [],
        },
    )


def fetch_unified_report(
    *,
    user_id: str,
    person_id: str,
    include_kb: bool = True,
    include_trinity: bool = True,
    include_scan: bool = True,
    include_nibo: bool = True,
) -> dict:
    return _post_json(
        "/api/v1/reports/unified",
        {
            "agent_id": user_id,
            "person_id": person_id,
            "include_kb": include_kb,
            "include_trinity": include_trinity,
            "include_scan": include_scan,
            "include_nibo": include_nibo,
        },
    )


def preprocess_scan_image(
    *,
    user_id: str,
    person_id: str,
    image_bytes: bytes,
    source: str = "camera",
    filename: str = "capture.jpg",
) -> dict:
    _ = user_id  # auth는 Bearer token의 HEAD_API_USER_ID를 사용
    if not image_bytes:
        return {"ok": False, "error": "empty_image"}
    return _post_json(
        "/api/v1/scan/preprocess",
        {
            "person_id": person_id,
            "image_b64": base64.b64encode(image_bytes).decode(),
            "source": source,
            "filename": filename,
        },
        timeout=40.0,
    )
