from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.request

import cv2
import numpy as np


def _token() -> str:
    import hmac

    uid = os.environ.get("HEAD_API_USER_ID", "ADMIN_MASTER")
    sec = os.environ.get("ENCRYPTION_KEY", "gk_token_secret_2026")
    ts = int(time.time())
    sig = hmac.new(sec.encode(), f"{uid}.{ts}".encode(), "sha256").hexdigest()[:32]
    return f"{uid}.{ts}.{sig}"


def _post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        method="POST",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {_token()}"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    p = subprocess.Popen(
        ["python", "-m", "uvicorn", "head_api.main:app", "--host", "127.0.0.1", "--port", "8813"],
        cwd=r"d:\CascadeProjects",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(2)
        img = np.full((900, 1300, 3), 240, dtype=np.uint8)
        cv2.rectangle(img, (120, 80), (1180, 820), (255, 255, 255), -1)
        cv2.putText(img, "POLICY SAMPLE", (220, 240), cv2.FONT_HERSHEY_SIMPLEX, 2.1, (20, 20, 20), 4, cv2.LINE_AA)
        cv2.putText(img, "insured amount", (220, 360), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (40, 40, 40), 2, cv2.LINE_AA)
        flare = np.zeros_like(img)
        cv2.circle(flare, (930, 260), 180, (255, 255, 255), -1)
        img = cv2.addWeighted(img, 1.0, flare, 0.24, 0)
        ok, enc = cv2.imencode(".jpg", img)
        if not ok:
            print("encode fail")
            return 1
        res = _post(
            "http://127.0.0.1:8813/api/v1/scan/preprocess",
            {
                "person_id": "scan_test_person",
                "image_b64": base64.b64encode(enc.tobytes()).decode(),
                "source": "camera",
                "filename": "sample.jpg",
            },
        )
        print(json.dumps({"ok": res.get("ok"), "status": res.get("status"), "quality_score": res.get("quality_score"), "meta": res.get("meta")}, ensure_ascii=False))
        return 0 if res.get("ok") else 1
    finally:
        p.terminate()
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()


if __name__ == "__main__":
    raise SystemExit(main())
