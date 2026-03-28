"""
HEAD API 통합 헬스체크 스크립트.

검증 항목:
1) gk_people version/updated_at 증가
2) handoff 생성/완료/상태 전이
3) kakao 동의 게이트 차단(consent 없을 때)

실행:
  python scripts/test_head_api.py
"""
from __future__ import annotations

import hmac
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid


HEAD_HOST = os.environ.get("HEAD_TEST_HOST", "127.0.0.1")
HEAD_PORT = int(os.environ.get("HEAD_TEST_PORT", "8811"))
BASE = f"http://{HEAD_HOST}:{HEAD_PORT}"
UID = os.environ.get("HEAD_API_USER_ID", "").strip() or "ADMIN_MASTER"
SECRET = os.environ.get("ENCRYPTION_KEY", "GoldKey_System_Encrypt_Master_2026_@#$")
SKIP_BOOT = os.environ.get("HEAD_TEST_SKIP_BOOT", "").strip().lower() in ("1", "true", "yes", "on")


def _token() -> str:
    ts = int(time.time())
    sig = hmac.new(SECRET.encode(), f"{UID}.{ts}".encode(), "sha256").hexdigest()[:32]
    return f"{UID}.{ts}.{sig}"


def _request(path: str, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = None
    headers = {"Authorization": f"Bearer {_token()}"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(f"{BASE}{path}", method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.getcode(), json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw}
    except Exception as e:
        return 0, {"error": str(e)}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    proc = None
    results: dict[str, dict] = {}
    try:
        if not SKIP_BOOT:
            proc = subprocess.Popen(
                ["python", "-m", "uvicorn", "head_api.main:app", "--host", HEAD_HOST, "--port", str(HEAD_PORT)],
                cwd=r"d:\CascadeProjects",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            time.sleep(2.5)

        code, body = _request("/health", "GET")
        results["health"] = {"code": code, "body": body}
        _assert(code == 200 and body.get("status") == "ok", "health check failed")

        person_id = "hc_" + uuid.uuid4().hex[:12]
        code, up1 = _request(
            "/api/v1/ops/customer/upsert",
            "POST",
            {"person_id": person_id, "patch": {"name": "헬스체크", "contact": "01000000000"}},
        )
        results["customer_upsert_1"] = {"code": code, "body": up1}
        _assert(code == 200 and up1.get("ok") is True and isinstance(up1.get("record"), dict), "customer_upsert_1 failed")
        rec1 = up1["record"]
        v1 = rec1.get("version")
        t1 = rec1.get("updated_at")
        _assert(isinstance(v1, int), "version missing after first upsert")

        time.sleep(1)
        code, up2 = _request(
            "/api/v1/ops/customer/upsert",
            "POST",
            {"person_id": person_id, "patch": {"memo": "v2"}, "expected_version": v1},
        )
        results["customer_upsert_2"] = {"code": code, "body": up2}
        _assert(code == 200 and up2.get("ok") is True and isinstance(up2.get("record"), dict), "customer_upsert_2 failed")
        rec2 = up2["record"]
        v2 = rec2.get("version")
        t2 = rec2.get("updated_at")
        _assert(v2 == v1 + 1, f"version did not increment: {v1} -> {v2}")
        _assert(t1 != t2, "updated_at did not change")

        code, hc = _request(
            "/api/v1/ops/handoff/create",
            "POST",
            {"person_id": person_id, "channel": "qr"},
        )
        results["handoff_create"] = {"code": code, "body": hc}
        _assert(code == 200 and hc.get("ok") is True and isinstance(hc.get("session"), dict), "handoff create failed")
        session_id = hc["session"].get("session_id", "")
        _assert(bool(session_id), "handoff session_id missing")

        code, hs1 = _request(f"/api/v1/ops/handoff/status/{session_id}", "GET")
        results["handoff_status_initial"] = {"code": code, "body": hs1}
        _assert(code == 200 and hs1.get("ok") is True, "handoff status initial failed")
        _assert(((hs1.get("session") or {}).get("status") == "pending"), "handoff initial status is not pending")

        code, hcomp = _request(
            "/api/v1/ops/handoff/complete",
            "POST",
            {"session_id": session_id, "consent_info_lookup": True, "consent_kakao_report": False},
        )
        results["handoff_complete"] = {"code": code, "body": hcomp}
        _assert(code == 200 and hcomp.get("ok") is True, "handoff complete failed")

        code, hs2 = _request(f"/api/v1/ops/handoff/status/{session_id}", "GET")
        results["handoff_status_after"] = {"code": code, "body": hs2}
        _assert(code == 200 and hs2.get("ok") is True, "handoff status after failed")
        _assert(((hs2.get("session") or {}).get("status") == "completed"), "handoff final status is not completed")

        code, kakao = _request(
            "/api/v1/kakao/send",
            "POST",
            {"person_id": person_id, "report_type": "ai_report", "payload": {"message": "hello"}},
        )
        results["kakao_gate"] = {"code": code, "body": kakao}
        _assert(code == 200 and kakao.get("ok") is False and kakao.get("error") == "consent_kakao_required", "kakao consent gate failed")

        print(json.dumps({"ok": True, "results": results}, ensure_ascii=False, indent=2))
        return 0
    except AssertionError as e:
        print(json.dumps({"ok": False, "assertion": str(e), "results": results}, ensure_ascii=False, indent=2))
        return 1
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e), "results": results}, ensure_ascii=False, indent=2))
        return 1
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()


if __name__ == "__main__":
    sys.exit(main())
