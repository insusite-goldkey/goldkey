#!/usr/bin/env python3
"""
HQ/CRM 연결 상태 스모크 테스트.

검증 항목:
1) HQ 초기 화면(HTML) 응답
2) HQ API health 응답
3) CRM 초기 화면(HTML) 응답
4) (선택) CRM→HQ 브리지 트리거 API 응답

실행:
  python hq_crm_smoke_test.py
  python hq_crm_smoke_test.py --person-id P123 --agent-id A123 --user-id U123 --sector home
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


DEFAULT_HQ_APP_URL = "https://goldkey-ai-vje5ef5qka-du.a.run.app"
DEFAULT_CRM_APP_URL = "https://goldkey-crm-vje5ef5qka-du.a.run.app"


def _env(name: str, default: str) -> str:
    return (os.environ.get(name, "") or default).strip().rstrip("/")


def _get(url: str, timeout: float = 20.0) -> tuple[int, dict[str, str], str]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        headers = {k.lower(): v for k, v in dict(resp.headers).items()}
        return resp.getcode(), headers, body


def _post_json(
    url: str,
    payload: dict,
    headers: dict[str, str] | None = None,
    timeout: float = 20.0,
) -> tuple[int, dict]:
    b = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    h = {"Content-Type": "application/json; charset=utf-8"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=b, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return resp.getcode(), (json.loads(raw) if raw.strip() else {})


def _ok(name: str, detail: str) -> None:
    print(f"[PASS] {name}: {detail}")


def _fail(name: str, detail: str) -> None:
    print(f"[FAIL] {name}: {detail}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--person-id", default=os.environ.get("TEST_PERSON_ID", "").strip())
    ap.add_argument("--agent-id", default=os.environ.get("TEST_AGENT_ID", "").strip())
    ap.add_argument("--user-id", default=os.environ.get("TEST_USER_ID", "").strip())
    ap.add_argument("--sector", default=os.environ.get("TEST_SECTOR", "home").strip() or "home")
    args = ap.parse_args()

    hq_app_url = _env("HQ_APP_URL", DEFAULT_HQ_APP_URL)
    crm_app_url = _env("CRM_APP_URL", DEFAULT_CRM_APP_URL)
    hq_api_url = _env("HQ_API_URL", f"{hq_app_url}/api/v1")

    print("=== HQ/CRM Smoke Test ===")
    print(f"HQ_APP_URL:  {hq_app_url}")
    print(f"CRM_APP_URL: {crm_app_url}")
    print(f"HQ_API_URL:  {hq_api_url}")
    print("")

    failed = 0

    # 1) HQ 초기 화면 응답 확인
    try:
        code, headers, body = _get(hq_app_url)
        ctype = headers.get("content-type", "")
        if code == 200 and "text/html" in ctype and ("streamlit" in body.lower() or "goldkey" in body.lower()):
            _ok("HQ 초기 화면", f"status={code}, content-type={ctype}")
        else:
            failed += 1
            _fail("HQ 초기 화면", f"unexpected response: status={code}, content-type={ctype}")
    except Exception as e:
        failed += 1
        _fail("HQ 초기 화면", str(e))

    # 2) HQ API health
    try:
        code, _, body = _get(f"{hq_api_url}/health")
        parsed = json.loads(body) if body.strip().startswith("{") else {}
        if code == 200 and bool(parsed.get("ok")):
            _ok("HQ API health", f"status={code}, ok={parsed.get('ok')}")
        else:
            failed += 1
            _fail("HQ API health", f"status={code}, body={body[:180]}")
    except Exception as e:
        failed += 1
        _fail("HQ API health", str(e))

    # 3) CRM 초기 화면 응답 확인
    try:
        code, headers, body = _get(crm_app_url)
        ctype = headers.get("content-type", "")
        if code == 200 and "text/html" in ctype and ("streamlit" in body.lower() or "crm" in body.lower()):
            _ok("CRM 초기 화면", f"status={code}, content-type={ctype}")
        else:
            failed += 1
            _fail("CRM 초기 화면", f"unexpected response: status={code}, content-type={ctype}")
    except Exception as e:
        failed += 1
        _fail("CRM 초기 화면", str(e))

    # 4) 선택: CRM->HQ 브리지 트리거
    if args.person_id:
        try:
            secret = (os.environ.get("GK_ANALYSIS_BRIDGE_SECRET", "") or "").strip()
            extra_headers = {"X-GK-Bridge-Key": secret} if secret else {}
            payload = {
                "person_id": args.person_id,
                "agent_id": args.agent_id or "",
                "user_id": args.user_id or "",
                "sector": args.sector or "home",
            }
            code, parsed = _post_json(
                f"{hq_api_url}/analysis/trigger",
                payload=payload,
                headers=extra_headers,
            )
            if code == 200 and bool(parsed.get("ok")):
                _ok("CRM→HQ trigger", f"status={code}, deeplink={parsed.get('hq_deeplink', '')[:120]}")
            else:
                failed += 1
                _fail("CRM→HQ trigger", f"status={code}, body={parsed}")
        except urllib.error.HTTPError as e:
            failed += 1
            _fail("CRM→HQ trigger", f"HTTP {e.code} (secret/person_id 확인 필요)")
        except Exception as e:
            failed += 1
            _fail("CRM→HQ trigger", str(e))
    else:
        print("[SKIP] CRM→HQ trigger: --person-id 또는 TEST_PERSON_ID가 없어 건너뜀")

    print("")
    if failed:
        print(f"RESULT: FAILED ({failed} checks)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

